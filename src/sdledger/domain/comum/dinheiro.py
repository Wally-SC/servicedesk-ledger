"""Dinheiro em centavos inteiros.

Ponto flutuante não é tipo para dinheiro: 0.1 + 0.2 não dá 0.3, e isso vira
diferença de centavo na fatura do cliente.
"""

from __future__ import annotations

from dataclasses import dataclass

from sdledger.domain.comum.duracao import Duracao
from sdledger.domain.comum.erros import ValorInvalido


@dataclass(frozen=True, order=True)
class Dinheiro:
    """Valor em centavos, nunca negativo."""

    centavos: int

    def __post_init__(self) -> None:
        if self.centavos < 0:
            raise ValorInvalido(f"valor não pode ser negativo: {self.centavos}")

    def __add__(self, outro: Dinheiro) -> Dinheiro:
        return Dinheiro(self.centavos + outro.centavos)

    def por_duracao(self, duracao: Duracao) -> Dinheiro:
        """Preço por hora aplicado a uma duração, arredondando para o centavo.

        O arredondamento é de meio para cima, explícito, para não depender do
        arredondamento bancário do float.
        """
        total = self.centavos * duracao.minutos
        return Dinheiro((total + 30) // 60)

    def __str__(self) -> str:
        return f"R$ {self.centavos // 100},{self.centavos % 100:02d}"


SEM_VALOR = Dinheiro(0)
