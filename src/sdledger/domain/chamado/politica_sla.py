"""Política de SLA: o prazo que vale para um chamado."""

from __future__ import annotations

from dataclasses import dataclass

from sdledger.domain.chamado.prioridade import Prioridade
from sdledger.domain.comum.duracao import Duracao
from sdledger.domain.comum.erros import ValorInvalido


@dataclass(frozen=True)
class PoliticaSla:
    """Prazos em minutos úteis para uma prioridade.

    Os prazos são contados em expediente, não em tempo corrido (decisão D06):
    chamado aberto sexta às 17h não vence no sábado de manhã.
    """

    prioridade: Prioridade
    prazo_primeira_resposta: Duracao
    prazo_resolucao: Duracao

    def __post_init__(self) -> None:
        if self.prazo_primeira_resposta.minutos <= 0 or self.prazo_resolucao.minutos <= 0:
            raise ValorInvalido("prazo de SLA precisa ser positivo")
        if self.prazo_resolucao < self.prazo_primeira_resposta:
            raise ValorInvalido("prazo de resolução não pode ser menor que o de resposta")

    def resposta_no_prazo(self, decorrido: Duracao) -> bool:
        return decorrido <= self.prazo_primeira_resposta

    def resolucao_no_prazo(self, decorrido: Duracao) -> bool:
        return decorrido <= self.prazo_resolucao
