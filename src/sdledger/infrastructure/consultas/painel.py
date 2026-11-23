"""Implementação das consultas do painel sobre PostgreSQL.

Cada método carrega um arquivo .sql e mapeia a linha direto para o modelo de
leitura, sem passar pelo domínio (decisão D02).
"""

from __future__ import annotations

from datetime import datetime

import psycopg
from psycopg.rows import class_row

from sdledger.application.consultas.painel import (
    ClienteCritico,
    Janela,
    LinhaDeBacklog,
    PercentisDeAtendimento,
    SemanaDaTendencia,
    TaxaDeSla,
)
from sdledger.infrastructure.db.sql import carregar


class ConsultasDoPainelEmPostgres:
    """Consultas do painel contra uma conexão já aberta."""

    def __init__(self, conexao: psycopg.Connection) -> None:
        self._conexao = conexao

    def percentis(self, janela: Janela) -> PercentisDeAtendimento:
        with self._conexao.cursor(row_factory=class_row(PercentisDeAtendimento)) as cursor:
            cursor.execute(
                carregar("painel/percentis_de_atendimento.sql"),
                {"inicio": janela.inicio, "fim": janela.fim},
            )
            linha = cursor.fetchone()
        if linha is None:  # pragma: no cover - a consulta sempre devolve uma linha
            raise RuntimeError("a consulta de percentis não devolveu linha")
        return linha

    def backlog(self, agora: datetime) -> list[LinhaDeBacklog]:
        with self._conexao.cursor(row_factory=class_row(LinhaDeBacklog)) as cursor:
            cursor.execute(carregar("painel/backlog_por_idade.sql"), {"agora": agora})
            return cursor.fetchall()

    def taxa_de_sla(self, janela: Janela) -> list[TaxaDeSla]:
        with self._conexao.cursor(row_factory=class_row(TaxaDeSla)) as cursor:
            cursor.execute(
                carregar("painel/taxa_de_sla.sql"),
                {"inicio": janela.inicio, "fim": janela.fim},
            )
            return cursor.fetchall()

    def tendencia_semanal(self, janela: Janela) -> list[SemanaDaTendencia]:
        with self._conexao.cursor(row_factory=class_row(SemanaDaTendencia)) as cursor:
            cursor.execute(
                carregar("painel/tendencia_semanal.sql"),
                {"inicio": janela.inicio, "fim": janela.fim},
            )
            return cursor.fetchall()

    def clientes_criticos(
        self, janela: Janela, agora: datetime, limite: int = 10
    ) -> list[ClienteCritico]:
        with self._conexao.cursor(row_factory=class_row(ClienteCritico)) as cursor:
            cursor.execute(
                carregar("painel/ranking_de_clientes.sql"),
                {
                    "inicio": janela.inicio,
                    "fim": janela.fim,
                    "agora": agora,
                    "limite": limite,
                },
            )
            return cursor.fetchall()
