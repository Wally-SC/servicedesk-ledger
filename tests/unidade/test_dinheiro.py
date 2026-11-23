"""Dinheiro em centavos: sem float, sem surpresa na fatura."""

from __future__ import annotations

import pytest

from sdledger.domain.comum.dinheiro import Dinheiro
from sdledger.domain.comum.duracao import Duracao
from sdledger.domain.comum.erros import ValorInvalido


def test_valor_negativo_nao_existe() -> None:
    with pytest.raises(ValorInvalido):
        Dinheiro(-1)


def test_soma() -> None:
    assert Dinheiro(1050) + Dinheiro(2500) == Dinheiro(3550)


@pytest.mark.parametrize(
    ("preco_hora", "minutos", "esperado"),
    [
        (12000, 60, 12000),
        (12000, 30, 6000),
        (12000, 15, 3000),
        (12000, 0, 0),
        (10000, 45, 7500),
    ],
)
def test_preco_por_hora_aplicado_a_duracao(preco_hora: int, minutos: int, esperado: int) -> None:
    assert Dinheiro(preco_hora).por_duracao(Duracao(minutos)) == Dinheiro(esperado)


def test_arredondamento_de_centavo_e_meio_para_cima() -> None:
    """1 centavo por hora em 30 minutos dá meio centavo: vira 1, não 0."""
    assert Dinheiro(1).por_duracao(Duracao(30)) == Dinheiro(1)


def test_formatacao() -> None:
    assert str(Dinheiro(49900)) == "R$ 499,00"
    assert str(Dinheiro(5)) == "R$ 0,05"
