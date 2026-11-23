"""As invariantes do chamado são garantidas pelo banco, não só pelo domínio."""

from __future__ import annotations

import psycopg
import pytest

pytestmark = pytest.mark.integracao

ABERTURA = "2026-11-23 09:00-03"


def _chamado(conexao: psycopg.Connection, cliente_id: int) -> int:
    linha = conexao.execute(
        """
        INSERT INTO chamado (cliente_id, prioridade, assunto, aberto_em)
        VALUES (%s, 'alta', 'Impressora parada', %s)
        RETURNING id
        """,
        (cliente_id, ABERTURA),
    ).fetchone()
    assert linha is not None
    return int(linha[0])


def test_resolvido_sem_data_e_rejeitado(conexao: psycopg.Connection, cliente_id: int) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        conexao.execute(
            """
            INSERT INTO chamado (cliente_id, prioridade, estado, assunto, aberto_em)
            VALUES (%s, 'alta', 'resolvido', 'Sem data', %s)
            """,
            (cliente_id, ABERTURA),
        )


def test_data_de_resolucao_sem_estado_resolvido_e_rejeitada(
    conexao: psycopg.Connection, cliente_id: int
) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        conexao.execute(
            """
            INSERT INTO chamado (cliente_id, prioridade, estado, assunto,
                                 aberto_em, resolvido_em)
            VALUES (%s, 'alta', 'aberto', 'Incoerente', %s, %s)
            """,
            (cliente_id, ABERTURA, "2026-11-23 10:00-03"),
        )


def test_primeira_resposta_antes_da_abertura_e_rejeitada(
    conexao: psycopg.Connection, cliente_id: int
) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        conexao.execute(
            """
            INSERT INTO chamado (cliente_id, prioridade, assunto, aberto_em,
                                 primeira_resposta_em)
            VALUES (%s, 'alta', 'Viajante do tempo', %s, %s)
            """,
            (cliente_id, ABERTURA, "2026-11-22 09:00-03"),
        )


def test_nota_interna_exige_autor(conexao: psycopg.Connection, cliente_id: int) -> None:
    chamado_id = _chamado(conexao, cliente_id)

    with pytest.raises(psycopg.errors.CheckViolation):
        conexao.execute(
            "INSERT INTO chamado_evento (chamado_id, tipo, ocorrido_em) VALUES (%s, %s, %s)",
            (chamado_id, "nota_interna", ABERTURA),
        )


def test_mensagem_do_cliente_nao_pode_ter_autor_agente(
    conexao: psycopg.Connection, cliente_id: int
) -> None:
    chamado_id = _chamado(conexao, cliente_id)
    linha = conexao.execute("INSERT INTO agente (nome) VALUES ('Ana') RETURNING id").fetchone()
    assert linha is not None

    with pytest.raises(psycopg.errors.CheckViolation):
        conexao.execute(
            """
            INSERT INTO chamado_evento (chamado_id, tipo, autor_agente_id, ocorrido_em)
            VALUES (%s, 'mensagem_cliente', %s, %s)
            """,
            (chamado_id, linha[0], ABERTURA),
        )


def test_periodos_de_estado_nao_podem_se_sobrepor(
    conexao: psycopg.Connection, cliente_id: int
) -> None:
    chamado_id = _chamado(conexao, cliente_id)
    conexao.execute(
        "INSERT INTO chamado_periodo_estado (chamado_id, estado, periodo) VALUES (%s, %s, %s)",
        (chamado_id, "aberto", "[2026-11-23 09:00-03,2026-11-23 14:00-03)"),
    )

    with pytest.raises(psycopg.errors.ExclusionViolation):
        conexao.execute(
            "INSERT INTO chamado_periodo_estado (chamado_id, estado, periodo) VALUES (%s, %s, %s)",
            (chamado_id, "em_atendimento", "[2026-11-23 13:00-03,2026-11-23 18:00-03)"),
        )
