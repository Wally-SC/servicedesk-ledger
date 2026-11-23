"""Modelos de leitura da cobrança.

Valores em centavos inteiros, como no banco e no domínio: a conversão para reais
acontece só na apresentação.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class JanelaDeCompetencias:
    """Competências fechadas: do primeiro dia de `inicio` até antes de `fim`."""

    inicio: date
    fim: date

    @classmethod
    def ultimas(cls, hoje: date, meses: int) -> JanelaDeCompetencias:
        """As últimas `meses` competências fechadas, sem o mês corrente.

        O mês corrente fica de fora pelo mesmo motivo da semana corrente na
        tendência: ele ainda não foi faturado, e mostrá-lo como receita zero
        desenharia uma queda que não aconteceu.
        """
        fim = hoje.replace(day=1)
        ano, mes = divmod(fim.year * 12 + fim.month - 1 - meses, 12)
        return cls(inicio=date(ano, mes + 1, 1), fim=fim)


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
