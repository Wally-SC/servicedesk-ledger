"""Modelos de leitura do painel.

Não são entidades: são o resultado de uma pergunta de negócio respondida em SQL
(decisão D02). Os nomes dos campos batem com os nomes das colunas das consultas,
e é isso que permite mapear a linha direto para estes objetos.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Janela:
    """Intervalo analisado, fechado no início e aberto no fim."""

    inicio: datetime
    fim: datetime


@dataclass(frozen=True)
class PercentisDeAtendimento:
    """Tempos de primeira resposta e de resolução, em minutos úteis."""

    resolvidos: int
    sem_primeira_resposta: int
    resposta_p50: float | None
    resposta_p90: float | None
    resposta_p95: float | None
    resolucao_p50: float | None
    resolucao_p90: float | None
    resolucao_p95: float | None
