"""Implementação das consultas do painel sobre PostgreSQL.

Cada método carrega um arquivo .sql e mapeia a linha direto para o modelo de
leitura, sem passar pelo domínio (decisão D02).
"""

from __future__ import annotations

import psycopg
from psycopg.rows import class_row

from sdledger.application.consultas.painel import Janela, PercentisDeAtendimento
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
