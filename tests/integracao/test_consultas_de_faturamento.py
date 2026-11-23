"""Consultas da cobrança contra a massa pequena com faturas."""

from __future__ import annotations

from datetime import date

import psycopg
import pytest

from sdledger.infrastructure.consultas.faturamento import ConsultasDeFaturamentoEmPostgres
from sdledger.infrastructure.massa.faturas import faturar_historico
from sdledger.infrastructure.massa.gerador import gerar, limpar
from sdledger.infrastructure.massa.perfis import PEQUENO

pytestmark = pytest.mark.integracao

FIM = date(2026, 11, 23)
INICIO = date(2026, 6, 1)


@pytest.fixture
def cobranca(conexao: psycopg.Connection) -> ConsultasDeFaturamentoEmPostgres:
    gerar(conexao, PEQUENO, semente=42, fim=FIM)
    faturar_historico(conexao, semente=42, fim=FIM)
    return ConsultasDeFaturamentoEmPostgres(conexao)


def test_receita_e_mensalidade_mais_excedente(cobranca: ConsultasDeFaturamentoEmPostgres) -> None:
    competencias = cobranca.receita_por_competencia(INICIO, FIM.replace(day=1))

    assert competencias
    for linha in competencias:
        assert linha.receita_centavos == linha.mensalidades_centavos + linha.excedente_centavos


def test_primeira_competencia_nao_tem_variacao(cobranca: ConsultasDeFaturamentoEmPostgres) -> None:
    competencias = cobranca.receita_por_competencia(INICIO, FIM.replace(day=1))

    assert competencias[0].variacao_percentual is None
    assert all(linha.variacao_percentual is not None for linha in competencias[1:])


def test_faixas_de_atraso_somam_o_total(cobranca: ConsultasDeFaturamentoEmPostgres) -> None:
    atraso = cobranca.receita_em_atraso(FIM)

    assert atraso.faturas > 0
    assert (
        atraso.ate_30_dias_centavos
        + atraso.de_31_a_90_dias_centavos
        + atraso.mais_de_90_dias_centavos
        == atraso.total_centavos
    )


def test_fatura_que_vence_hoje_ainda_nao_esta_atrasada(
    cobranca: ConsultasDeFaturamentoEmPostgres, conexao: psycopg.Connection
) -> None:
    antes = cobranca.receita_em_atraso(FIM)
    conexao.execute(
        """
        UPDATE fatura SET estado = 'emitida', paga_em = NULL, vencimento = %s
        WHERE id = (SELECT min(id) FROM fatura WHERE estado = 'paga')
        """,
        (FIM,),
    )

    depois = cobranca.receita_em_atraso(FIM)

    assert depois.faturas == antes.faturas


def test_churn_conta_quem_saiu(cobranca: ConsultasDeFaturamentoEmPostgres) -> None:
    meses = cobranca.churn_mensal(date(2025, 7, 1), FIM)

    assert sum(m.perdidos for m in meses) >= 1
    for mes in meses:
        assert mes.perdidos <= mes.ativos_no_mes_anterior
        assert mes.churn_percentual is None or 0 <= mes.churn_percentual <= 100


def test_troca_de_plano_nao_e_churn(conexao: psycopg.Connection) -> None:
    """Cenário controlado: em março um cliente troca de plano e outro sai.

    Dos dois ativos em fevereiro, só um foi perdido: churn de 50%. Se a troca de
    plano contasse como saída, daria 100%.
    """
    limpar(conexao)
    conexao.execute(
        """
        INSERT INTO plano (nome, franquia_minutos, mensalidade_centavos,
                           preco_hora_excedente_centavos)
        VALUES ('Básico', 600, 10000, 10000), ('Maior', 1200, 20000, 10000)
        """
    )
    conexao.execute("INSERT INTO cliente (nome, documento) VALUES ('Troca', '1'), ('Sai', '2')")
    conexao.execute(
        """
        INSERT INTO contrato (cliente_id, plano_id, vigencia) VALUES
            (1, 1, '[2026-01-01,2026-03-01)'),
            (1, 2, '[2026-03-01,2027-01-01)'),
            (2, 1, '[2026-01-01,2026-03-01)')
        """
    )

    meses = ConsultasDeFaturamentoEmPostgres(conexao).churn_mensal(
        date(2026, 3, 1), date(2026, 5, 1)
    )
    marco = next(m for m in meses if m.mes == date(2026, 3, 1))

    assert marco.ativos_no_mes_anterior == 2
    assert marco.perdidos == 1
    assert marco.churn_percentual == 50.0
