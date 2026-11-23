"""Porta das consultas analíticas da cobrança."""

from __future__ import annotations

from datetime import date
from typing import Protocol

from sdledger.application.consultas.faturamento import (
    MesDeChurn,
    ReceitaDaCompetencia,
    ReceitaEmAtraso,
)


class ConsultasDeFaturamento(Protocol):
    def receita_por_competencia(self, inicio: date, fim: date) -> list[ReceitaDaCompetencia]: ...

    def receita_em_atraso(self, referencia: date) -> ReceitaEmAtraso: ...

    def churn_mensal(self, inicio: date, fim: date) -> list[MesDeChurn]: ...
