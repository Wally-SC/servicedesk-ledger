"""Implementação das consultas da cobrança sobre PostgreSQL."""

from __future__ import annotations

from datetime import date

import psycopg
from psycopg.rows import class_row

from sdledger.application.consultas.faturamento import (
    MesDeChurn,
    ReceitaDaCompetencia,
    ReceitaEmAtraso,
)
from sdledger.infrastructure.db.sql import carregar


class ConsultasDeFaturamentoEmPostgres:
    def __init__(self, conexao: psycopg.Connection) -> None:
        self._conexao = conexao

    def receita_por_competencia(self, inicio: date, fim: date) -> list[ReceitaDaCompetencia]:
        with self._conexao.cursor(row_factory=class_row(ReceitaDaCompetencia)) as cursor:
            cursor.execute(
                carregar("faturamento/receita_por_competencia.sql"),
                {"inicio": inicio, "fim": fim},
            )
            return cursor.fetchall()

    def receita_em_atraso(self, referencia: date) -> ReceitaEmAtraso:
        with self._conexao.cursor(row_factory=class_row(ReceitaEmAtraso)) as cursor:
            cursor.execute(
                carregar("faturamento/receita_em_atraso.sql"), {"referencia": referencia}
            )
            linha = cursor.fetchone()
        if linha is None:  # pragma: no cover - agregação sem GROUP BY sempre devolve linha
            raise RuntimeError("a consulta de atraso não devolveu linha")
        return linha

    def churn_mensal(self, inicio: date, fim: date) -> list[MesDeChurn]:
        with self._conexao.cursor(row_factory=class_row(MesDeChurn)) as cursor:
            cursor.execute(carregar("faturamento/churn_mensal.sql"), {"inicio": inicio, "fim": fim})
            return cursor.fetchall()
