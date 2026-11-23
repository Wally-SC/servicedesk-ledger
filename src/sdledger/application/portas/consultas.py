"""Portas das consultas analíticas.

A rota depende desta interface, não do SQL. É o que mantém a regra de
dependências apontando para dentro mesmo com a leitura saindo do domínio
(decisão D02).
"""

from __future__ import annotations

from typing import Protocol

from sdledger.application.consultas.painel import Janela, PercentisDeAtendimento


class ConsultasDoPainel(Protocol):
    def percentis(self, janela: Janela) -> PercentisDeAtendimento: ...
