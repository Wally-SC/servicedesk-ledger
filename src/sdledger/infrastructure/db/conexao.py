"""Acesso ao PostgreSQL."""

from __future__ import annotations

import psycopg


def banco_responde(dsn: str, segundos: int = 2) -> bool:
    """Diz se o banco aceita conexão e responde a uma consulta trivial."""
    try:
        with (
            psycopg.connect(dsn, connect_timeout=segundos) as conexao,
            conexao.cursor() as cursor,
        ):
            cursor.execute("SELECT 1")
            return cursor.fetchone() == (1,)
    except psycopg.Error:
        return False
