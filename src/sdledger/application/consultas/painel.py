"""Modelos de leitura do painel.

Não são entidades: são o resultado de uma pergunta de negócio respondida em SQL
(decisão D02). Os nomes dos campos batem com os nomes das colunas das consultas,
e é isso que permite mapear a linha direto para estes objetos.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


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


@dataclass(frozen=True)
class LinhaDeBacklog:
    """Fila parada agora, por prioridade e faixa de idade em dias corridos."""

    prioridade: str
    total: int
    ate_1_dia: int
    de_1_a_3_dias: int
    de_3_a_7_dias: int
    mais_de_7_dias: int
    idade_maxima_dias: float


@dataclass(frozen=True)
class TaxaDeSla:
    """Cumprimento do prazo vigente na abertura, por prioridade."""

    prioridade: str
    entregues: int
    dentro_do_prazo: int
    taxa_percentual: float


@dataclass(frozen=True)
class SemanaDaTendencia:
    """Uma semana ISO da série do painel."""

    semana: date
    resolvidos: int
    resolucao_p95: float | None
    variacao_p95: float | None
    variacao_resolvidos: int | None
    resolvidos_acumulados: int


@dataclass(frozen=True)
class ClienteCritico:
    """Uma linha do ranking de clientes que merecem atenção."""

    posicao: int
    quartil: int
    cliente_id: int
    nome: str
    chamados: int
    em_aberto: int
    prioritarios: int
    idade_maxima_dias: float
    escore: float
