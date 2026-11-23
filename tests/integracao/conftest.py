"""Fixtures dos testes que exigem um PostgreSQL de verdade.

As migrações são aplicadas uma vez por sessão; cada teste roda dentro de uma
transação que é desfeita no fim, então a ordem dos testes não importa e o banco
não acumula lixo.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from alembic import command
from alembic.config import Config as ConfigAlembic

from sdledger.infrastructure.config import Config

RAIZ = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def dsn() -> str:
    return Config(_env_file=None).dsn


@pytest.fixture(scope="session", autouse=True)
def _migracoes_aplicadas() -> None:
    config = ConfigAlembic(str(RAIZ / "alembic.ini"))
    config.set_main_option(
        "script_location", str(RAIZ / "src" / "sdledger" / "infrastructure" / "migracoes")
    )
    command.upgrade(config, "head")


@pytest.fixture
def conexao(dsn: str) -> Iterator[psycopg.Connection]:
    conexao = psycopg.connect(dsn)
    try:
        yield conexao
    finally:
        conexao.rollback()
        conexao.close()


@pytest.fixture
def cliente_id(conexao: psycopg.Connection) -> int:
    """Cliente novo a cada teste.

    Os valores únicos são sorteados de propósito: o banco de desenvolvimento tem
    a massa fictícia carregada, e fixture com documento fixo passaria só em banco
    vazio — ou seja, passaria na esteira e quebraria na máquina.
    """
    linha = conexao.execute(
        "INSERT INTO cliente (nome, documento) VALUES (%s, %s) RETURNING id",
        (f"Cliente {uuid4().hex[:8]}", uuid4().hex[:14]),
    ).fetchone()
    assert linha is not None
    return int(linha[0])


@pytest.fixture
def plano_id(conexao: psycopg.Connection) -> int:
    linha = conexao.execute(
        """
        INSERT INTO plano (nome, franquia_minutos, mensalidade_centavos,
                           preco_hora_excedente_centavos)
        VALUES (%s, 600, 49900, 12000)
        RETURNING id
        """,
        (f"Plano {uuid4().hex[:8]}",),
    ).fetchone()
    assert linha is not None
    return int(linha[0])
