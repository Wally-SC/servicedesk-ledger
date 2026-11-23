"""Rotas do painel de SLA e backlog.

Finas de propósito: montam a janela, chamam a porta de consulta e devolvem o
modelo de leitura. Nenhuma regra de negócio, nenhum SQL.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from sdledger.api.dependencias import obter_consultas_do_painel, obter_relogio
from sdledger.application.consultas.painel import (
    ClienteCritico,
    Janela,
    LinhaDeBacklog,
    PercentisDeAtendimento,
    SemanaDaTendencia,
    TaxaDeSla,
)
from sdledger.application.portas.consultas import ConsultasDoPainel
from sdledger.application.portas.relogio import Relogio

router = APIRouter(prefix="/api/painel", tags=["painel"])

DIAS = Query(30, ge=1, le=365, description="Tamanho da janela, em dias.")


@router.get("/percentis", response_model=PercentisDeAtendimento)
def percentis(
    dias: int = DIAS,
    consultas: ConsultasDoPainel = Depends(obter_consultas_do_painel),
    relogio: Relogio = Depends(obter_relogio),
) -> PercentisDeAtendimento:
    return consultas.percentis(Janela.ultimos_dias(relogio.agora(), dias))


@router.get("/backlog", response_model=list[LinhaDeBacklog])
def backlog(
    consultas: ConsultasDoPainel = Depends(obter_consultas_do_painel),
    relogio: Relogio = Depends(obter_relogio),
) -> list[LinhaDeBacklog]:
    return consultas.backlog(relogio.agora())


@router.get("/sla", response_model=list[TaxaDeSla])
def taxa_de_sla(
    dias: int = DIAS,
    consultas: ConsultasDoPainel = Depends(obter_consultas_do_painel),
    relogio: Relogio = Depends(obter_relogio),
) -> list[TaxaDeSla]:
    return consultas.taxa_de_sla(Janela.ultimos_dias(relogio.agora(), dias))


@router.get("/tendencia", response_model=list[SemanaDaTendencia])
def tendencia(
    semanas: int = Query(12, ge=2, le=52, description="Semanas completas na série."),
    consultas: ConsultasDoPainel = Depends(obter_consultas_do_painel),
    relogio: Relogio = Depends(obter_relogio),
) -> list[SemanaDaTendencia]:
    return consultas.tendencia_semanal(Janela.semanas_completas(relogio.agora(), semanas))


@router.get("/clientes", response_model=list[ClienteCritico])
def clientes_criticos(
    dias: int = DIAS,
    limite: int = Query(10, ge=1, le=50),
    consultas: ConsultasDoPainel = Depends(obter_consultas_do_painel),
    relogio: Relogio = Depends(obter_relogio),
) -> list[ClienteCritico]:
    agora = relogio.agora()
    return consultas.clientes_criticos(Janela.ultimos_dias(agora, dias), agora, limite)
