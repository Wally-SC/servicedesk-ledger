"""Janelas de análise e a borda das semanas."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sdledger.application.consultas.painel import Janela

FUSO = timezone(timedelta(hours=-3))


def test_ultimos_dias_termina_agora() -> None:
    agora = datetime(2026, 11, 23, 2, 5, tzinfo=FUSO)

    janela = Janela.ultimos_dias(agora, 30)

    assert janela.fim == agora
    assert janela.inicio == agora - timedelta(days=30)


def test_semanas_completas_exclui_a_semana_corrente() -> None:
    """Segunda às 2h05: a semana corrente tem duas horas e fica de fora."""
    agora = datetime(2026, 11, 23, 2, 5, tzinfo=FUSO)

    janela = Janela.semanas_completas(agora, 12)

    assert janela.fim == datetime(2026, 11, 23, 0, 0, tzinfo=FUSO)
    assert janela.inicio == datetime(2026, 8, 31, 0, 0, tzinfo=FUSO)


def test_semanas_completas_no_meio_da_semana() -> None:
    quinta = datetime(2026, 11, 26, 15, 0, tzinfo=FUSO)

    janela = Janela.semanas_completas(quinta, 1)

    assert janela.inicio == datetime(2026, 11, 16, 0, 0, tzinfo=FUSO)
    assert janela.fim == datetime(2026, 11, 23, 0, 0, tzinfo=FUSO)
