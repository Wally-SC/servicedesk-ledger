"""Franquia e excedente: a conta que vira dinheiro na fatura."""

from __future__ import annotations

import pytest

from sdledger.domain.comum.dinheiro import Dinheiro
from sdledger.domain.comum.duracao import Duracao
from sdledger.domain.contrato.franquia import Franquia

FRANQUIA = Franquia(inclusa=Duracao(600), preco_hora_excedente=Dinheiro(12000))


@pytest.mark.parametrize(
    ("consumido", "excedente"),
    [
        (0, 0),
        (599, 0),
        (600, 0),
        (601, 15),
        (615, 15),
        (616, 30),
        (900, 300),
    ],
)
def test_excedente_arredonda_para_o_bloco(consumido: int, excedente: int) -> None:
    assert FRANQUIA.excedente(Duracao(consumido)) == Duracao(excedente)


def test_valor_do_excedente() -> None:
    """601 minutos consumidos: 1 minuto além vira 15, e 15 minutos a 120 reais a
    hora custam 30 reais."""
    assert FRANQUIA.valor_do_excedente(Duracao(601)) == Dinheiro(3000)


def test_sem_excedente_nao_ha_cobranca() -> None:
    assert FRANQUIA.valor_do_excedente(Duracao(600)) == Dinheiro(0)
