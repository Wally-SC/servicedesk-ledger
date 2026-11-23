"""Dependências das rotas.

É aqui, e só aqui, que a API escolhe a implementação concreta de cada porta. Os
testes trocam estas funções por dublês sem tocar nas rotas.
"""

from __future__ import annotations

import secrets
from collections.abc import Callable, Iterator

import psycopg
from fastapi import Depends, Header, HTTPException, Request, status
from psycopg_pool import ConnectionPool

from sdledger.application.portas.consultas import ConsultasDoPainel
from sdledger.application.portas.consultas_de_faturamento import ConsultasDeFaturamento
from sdledger.application.portas.laboratorio import RepositorioDeExecucoes
from sdledger.application.portas.relogio import Relogio
from sdledger.infrastructure.config import obter_config
from sdledger.infrastructure.consultas.faturamento import ConsultasDeFaturamentoEmPostgres
from sdledger.infrastructure.consultas.painel import ConsultasDoPainelEmPostgres
from sdledger.infrastructure.laboratorio.execucoes import (
    RepositorioDeExecucoesEmPostgres,
    executar_em_segundo_plano,
)
from sdledger.infrastructure.relogio import RelogioDoSistema


def obter_pool(request: Request) -> ConnectionPool:
    pool: ConnectionPool = request.app.state.pool
    return pool


def obter_conexao(pool: ConnectionPool = Depends(obter_pool)) -> Iterator[psycopg.Connection]:
    with pool.connection() as conexao:
        yield conexao


def obter_consultas_do_painel(
    conexao: psycopg.Connection = Depends(obter_conexao),
) -> ConsultasDoPainel:
    return ConsultasDoPainelEmPostgres(conexao)


def obter_consultas_de_faturamento(
    conexao: psycopg.Connection = Depends(obter_conexao),
) -> ConsultasDeFaturamento:
    return ConsultasDeFaturamentoEmPostgres(conexao)


def obter_relogio() -> Relogio:
    return RelogioDoSistema()


def obter_dsn_do_laboratorio() -> str:
    return obter_config().dsn_laboratorio


def obter_conexao_do_laboratorio(
    dsn: str = Depends(obter_dsn_do_laboratorio),
) -> Iterator[psycopg.Connection]:
    """Conexão com o banco do laboratório, separado do banco da aplicação."""
    try:
        conexao = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    except psycopg.OperationalError as erro:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "banco do laboratório indisponível"
        ) from erro
    with conexao:
        yield conexao


def obter_repositorio_de_execucoes(
    conexao: psycopg.Connection = Depends(obter_conexao_do_laboratorio),
) -> RepositorioDeExecucoes:
    return RepositorioDeExecucoesEmPostgres(conexao)


def obter_executor_de_medicao() -> Callable[[str, int], None]:
    return executar_em_segundo_plano


def exigir_token_do_laboratorio(x_lab_token: str | None = Header(default=None)) -> None:
    """Criar e remover índice exige token, e pode ser desligado por completo.

    Desligado responde 403 mesmo com token certo: num deploy público, ninguém
    deve conseguir rodar DDL, nem quem descobrir o token.
    """
    config = obter_config()
    if not config.lab_habilitado:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "laboratório desligado neste ambiente")
    if x_lab_token is None or not secrets.compare_digest(x_lab_token, config.lab_token):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "token do laboratório inválido")
