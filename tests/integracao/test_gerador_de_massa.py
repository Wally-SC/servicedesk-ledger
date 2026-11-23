"""A massa fictícia precisa ser reproduzível: mesma semente, mesmo banco.

Sem isso, nenhum número do laboratório de índices pode ser comparado com outro,
porque não dá para saber se a diferença veio do índice ou de dados diferentes.
"""

from __future__ import annotations

from datetime import date

import psycopg
import pytest

from sdledger.infrastructure.massa.gerador import gerar
from sdledger.infrastructure.massa.perfis import PEQUENO

pytestmark = pytest.mark.integracao

FIM = date(2026, 11, 23)


def _impressao_digital(conexao: psycopg.Connection) -> str:
    """Resumo do conteúdo gerado, estável para a mesma massa."""
    linha = conexao.execute(
        """
        SELECT md5(string_agg(assinatura, '|' ORDER BY assinatura))
        FROM (
            SELECT concat_ws(';', id, cliente_id, prioridade, estado, aberto_em,
                             primeira_resposta_em, resolvido_em) AS assinatura
            FROM chamado
        ) AS c
        """
    ).fetchone()
    assert linha is not None
    return str(linha[0])


def test_mesma_semente_produz_a_mesma_massa(conexao: psycopg.Connection) -> None:
    gerar(conexao, PEQUENO, semente=42, fim=FIM)
    primeira = _impressao_digital(conexao)

    gerar(conexao, PEQUENO, semente=42, fim=FIM)
    segunda = _impressao_digital(conexao)

    assert primeira == segunda


def test_sementes_diferentes_produzem_massas_diferentes(conexao: psycopg.Connection) -> None:
    gerar(conexao, PEQUENO, semente=42, fim=FIM)
    com_42 = _impressao_digital(conexao)

    gerar(conexao, PEQUENO, semente=7, fim=FIM)
    com_7 = _impressao_digital(conexao)

    assert com_42 != com_7


def test_a_massa_tem_o_tamanho_do_perfil(conexao: psycopg.Connection) -> None:
    resumo = gerar(conexao, PEQUENO, semente=42, fim=FIM)

    total = conexao.execute("SELECT count(*) FROM chamado").fetchone()
    assert total is not None
    assert total[0] == PEQUENO.chamados == resumo.chamados


def test_a_massa_respeita_a_janela_pedida(conexao: psycopg.Connection) -> None:
    gerar(conexao, PEQUENO, semente=42, fim=FIM)

    linha = conexao.execute(
        "SELECT min(aberto_em)::date, max(aberto_em)::date FROM chamado"
    ).fetchone()
    assert linha is not None
    primeiro, ultimo = linha
    assert ultimo <= FIM
    assert (FIM - primeiro).days <= PEQUENO.meses * 30


def test_parte_dos_chamados_fica_sem_primeira_resposta(conexao: psycopg.Connection) -> None:
    """O painel precisa desse caso: ele é contado à parte, fora do percentil."""
    gerar(conexao, PEQUENO, semente=42, fim=FIM)

    linha = conexao.execute(
        "SELECT count(*) FILTER (WHERE primeira_resposta_em IS NULL) FROM chamado"
    ).fetchone()
    assert linha is not None
    assert 0 < linha[0] < PEQUENO.chamados
