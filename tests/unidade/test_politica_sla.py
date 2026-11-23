"""Prazos de SLA e as bordas exatas."""

from __future__ import annotations

import pytest

from sdledger.domain.chamado.politica_sla import PoliticaSla
from sdledger.domain.chamado.prioridade import Prioridade
from sdledger.domain.comum.duracao import Duracao
from sdledger.domain.comum.erros import ValorInvalido

POLITICA = PoliticaSla(Prioridade.ALTA, Duracao(60), Duracao(960))


@pytest.mark.parametrize(
    ("decorrido", "no_prazo"),
    [(0, True), (59, True), (60, True), (61, False)],
)
def test_borda_do_prazo_de_resposta(decorrido: int, no_prazo: bool) -> None:
    """O minuto exato do prazo ainda está dentro; o seguinte não."""
    assert POLITICA.resposta_no_prazo(Duracao(decorrido)) is no_prazo


def test_resolucao_menor_que_resposta_nao_existe() -> None:
    with pytest.raises(ValorInvalido):
        PoliticaSla(Prioridade.BAIXA, Duracao(480), Duracao(60))


def test_prazo_zerado_nao_existe() -> None:
    with pytest.raises(ValorInvalido):
        PoliticaSla(Prioridade.BAIXA, Duracao(0), Duracao(60))
