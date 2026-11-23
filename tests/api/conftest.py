"""Dublês para as rotas: a API é testada sem banco.

O que se testa aqui é a tradução de HTTP — parâmetro, validação, formato da
resposta. As consultas têm seus próprios testes contra PostgreSQL real.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from sdledger.api import dependencias
from sdledger.api.main import app
from sdledger.application.consultas.faturamento import (
    MesDeChurn,
    ReceitaDaCompetencia,
    ReceitaEmAtraso,
)
from sdledger.application.consultas.painel import (
    ClienteCritico,
    Janela,
    LinhaDeBacklog,
    PercentisDeAtendimento,
    SemanaDaTendencia,
    TaxaDeSla,
)

FUSO = timezone(timedelta(hours=-3))
AGORA = datetime(2026, 11, 23, 12, 0, tzinfo=FUSO)


class RelogioFixo:
    def agora(self) -> datetime:
        return AGORA


class PainelFalso:
    """Guarda as janelas recebidas para o teste conferir o que a rota montou."""

    def __init__(self) -> None:
        self.janelas: list[Janela] = []

    def percentis(self, janela: Janela) -> PercentisDeAtendimento:
        self.janelas.append(janela)
        return PercentisDeAtendimento(100, 3, 20.0, 160.0, 260.0, 210.0, 1140.0, 2100.0)

    def backlog(self, agora: datetime) -> list[LinhaDeBacklog]:
        return [LinhaDeBacklog("critica", 10, 1, 2, 3, 4, 12.5)]

    def taxa_de_sla(self, janela: Janela) -> list[TaxaDeSla]:
        self.janelas.append(janela)
        return [TaxaDeSla("alta", 50, 45, 90.0)]

    def tendencia_semanal(self, janela: Janela) -> list[SemanaDaTendencia]:
        self.janelas.append(janela)
        return [
            SemanaDaTendencia(date(2026, 11, 9), 30, 2000.0, None, None, 30),
            SemanaDaTendencia(date(2026, 11, 16), 35, 1900.0, -100.0, 5, 65),
        ]

    def clientes_criticos(
        self, janela: Janela, agora: datetime, limite: int = 10
    ) -> list[ClienteCritico]:
        self.janelas.append(janela)
        return [ClienteCritico(1, 1, 7, "Cliente 0007", 90, 12, 30, 5.5, 71.5)][:limite]


class CobrancaFalsa:
    def __init__(self) -> None:
        self.intervalos: list[tuple[date, date]] = []

    def receita_por_competencia(self, inicio: date, fim: date) -> list[ReceitaDaCompetencia]:
        self.intervalos.append((inicio, fim))
        return [ReceitaDaCompetencia(date(2026, 10, 1), 3, 150000, 50000, 200000, None)]

    def receita_em_atraso(self, referencia: date) -> ReceitaEmAtraso:
        return ReceitaEmAtraso(2, 2, 90000, 10000, 30000, 50000)

    def churn_mensal(self, inicio: date, fim: date) -> list[MesDeChurn]:
        self.intervalos.append((inicio, fim))
        return [MesDeChurn(date(2026, 10, 1), 100, 2, 2.0)]


@pytest.fixture
def cobranca_falsa() -> CobrancaFalsa:
    return CobrancaFalsa()


@pytest.fixture
def agora() -> datetime:
    return AGORA


@pytest.fixture
def painel_falso() -> PainelFalso:
    return PainelFalso()


@pytest.fixture
def cliente(painel_falso: PainelFalso) -> Iterator[TestClient]:
    app.dependency_overrides[dependencias.obter_consultas_do_painel] = lambda: painel_falso
    app.dependency_overrides[dependencias.obter_relogio] = RelogioFixo
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def cliente_cobranca(cobranca_falsa: CobrancaFalsa) -> Iterator[TestClient]:
    app.dependency_overrides[dependencias.obter_consultas_de_faturamento] = lambda: cobranca_falsa
    app.dependency_overrides[dependencias.obter_relogio] = RelogioFixo
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
