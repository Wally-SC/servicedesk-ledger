"""Duração e o arredondamento que decide quanto o cliente paga."""

from __future__ import annotations

import pytest

from sdledger.domain.comum.duracao import BLOCO_DE_COBRANCA, Duracao
from sdledger.domain.comum.erros import ValorInvalido


def test_duracao_negativa_nao_existe() -> None:
    with pytest.raises(ValorInvalido):
        Duracao(-1)


def test_subtracao_satura_em_zero() -> None:
    """Consumo abaixo da franquia não é excedente negativo."""
    assert Duracao(30) - Duracao(100) == Duracao(0)


@pytest.mark.parametrize(
    ("minutos", "esperado"),
    [(0, 0), (1, 15), (15, 15), (16, 30), (29, 30), (30, 30), (31, 45)],
)
def test_arredondamento_para_cima_em_blocos(minutos: int, esperado: int) -> None:
    """Um minuto além da franquia paga o bloco inteiro — é a regra de cobrança."""
    assert Duracao(minutos).arredondada_para_cima(BLOCO_DE_COBRANCA) == Duracao(esperado)


def test_bloco_precisa_ser_positivo() -> None:
    with pytest.raises(ValorInvalido):
        Duracao(10).arredondada_para_cima(Duracao(0))


def test_conversao_de_horas() -> None:
    assert Duracao.de_horas(1.5) == Duracao(90)
    assert Duracao(90).horas == 1.5
