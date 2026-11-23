"""Porta do faturamento.

As leituras são por competência inteira, de uma vez, e não por cliente: fechar
um mês de 300 clientes cliente a cliente seria 300 idas ao banco para cada
pergunta.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from sdledger.domain.comum.dinheiro import Dinheiro
from sdledger.domain.comum.duracao import Duracao
from sdledger.domain.contrato.franquia import Franquia
from sdledger.domain.faturamento.fatura import FaturaCalculada


@dataclass(frozen=True)
class CondicoesDoPlano:
    """O que o plano do cliente cobra naquela competência."""

    mensalidade: Dinheiro
    franquia: Franquia


class RepositorioDeFaturamento(Protocol):
    def condicoes_da_competencia(self, competencia: date) -> dict[int, CondicoesDoPlano]: ...

    def consumo_da_competencia(self, competencia: date) -> dict[int, Duracao]: ...

    def clientes_ja_fechados(self, competencia: date) -> set[int]: ...

    def gravar_fechamento(
        self,
        cliente_id: int,
        fatura: FaturaCalculada,
        emitida_em: datetime,
        vencimento: date,
    ) -> None: ...
