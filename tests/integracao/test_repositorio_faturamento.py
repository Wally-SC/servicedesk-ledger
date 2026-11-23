"""Fechamento de ciclo de ponta a ponta contra PostgreSQL."""

from __future__ import annotations

from datetime import date

import psycopg
import pytest

from sdledger.application.casos_de_uso.fechar_ciclo import FecharCiclo
from sdledger.infrastructure.repositorios.faturamento import RepositorioDeFaturamentoEmPostgres

pytestmark = pytest.mark.integracao

MAIO = date(2026, 5, 1)


def _cenario(conexao: psycopg.Connection, cliente_id: int, plano_id: int) -> None:
    """Um contrato no mês e 750 minutos apontados — 150 além da franquia de 600."""
    conexao.execute(
        "INSERT INTO contrato (cliente_id, plano_id, vigencia) VALUES (%s, %s, %s)",
        (cliente_id, plano_id, "[2026-01-01,2027-01-01)"),
    )
    chamado = conexao.execute(
        """
        INSERT INTO chamado (cliente_id, prioridade, assunto, aberto_em)
        VALUES (%s, 'media', 'Rede lenta', '2026-05-04 10:00-03') RETURNING id
        """,
        (cliente_id,),
    ).fetchone()
    agente = conexao.execute("INSERT INTO agente (nome) VALUES ('Duda') RETURNING id").fetchone()
    assert chamado is not None and agente is not None
    for minutos, quando in ((500, "2026-05-04 12:00-03"), (250, "2026-05-31 23:30-03")):
        conexao.execute(
            """
            INSERT INTO apontamento (chamado_id, agente_id, minutos, apontado_em)
            VALUES (%s, %s, %s, %s)
            """,
            (chamado[0], agente[0], minutos, quando),
        )
    # fora da competência no fuso da análise: 1º de junho, 00h30 em São Paulo
    conexao.execute(
        """
        INSERT INTO apontamento (chamado_id, agente_id, minutos, apontado_em)
        VALUES (%s, %s, 999, '2026-06-01 00:30-03')
        """,
        (chamado[0], agente[0]),
    )


def test_fecha_ciclo_com_mensalidade_e_excedente(
    conexao: psycopg.Connection, cliente_id: int, plano_id: int
) -> None:
    _cenario(conexao, cliente_id, plano_id)

    FecharCiclo(RepositorioDeFaturamentoEmPostgres(conexao)).executar(MAIO)

    linha = conexao.execute(
        """
        SELECT f.estado, f.vencimento, f.total_centavos,
               array_agg(fi.tipo::text ORDER BY fi.tipo) AS tipos
        FROM ciclo_faturamento cf
        JOIN fatura f ON f.ciclo_id = cf.id
        JOIN fatura_item fi ON fi.fatura_id = f.id
        WHERE cf.cliente_id = %s AND cf.competencia = %s
        GROUP BY f.estado, f.vencimento, f.total_centavos
        """,
        (cliente_id, MAIO),
    ).fetchone()
    assert linha is not None
    estado, vencimento, total, tipos = linha
    assert estado == "emitida"
    assert vencimento == date(2026, 6, 10)
    # 49900 de mensalidade + 2,5 h a 120 reais
    assert total == 49900 + 30000
    assert tipos == ["mensalidade", "hora_excedente"]


def test_apontamento_da_madrugada_do_mes_seguinte_nao_entra(
    conexao: psycopg.Connection, cliente_id: int, plano_id: int
) -> None:
    """00h30 de 1º de junho em São Paulo é junho, ainda que seja 31 de maio em
    algum outro fuso. O consumo é medido no fuso da análise."""
    _cenario(conexao, cliente_id, plano_id)

    consumo = RepositorioDeFaturamentoEmPostgres(conexao).consumo_da_competencia(MAIO)

    assert consumo[cliente_id].minutos == 750
