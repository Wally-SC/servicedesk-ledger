"""Portas das consultas analíticas.

A rota depende desta interface, não do SQL. É o que mantém a regra de
dependências apontando para dentro mesmo com a leitura saindo do domínio
(decisão D02).
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from sdledger.application.consultas.painel import (
    ClienteCritico,
    Janela,
    LinhaDeBacklog,
    PercentisDeAtendimento,
    SemanaDaTendencia,
    TaxaDeSla,
)


class ConsultasDoPainel(Protocol):
    def percentis(self, janela: Janela) -> PercentisDeAtendimento: ...

    def backlog(self, agora: datetime) -> list[LinhaDeBacklog]: ...

    def taxa_de_sla(self, janela: Janela) -> list[TaxaDeSla]: ...

    def tendencia_semanal(self, janela: Janela) -> list[SemanaDaTendencia]: ...

    def clientes_criticos(
        self, janela: Janela, agora: datetime, limite: int = 10
    ) -> list[ClienteCritico]: ...
