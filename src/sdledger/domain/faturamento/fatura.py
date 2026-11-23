"""Cálculo da fatura de um ciclo.

A fatura é derivada de três coisas: a mensalidade do plano, a franquia e o que
o cliente consumiu na competência. A conta vive no domínio porque é regra de
negócio e precisa ser testada nas bordas sem subir banco.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sdledger.domain.comum.dinheiro import SEM_VALOR, Dinheiro
from sdledger.domain.comum.duracao import Duracao
from sdledger.domain.comum.erros import ValorInvalido
from sdledger.domain.contrato.franquia import Franquia

FUSO = timezone(timedelta(hours=-3))
DIA_DE_VENCIMENTO = 10


def primeiro_dia_do_mes_seguinte(competencia: date) -> date:
    return (competencia.replace(day=28) + timedelta(days=4)).replace(day=1)


def validar_competencia(competencia: date) -> None:
    """Competência é sempre o primeiro dia do mês, como no banco."""
    if competencia.day != 1:
        raise ValorInvalido(f"competência precisa ser o primeiro dia do mês: {competencia}")


def emissao(competencia: date) -> datetime:
    """A fatura sai no primeiro dia do mês seguinte, às 9h."""
    validar_competencia(competencia)
    return datetime.combine(primeiro_dia_do_mes_seguinte(competencia), time(9, 0), FUSO)


def vencimento(competencia: date) -> date:
    """Vence no dia 10 do mês seguinte à competência."""
    validar_competencia(competencia)
    return primeiro_dia_do_mes_seguinte(competencia).replace(day=DIA_DE_VENCIMENTO)


@dataclass(frozen=True)
class ItemDeFatura:
    tipo: str
    descricao: str
    quantidade: Decimal
    valor_unitario: Dinheiro
    valor: Dinheiro


@dataclass(frozen=True)
class FaturaCalculada:
    competencia: date
    itens: tuple[ItemDeFatura, ...]

    @property
    def total(self) -> Dinheiro:
        soma = SEM_VALOR
        for item in self.itens:
            soma = soma + item.valor
        return soma


def calcular_fatura(
    competencia: date, mensalidade: Dinheiro, franquia: Franquia, consumido: Duracao
) -> FaturaCalculada:
    """Mensalidade sempre; hora excedente só quando o consumo passa da franquia.

    A quantidade de horas excedentes sai sempre exata em quartos de hora, porque
    o excedente já vem arredondado para o bloco de 15 minutos.
    """
    validar_competencia(competencia)
    itens = [
        ItemDeFatura(
            tipo="mensalidade",
            descricao=f"Mensalidade {competencia:%m/%Y}",
            quantidade=Decimal(1),
            valor_unitario=mensalidade,
            valor=mensalidade,
        )
    ]
    excedente = franquia.excedente(consumido)
    if excedente.minutos > 0:
        horas = (Decimal(excedente.minutos) / Decimal(60)).quantize(Decimal("0.01"))
        itens.append(
            ItemDeFatura(
                tipo="hora_excedente",
                descricao=f"{horas} h além da franquia",
                quantidade=horas,
                valor_unitario=franquia.preco_hora_excedente,
                valor=franquia.valor_do_excedente(consumido),
            )
        )
    return FaturaCalculada(competencia=competencia, itens=tuple(itens))
