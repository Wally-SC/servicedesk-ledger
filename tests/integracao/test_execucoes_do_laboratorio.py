"""Registro e processamento de uma medição, contra PostgreSQL real."""

from __future__ import annotations

from datetime import date

import psycopg
import pytest

from sdledger.infrastructure.laboratorio.execucoes import (
    TRAVA_DO_LABORATORIO,
    RepositorioDeExecucoesEmPostgres,
    processar,
)
from sdledger.infrastructure.massa.gerador import gerar
from sdledger.infrastructure.massa.perfis import PEQUENO

pytestmark = pytest.mark.integracao


@pytest.fixture
def repositorio(conexao: psycopg.Connection) -> RepositorioDeExecucoesEmPostgres:
    gerar(conexao, PEQUENO, semente=42, fim=date(2026, 11, 23))
    return RepositorioDeExecucoesEmPostgres(conexao)


def test_processa_e_registra_os_dois_planos(
    conexao: psycopg.Connection, repositorio: RepositorioDeExecucoesEmPostgres
) -> None:
    pedido = repositorio.solicitar("historico_do_cliente", 1)

    processar(conexao, pedido.id)

    execucao = repositorio.obter(pedido.id)
    assert execucao is not None
    assert execucao.estado == "concluida"
    assert execucao.sem_indice_ms is not None and execucao.com_indice_ms is not None
    assert execucao.plano_sem_indice and execucao.plano_com_indice
    assert repositorio.em_andamento() is None


def test_falha_quando_outra_sessao_segura_a_trava(
    conexao: psycopg.Connection, repositorio: RepositorioDeExecucoesEmPostgres, dsn: str
) -> None:
    """Dois pedidos no mesmo instante passam pelo caso de uso; a trava segura."""
    pedido = repositorio.solicitar("historico_do_cliente", 1)
    with psycopg.connect(dsn, autocommit=True) as outra:
        outra.execute("SELECT pg_advisory_lock(%s)", (TRAVA_DO_LABORATORIO,))
        processar(conexao, pedido.id)
        outra.execute("SELECT pg_advisory_unlock(%s)", (TRAVA_DO_LABORATORIO,))

    execucao = repositorio.obter(pedido.id)
    assert execucao is not None
    assert execucao.estado == "falhou"
    assert execucao.erro is not None and "outra medição" in execucao.erro
