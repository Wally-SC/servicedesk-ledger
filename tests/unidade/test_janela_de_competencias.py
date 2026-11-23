"""Janela de competências fechadas."""

from __future__ import annotations

from datetime import date

from sdledger.application.consultas.faturamento import JanelaDeCompetencias


def test_exclui_o_mes_corrente() -> None:
    janela = JanelaDeCompetencias.ultimas(date(2026, 11, 23), 3)

    assert janela.fim == date(2026, 11, 1)
    assert janela.inicio == date(2026, 8, 1)


def test_atravessa_a_virada_do_ano() -> None:
    janela = JanelaDeCompetencias.ultimas(date(2026, 2, 10), 12)

    assert janela.inicio == date(2025, 2, 1)
    assert janela.fim == date(2026, 2, 1)
