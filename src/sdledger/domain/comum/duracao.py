"""Duração em minutos.

Minutos inteiros, não float: tempo de atendimento e franquia são somados e
comparados o tempo todo, e ponto flutuante acumula erro onde ninguém olha.
"""

from __future__ import annotations

from dataclasses import dataclass

from sdledger.domain.comum.erros import ValorInvalido


@dataclass(frozen=True, order=True)
class Duracao:
    """Quantidade de minutos, nunca negativa."""

    minutos: int

    def __post_init__(self) -> None:
        if self.minutos < 0:
            raise ValorInvalido(f"duração não pode ser negativa: {self.minutos}")

    @classmethod
    def de_horas(cls, horas: float) -> Duracao:
        return cls(round(horas * 60))

    @property
    def horas(self) -> float:
        return self.minutos / 60

    def __add__(self, outra: Duracao) -> Duracao:
        return Duracao(self.minutos + outra.minutos)

    def __sub__(self, outra: Duracao) -> Duracao:
        """Subtração saturada em zero: consumo abaixo da franquia não é excedente
        negativo, é excedente nenhum."""
        return Duracao(max(0, self.minutos - outra.minutos))

    def arredondada_para_cima(self, bloco: Duracao) -> Duracao:
        """Arredonda para o próximo múltiplo do bloco.

        É assim que hora excedente é cobrada: quem usou um minuto além da
        franquia paga o bloco inteiro.
        """
        if bloco.minutos <= 0:
            raise ValorInvalido("o bloco de arredondamento precisa ser positivo")
        if self.minutos == 0:
            return Duracao(0)
        blocos = -(-self.minutos // bloco.minutos)
        return Duracao(blocos * bloco.minutos)


ZERO = Duracao(0)
BLOCO_DE_COBRANCA = Duracao(15)
