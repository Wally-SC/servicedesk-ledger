"""O banco amarra os estados da fatura e a unicidade do ciclo."""

from __future__ import annotations

import psycopg
import pytest

pytestmark = pytest.mark.integracao


def _ciclo(conexao: psycopg.Connection, cliente_id: int, competencia: str = "2026-05-01") -> int:
    linha = conexao.execute(
        "INSERT INTO ciclo_faturamento (cliente_id, competencia) VALUES (%s, %s) RETURNING id",
        (cliente_id, competencia),
    ).fetchone()
    assert linha is not None
    return int(linha[0])


def test_competencia_precisa_ser_o_primeiro_dia_do_mes(
    conexao: psycopg.Connection, cliente_id: int
) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        _ciclo(conexao, cliente_id, "2026-05-15")


def test_ciclo_duplicado_no_mesmo_mes_e_rejeitado(
    conexao: psycopg.Connection, cliente_id: int
) -> None:
    _ciclo(conexao, cliente_id)

    with pytest.raises(psycopg.errors.UniqueViolation):
        _ciclo(conexao, cliente_id)


def test_fatura_paga_sem_data_de_pagamento_e_rejeitada(
    conexao: psycopg.Connection, cliente_id: int
) -> None:
    ciclo_id = _ciclo(conexao, cliente_id)

    with pytest.raises(psycopg.errors.CheckViolation):
        conexao.execute(
            """
            INSERT INTO fatura (ciclo_id, estado, emitida_em, vencimento)
            VALUES (%s, 'paga', '2026-06-01 09:00-03', '2026-06-10')
            """,
            (ciclo_id,),
        )


def test_fatura_aberta_nao_pode_ter_emissao(conexao: psycopg.Connection, cliente_id: int) -> None:
    ciclo_id = _ciclo(conexao, cliente_id)

    with pytest.raises(psycopg.errors.CheckViolation):
        conexao.execute(
            """
            INSERT INTO fatura (ciclo_id, estado, emitida_em, vencimento)
            VALUES (%s, 'aberta', '2026-06-01 09:00-03', '2026-06-10')
            """,
            (ciclo_id,),
        )


def test_fatura_emitida_exige_vencimento(conexao: psycopg.Connection, cliente_id: int) -> None:
    ciclo_id = _ciclo(conexao, cliente_id)

    with pytest.raises(psycopg.errors.CheckViolation):
        conexao.execute(
            "INSERT INTO fatura (ciclo_id, estado, emitida_em) VALUES (%s, 'emitida', %s)",
            (ciclo_id, "2026-06-01 09:00-03"),
        )


def test_apontamento_com_minutos_nao_positivos_e_rejeitado(
    conexao: psycopg.Connection, cliente_id: int
) -> None:
    chamado = conexao.execute(
        """
        INSERT INTO chamado (cliente_id, prioridade, assunto, aberto_em)
        VALUES (%s, 'media', 'Lentidão', '2026-05-04 10:00-03') RETURNING id
        """,
        (cliente_id,),
    ).fetchone()
    agente = conexao.execute("INSERT INTO agente (nome) VALUES ('Bia') RETURNING id").fetchone()
    assert chamado is not None and agente is not None

    with pytest.raises(psycopg.errors.CheckViolation):
        conexao.execute(
            """
            INSERT INTO apontamento (chamado_id, agente_id, minutos, apontado_em)
            VALUES (%s, %s, 0, '2026-05-04 11:00-03')
            """,
            (chamado[0], agente[0]),
        )
