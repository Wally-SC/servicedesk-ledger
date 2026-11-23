"""Cálculo da fatura: mensalidade, excedente e datas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from sdledger.domain.comum.dinheiro import Dinheiro
from sdledger.domain.comum.duracao import Duracao
from sdledger.domain.comum.erros import ValorInvalido
from sdledger.domain.contrato.franquia import Franquia
from sdledger.domain.faturamento.fatura import calcular_fatura, emissao, vencimento

FRANQUIA = Franquia(inclusa=Duracao(600), preco_hora_excedente=Dinheiro(12000))
MENSALIDADE = Dinheiro(49900)
MAIO = date(2026, 5, 1)


def test_sem_excedente_a_fatura_e_so_a_mensalidade() -> None:
    fatura = calcular_fatura(MAIO, MENSALIDADE, FRANQUIA, Duracao(600))

    assert [item.tipo for item in fatura.itens] == ["mensalidade"]
    assert fatura.total == MENSALIDADE


def test_excedente_entra_como_item_proprio() -> None:
    """750 minutos contra franquia de 600: 150 minutos, 2,5 h a R$ 120."""
    fatura = calcular_fatura(MAIO, MENSALIDADE, FRANQUIA, Duracao(750))

    excedente = fatura.itens[1]
    assert excedente.tipo == "hora_excedente"
    assert excedente.quantidade == Decimal("2.50")
    assert excedente.valor == Dinheiro(30000)
    assert fatura.total == Dinheiro(79900)


def test_um_minuto_alem_cobra_o_bloco_inteiro() -> None:
    fatura = calcular_fatura(MAIO, MENSALIDADE, FRANQUIA, Duracao(601))

    assert fatura.itens[1].quantidade == Decimal("0.25")
    assert fatura.itens[1].valor == Dinheiro(3000)


def test_competencia_fora_do_primeiro_dia_e_recusada() -> None:
    with pytest.raises(ValorInvalido):
        calcular_fatura(date(2026, 5, 15), MENSALIDADE, FRANQUIA, Duracao(0))


@pytest.mark.parametrize(
    ("competencia", "esperado"),
    [
        (date(2026, 1, 1), date(2026, 2, 10)),
        (date(2026, 2, 1), date(2026, 3, 10)),
        (date(2026, 12, 1), date(2027, 1, 10)),
    ],
)
def test_vencimento_no_dia_10_do_mes_seguinte(competencia: date, esperado: date) -> None:
    assert vencimento(competencia) == esperado


def test_emissao_no_primeiro_dia_do_mes_seguinte() -> None:
    assert emissao(date(2026, 12, 1)).date() == date(2027, 1, 1)
