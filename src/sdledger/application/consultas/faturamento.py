"""Modelos de leitura da cobrança.

Valores em centavos inteiros, como no banco e no domínio: a conversão para reais
acontece só na apresentação.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ReceitaDaCompetencia:
    competencia: date
    faturas: int
    mensalidades_centavos: int
    excedente_centavos: int
    receita_centavos: int
    variacao_percentual: float | None


@dataclass(frozen=True)
class ReceitaEmAtraso:
    faturas: int
    clientes: int
    total_centavos: int
    ate_30_dias_centavos: int
    de_31_a_90_dias_centavos: int
    mais_de_90_dias_centavos: int


@dataclass(frozen=True)
class MesDeChurn:
    mes: date
    ativos_no_mes_anterior: int
    perdidos: int
    churn_percentual: float | None
