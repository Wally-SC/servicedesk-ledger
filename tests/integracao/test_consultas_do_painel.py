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


def test_backlog_soma_as_faixas(painel: ConsultasDoPainelEmPostgres) -> None:
    """As quatro faixas de idade precisam somar o total da prioridade."""
    for linha in painel.backlog(AGORA):
        assert (
            linha.ate_1_dia + linha.de_1_a_3_dias + linha.de_3_a_7_dias + linha.mais_de_7_dias
            == linha.total
        )


def test_backlog_so_traz_chamado_em_aberto(
    painel: ConsultasDoPainelEmPostgres, conexao: psycopg.Connection
) -> None:
    total_consulta = sum(linha.total for linha in painel.backlog(AGORA))

    em_aberto = conexao.execute(
        "SELECT count(*) FROM chamado WHERE resolvido_em IS NULL"
    ).fetchone()
    assert em_aberto is not None and total_consulta == em_aberto[0]


def test_taxa_de_sla_fica_entre_zero_e_cem(painel: ConsultasDoPainelEmPostgres) -> None:
    linhas = painel.taxa_de_sla(JANELA)

    assert linhas
    for linha in linhas:
        assert 0 <= linha.taxa_percentual <= 100
        assert linha.dentro_do_prazo <= linha.entregues


def test_tendencia_tem_variacao_nula_na_primeira_semana(
    painel: ConsultasDoPainelEmPostgres,
) -> None:
    """LAG não tem linha anterior na primeira semana: precisa vir nulo, não zero."""
    semanas = painel.tendencia_semanal(JANELA)

    assert len(semanas) >= 2
    assert semanas[0].variacao_p95 is None
    assert semanas[0].variacao_resolvidos is None
    assert all(s.variacao_p95 is not None for s in semanas[1:])


def test_tendencia_acumula_os_resolvidos(painel: ConsultasDoPainelEmPostgres) -> None:
    semanas = painel.tendencia_semanal(JANELA)

    total = 0
    for semana in semanas:
        total += semana.resolvidos
        assert semana.resolvidos_acumulados == total


def test_ranking_vem_ordenado_e_limitado(painel: ConsultasDoPainelEmPostgres) -> None:
    linhas = painel.clientes_criticos(JANELA, AGORA, limite=5)

    assert 0 < len(linhas) <= 5
    assert [linha.posicao for linha in linhas] == list(range(1, len(linhas) + 1))
    escores = [linha.escore for linha in linhas]
    assert escores == sorted(escores, reverse=True)
    assert all(1 <= linha.quartil <= 4 for linha in linhas)
