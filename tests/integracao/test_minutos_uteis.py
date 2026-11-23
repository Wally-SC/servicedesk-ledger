"""O relógio de SLA conta expediente, não tempo corrido.

2026-11-23 é segunda-feira e 2026-11-27 é sexta. O expediente é de segunda a
sexta, das 9h às 18h — 540 minutos por dia.
"""

from __future__ import annotations

import psycopg
import pytest

pytestmark = pytest.mark.integracao


def _minutos(conexao: psycopg.Connection, inicio: str, fim: str) -> int:
    linha = conexao.execute("SELECT minutos_uteis(%s, %s)", (inicio, fim)).fetchone()
    assert linha is not None
    return int(linha[0])


@pytest.mark.parametrize(
    ("inicio", "fim", "esperado", "caso"),
    [
        ("2026-11-23 10:00-03", "2026-11-23 11:30-03", 90, "dentro do expediente"),
        ("2026-11-23 07:00-03", "2026-11-23 10:00-03", 60, "começa antes de abrir"),
        ("2026-11-23 17:00-03", "2026-11-23 20:00-03", 60, "termina depois de fechar"),
        ("2026-11-23 09:00-03", "2026-11-23 18:00-03", 540, "dia inteiro"),
        ("2026-11-27 17:00-03", "2026-11-30 10:00-03", 120, "atravessa o fim de semana"),
        ("2026-11-28 08:00-03", "2026-11-29 23:00-03", 0, "só fim de semana"),
        ("2026-11-23 09:00-03", "2026-11-27 18:00-03", 2700, "semana inteira"),
        ("2026-11-23 12:00-03", "2026-11-23 10:00-03", 0, "intervalo invertido"),
        ("2026-11-23 10:00-03", "2026-11-23 10:00-03", 0, "intervalo vazio"),
    ],
)
def test_minutos_uteis(
    conexao: psycopg.Connection, inicio: str, fim: str, esperado: int, caso: str
) -> None:
    assert _minutos(conexao, inicio, fim) == esperado, caso


def test_feriado_nao_conta(conexao: psycopg.Connection) -> None:
    """Terça vira feriado: três dias úteis passam a valer dois."""
    assert _minutos(conexao, "2026-11-23 09:00-03", "2026-11-25 18:00-03") == 1620

    conexao.execute(
        "INSERT INTO feriado (dia, descricao) VALUES ('2026-11-24', 'Feriado de teste')"
    )

    assert _minutos(conexao, "2026-11-23 09:00-03", "2026-11-25 18:00-03") == 1080


def test_politicas_de_sla_sobrepostas_sao_rejeitadas(
    conexao: psycopg.Connection, plano_id: int
) -> None:
    conexao.execute(
        """
        INSERT INTO politica_sla (plano_id, prioridade, minutos_uteis_primeira_resposta,
                                  minutos_uteis_resolucao, vigencia)
        VALUES (%s, 'alta', 60, 480, '[2026-01-01,2026-07-01)')
        """,
        (plano_id,),
    )

    with pytest.raises(psycopg.errors.ExclusionViolation):
        conexao.execute(
            """
            INSERT INTO politica_sla (plano_id, prioridade, minutos_uteis_primeira_resposta,
                                      minutos_uteis_resolucao, vigencia)
            VALUES (%s, 'alta', 30, 240, '[2026-06-01,2027-01-01)')
            """,
            (plano_id,),
        )


def test_resolucao_menor_que_primeira_resposta_e_rejeitada(
    conexao: psycopg.Connection, plano_id: int
) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        conexao.execute(
            """
            INSERT INTO politica_sla (plano_id, prioridade, minutos_uteis_primeira_resposta,
                                      minutos_uteis_resolucao, vigencia)
            VALUES (%s, 'baixa', 480, 60, '[2026-01-01,2027-01-01)')
            """,
            (plano_id,),
        )
