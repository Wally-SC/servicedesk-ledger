"""Caso de uso: fechar o ciclo de faturamento de uma competência."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sdledger.application.portas.faturamento import RepositorioDeFaturamento
from sdledger.domain.comum.dinheiro import SEM_VALOR, Dinheiro
from sdledger.domain.comum.duracao import ZERO
from sdledger.domain.faturamento.fatura import (
    calcular_fatura,
    emissao,
    validar_competencia,
    vencimento,
)


@dataclass(frozen=True)
class ResumoDoFechamento:
    competencia: date
    faturas_emitidas: int
    ja_fechados: int
    total_emitido: Dinheiro


class FecharCiclo:
    """Emite uma fatura por cliente com contrato na competência.

    Idempotente: rodar de novo não duplica fatura, porque cliente já fechado é
    pulado. Isso importa porque fechamento é operação que alguém vai repetir
    depois de uma falha no meio.
    """

    def __init__(self, repositorio: RepositorioDeFaturamento) -> None:
        self._repositorio = repositorio

    def executar(self, competencia: date) -> ResumoDoFechamento:
        validar_competencia(competencia)
        condicoes = self._repositorio.condicoes_da_competencia(competencia)
        consumo = self._repositorio.consumo_da_competencia(competencia)
        fechados = self._repositorio.clientes_ja_fechados(competencia)

        emitidas = 0
        total = SEM_VALOR
        for cliente_id in sorted(condicoes):
            if cliente_id in fechados:
                continue
            plano = condicoes[cliente_id]
            fatura = calcular_fatura(
                competencia, plano.mensalidade, plano.franquia, consumo.get(cliente_id, ZERO)
            )
            self._repositorio.gravar_fechamento(
                cliente_id, fatura, emissao(competencia), vencimento(competencia)
            )
            emitidas += 1
            total = total + fatura.total

        return ResumoDoFechamento(
            competencia=competencia,
            faturas_emitidas=emitidas,
            ja_fechados=len(fechados & set(condicoes)),
            total_emitido=total,
        )
