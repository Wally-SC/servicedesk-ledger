"""O banco impede dois contratos do mesmo cliente valendo no mesmo dia."""

from __future__ import annotations

import psycopg
import pytest

pytestmark = pytest.mark.integracao


def test_contratos_sobrepostos_sao_rejeitados(
    conexao: psycopg.Connection, cliente_id: int, plano_id: int
) -> None:
    conexao.execute(
        "INSERT INTO contrato (cliente_id, plano_id, vigencia) VALUES (%s, %s, %s)",
        (cliente_id, plano_id, "[2026-01-01,2026-07-01)"),
    )

    with pytest.raises(psycopg.errors.ExclusionViolation):
        conexao.execute(
            "INSERT INTO contrato (cliente_id, plano_id, vigencia) VALUES (%s, %s, %s)",
            (cliente_id, plano_id, "[2026-06-01,2027-01-01)"),
        )


def test_contratos_colados_sao_aceitos(
    conexao: psycopg.Connection, cliente_id: int, plano_id: int
) -> None:
    """Fim de um e começo do outro no mesmo dia não é sobreposição: o
    daterange é fechado-aberto, então [a,b) e [b,c) não se tocam."""
    conexao.execute(
        "INSERT INTO contrato (cliente_id, plano_id, vigencia) VALUES (%s, %s, %s)",
        (cliente_id, plano_id, "[2026-01-01,2026-07-01)"),
    )
    conexao.execute(
        "INSERT INTO contrato (cliente_id, plano_id, vigencia) VALUES (%s, %s, %s)",
        (cliente_id, plano_id, "[2026-07-01,2027-01-01)"),
    )

    total = conexao.execute(
        "SELECT count(*) FROM contrato WHERE cliente_id = %s", (cliente_id,)
    ).fetchone()
    assert total is not None and total[0] == 2


def test_plano_com_franquia_zero_e_rejeitado(conexao: psycopg.Connection) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        conexao.execute(
            """
            INSERT INTO plano (nome, franquia_minutos, mensalidade_centavos,
                               preco_hora_excedente_centavos)
            VALUES ('Zerado', 0, 1000, 1000)
            """
        )
