"""Rotas do laboratório de índices.

A tela nunca envia SQL: escolhe um experimento do catálogo pelo nome. Criar e
remover índice exige token e pode ser desligado por variável de ambiente
(decisão D15).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, status
from pydantic import BaseModel, Field

from sdledger.api.dependencias import (
    exigir_token_do_laboratorio,
    obter_dsn_do_laboratorio,
    obter_executor_de_medicao,
    obter_repositorio_de_execucoes,
)
from sdledger.application.casos_de_uso.solicitar_medicao import SolicitarMedicao
from sdledger.application.portas.laboratorio import ExecucaoDoLaboratorio, RepositorioDeExecucoes
from sdledger.domain.comum.erros import NaoEncontrado
from sdledger.infrastructure.db.sql import carregar
from sdledger.infrastructure.laboratorio.catalogo import EXPERIMENTOS, POR_NOME
from sdledger.infrastructure.laboratorio.plano import resumir

router = APIRouter(prefix="/api/laboratorio", tags=["laboratório"])


class PedidoDeMedicao(BaseModel):
    experimento: str
    repeticoes: int = Field(5, ge=1, le=15)


def _serializar(execucao: ExecucaoDoLaboratorio | None) -> dict[str, Any] | None:
    if execucao is None:
        return None
    dados = asdict(execucao)
    for lado in ("plano_sem_indice", "plano_com_indice"):
        plano = dados.pop(lado)
        dados[lado] = [asdict(no) for no in resumir(plano)] if plano else None
    return dados


@router.get("/experimentos")
def experimentos(
    repositorio: RepositorioDeExecucoes = Depends(obter_repositorio_de_execucoes),
) -> list[dict[str, Any]]:
    ultimas = repositorio.ultimas_por_experimento()
    return [
        {
            "nome": experimento.nome,
            "titulo": experimento.titulo,
            "tabela": experimento.tabela,
            "indice": experimento.indice,
            "consulta": carregar(experimento.consulta_sql),
            "ddl": carregar(experimento.indice_sql),
            "ultima": _serializar(ultimas.get(experimento.nome)),
        }
        for experimento in EXPERIMENTOS
    ]


@router.post(
    "/medicoes",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(exigir_token_do_laboratorio)],
)
def solicitar_medicao(
    pedido: PedidoDeMedicao,
    tarefas: BackgroundTasks,
    repositorio: RepositorioDeExecucoes = Depends(obter_repositorio_de_execucoes),
    dsn: str = Depends(obter_dsn_do_laboratorio),
    executor: Callable[[str, int], None] = Depends(obter_executor_de_medicao),
) -> dict[str, Any] | None:
    execucao = SolicitarMedicao(repositorio, frozenset(POR_NOME)).executar(
        pedido.experimento, pedido.repeticoes
    )
    tarefas.add_task(executor, dsn, execucao.id)
    return _serializar(execucao)


@router.get("/medicoes/{execucao_id}")
def medicao(
    execucao_id: int,
    repositorio: RepositorioDeExecucoes = Depends(obter_repositorio_de_execucoes),
) -> dict[str, Any] | None:
    execucao = repositorio.obter(execucao_id)
    if execucao is None:
        raise NaoEncontrado(f"medição #{execucao_id} não existe")
    return _serializar(execucao)
