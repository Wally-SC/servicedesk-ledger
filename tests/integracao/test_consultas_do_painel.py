"""As consultas do painel, contra massa fictícia gerada na própria transação.

Os testes não fixam números: eles fixam invariantes. Número de painel muda com a
semente e com a janela; invariante quebrada é bug de consulta.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import psycopg
import pytest

from sdledger.application.consultas.painel import Janela
from sdledger.infrastructure.consultas.painel import ConsultasDoPainelEmPostgres
from sdledger.infrastructure.massa.gerador import gerar
from sdledger.infrastructure.massa.perfis import PEQUENO

pytestmark = pytest.mark.integracao

FUSO = timezone(timedelta(hours=-3))
FIM_DA_MASSA = date(2026, 11, 23)
AGORA = datetime(2026, 11, 23, 12, 0, tzinfo=FUSO)
JANELA = Janela(inicio=AGORA - timedelta(days=30), fim=AGORA)


@pytest.fixture
def painel(conexao: psycopg.Connection) -> ConsultasDoPainelEmPostgres:
    gerar(conexao, PEQUENO, semente=42, fim=FIM_DA_MASSA)
    return ConsultasDoPainelEmPostgres(conexao)


def test_percentis_sao_monotonicos(painel: ConsultasDoPainelEmPostgres) -> None:
    """p50 <= p90 <= p95 é definição de percentil: se quebrar, a consulta errou."""
    resultado = painel.percentis(JANELA)

    assert resultado.resolvidos > 0
    for p50, p90, p95 in (
        (resultado.resposta_p50, resultado.resposta_p90, resultado.resposta_p95),
        (resultado.resolucao_p50, resultado.resolucao_p90, resultado.resolucao_p95),
    ):
        assert p50 is not None and p90 is not None and p95 is not None
        assert p50 <= p90 <= p95


def test_chamado_sem_resposta_fica_fora_do_percentil_e_e_contado(
    painel: ConsultasDoPainelEmPostgres, conexao: psycopg.Connection
) -> None:
    """O pior caso não some dentro do p95: ele é contado à parte."""
    resultado = painel.percentis(JANELA)

    com_resposta = conexao.execute(
        """
        SELECT count(*) FROM chamado
        WHERE resolvido_em >= %s AND resolvido_em < %s AND primeira_resposta_em IS NOT NULL
        """,
        (JANELA.inicio, JANELA.fim),
    ).fetchone()
    assert com_resposta is not None
    assert resultado.resolvidos - resultado.sem_primeira_resposta == com_resposta[0]
