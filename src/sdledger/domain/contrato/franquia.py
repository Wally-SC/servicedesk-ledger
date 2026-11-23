"""Franquia de horas do plano."""

from __future__ import annotations

from dataclasses import dataclass

from sdledger.domain.comum.dinheiro import Dinheiro
from sdledger.domain.comum.duracao import BLOCO_DE_COBRANCA, Duracao


@dataclass(frozen=True)
class Franquia:
    """Minutos inclusos no plano e o preço da hora que passar disso."""

    inclusa: Duracao
    preco_hora_excedente: Dinheiro

    def excedente(self, consumido: Duracao) -> Duracao:
        """Minutos além da franquia, arredondados para o bloco de cobrança.

        Quem consumiu menos que a franquia não gera excedente negativo: gera
        excedente nenhum.
        """
        return (consumido - self.inclusa).arredondada_para_cima(BLOCO_DE_COBRANCA)

    def valor_do_excedente(self, consumido: Duracao) -> Dinheiro:
        return self.preco_hora_excedente.por_duracao(self.excedente(consumido))
