"""O histórico de faturas da massa sai do caso de uso de fechamento."""

from __future__ import annotations

from datetime import date

import psycopg
import pytest

from sdledger.infrastructure.massa.faturas import faturar_historico
from sdledger.infrastructure.massa.gerador import gerar
from sdledger.infrastructure.massa.perfis import PEQUENO

pytestmark = pytest.mark.integracao

FIM = date(2026, 11, 23)


@pytest.fixture
def massa(conexao: psycopg.Connection) -> psycopg.Connection:
    gerar(conexao, PEQUENO, semente=42, fim=FIM)
    faturar_historico(conexao, semente=42, fim=FIM)
    return conexao


def _um(conexao: psycopg.Connection, sql: str, *parametros: object) -> object:
    linha = conexao.execute(sql, parametros).fetchone()
    assert linha is not None
    return linha[0]


def test_um_ciclo_por_cliente_com_contrato_em_cada_competencia(massa: psycopg.Connection) -> None:
    sem_ciclo = _um(
        massa,
        """
        SELECT count(*)
        FROM generate_series(
            (SELECT date_trunc('month', min(lower(vigencia)))::date FROM contrato),
            date_trunc('month', %s::date)::date - 1,
            interval '1 month'
        ) AS m(mes)
        JOIN contrato ct
          ON ct.vigencia && daterange(m.mes::date, (m.mes + interval '1 month')::date)
        WHERE NOT EXISTS (
            SELECT 1 FROM ciclo_faturamento cf
            WHERE cf.cliente_id = ct.cliente_id AND cf.competencia = m.mes::date
        )
        """,
        FIM,
    )
    assert sem_ciclo == 0


def test_nenhum_pagamento_no_futuro(massa: psycopg.Connection) -> None:
    assert _um(massa, "SELECT count(*) FROM fatura WHERE paga_em >= %s", FIM) == 0


def test_existe_fatura_em_atraso(massa: psycopg.Connection) -> None:
    em_atraso = _um(
        massa, "SELECT count(*) FROM fatura WHERE estado = 'emitida' AND vencimento < %s", FIM
    )
    assert isinstance(em_atraso, int) and em_atraso > 0


def test_existe_cliente_que_saiu(massa: psycopg.Connection) -> None:
    """Sem cliente saindo, o churn do painel de cobrança seria sempre zero."""
    saiu = _um(
        massa,
        """
        SELECT count(*) FROM (
            SELECT cliente_id FROM contrato GROUP BY cliente_id
            HAVING max(upper(vigencia)) <= %s
        ) AS s
        """,
        FIM,
    )
    assert isinstance(saiu, int) and saiu >= 1


def test_cliente_que_saiu_nao_abre_chamado_depois(massa: psycopg.Connection) -> None:
    depois = _um(
        massa,
        """
        SELECT count(*)
        FROM chamado c
        JOIN (
            SELECT cliente_id, max(upper(vigencia)) AS saida
            FROM contrato GROUP BY cliente_id HAVING max(upper(vigencia)) <= %s
        ) AS s ON s.cliente_id = c.cliente_id
        WHERE c.aberto_em::date >= s.saida
        """,
        FIM,
    )
    assert depois == 0


def test_rodar_o_faturamento_de_novo_nao_duplica(massa: psycopg.Connection) -> None:
    antes = _um(massa, "SELECT count(*) FROM fatura")

    faturar_historico(massa, semente=42, fim=FIM)

    assert _um(massa, "SELECT count(*) FROM fatura") == antes
