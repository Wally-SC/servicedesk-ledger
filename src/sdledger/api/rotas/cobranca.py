"""Rotas da cobrança recorrente."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from sdledger.api.dependencias import obter_consultas_de_faturamento, obter_relogio
from sdledger.application.consultas.faturamento import (
    JanelaDeCompetencias,
    MesDeChurn,
    ReceitaDaCompetencia,
    ReceitaEmAtraso,
)
from sdledger.application.portas.consultas_de_faturamento import ConsultasDeFaturamento
from sdledger.application.portas.relogio import Relogio

router = APIRouter(prefix="/api/cobranca", tags=["cobrança"])

MESES = Query(12, ge=1, le=36, description="Competências fechadas na série.")


@router.get("/receita", response_model=list[ReceitaDaCompetencia])
def receita(
    meses: int = MESES,
    consultas: ConsultasDeFaturamento = Depends(obter_consultas_de_faturamento),
    relogio: Relogio = Depends(obter_relogio),
) -> list[ReceitaDaCompetencia]:
    janela = JanelaDeCompetencias.ultimas(relogio.agora().date(), meses)
    return consultas.receita_por_competencia(janela.inicio, janela.fim)


@router.get("/atraso", response_model=ReceitaEmAtraso)
def atraso(
    consultas: ConsultasDeFaturamento = Depends(obter_consultas_de_faturamento),
    relogio: Relogio = Depends(obter_relogio),
) -> ReceitaEmAtraso:
    return consultas.receita_em_atraso(relogio.agora().date())


@router.get("/churn", response_model=list[MesDeChurn])
def churn(
    meses: int = MESES,
    consultas: ConsultasDeFaturamento = Depends(obter_consultas_de_faturamento),
    relogio: Relogio = Depends(obter_relogio),
) -> list[MesDeChurn]:
    janela = JanelaDeCompetencias.ultimas(relogio.agora().date(), meses)
    return consultas.churn_mensal(janela.inicio, janela.fim)
