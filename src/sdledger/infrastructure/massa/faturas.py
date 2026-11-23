"""Histórico de faturas da massa fictícia.

As faturas não são inventadas: cada competência é fechada pelo próprio caso de
uso de fechamento de ciclo, então a massa exercita a mesma regra que produção
exercitaria. Só o pagamento é simulado, porque pagamento é comportamento do
cliente e não regra do sistema.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

import psycopg

from sdledger.application.casos_de_uso.fechar_ciclo import FecharCiclo
from sdledger.domain.faturamento.fatura import FUSO, primeiro_dia_do_mes_seguinte
from sdledger.infrastructure.repositorios.faturamento import RepositorioDeFaturamentoEmPostgres


@dataclass(frozen=True)
class ResumoDeFaturas:
    competencias: int
    faturas: int
    pagas: int
    em_aberto: int


def faturar_historico(conexao: psycopg.Connection, semente: int, fim: date) -> ResumoDeFaturas:
    """Fecha todas as competências completas da janela e simula os pagamentos.

    Não faz commit, pelo mesmo motivo do gerador de chamados.
    """
    rng = random.Random(semente + 1)
    linha = conexao.execute("SELECT min(lower(vigencia)) FROM contrato").fetchone()
    if linha is None or linha[0] is None:
        return ResumoDeFaturas(0, 0, 0, 0)

    competencia = linha[0].replace(day=1)
    ultima = fim.replace(day=1)
    fechamento = FecharCiclo(RepositorioDeFaturamentoEmPostgres(conexao))
    competencias = 0
    while competencia < ultima:
        fechamento.executar(competencia)
        competencias += 1
        competencia = primeiro_dia_do_mes_seguinte(competencia)

    return _simular_pagamentos(conexao, rng, fim, competencias)


def _simular_pagamentos(
    conexao: psycopg.Connection, rng: random.Random, fim: date, competencias: int
) -> ResumoDeFaturas:
    """78% pagam até o vencimento, 12% pagam atrasado, 10% não pagam.

    Nenhum pagamento acontece depois da data final da massa: a massa descreve o
    passado, e fatura paga no futuro seria dado impossível.
    """
    limite = datetime.combine(fim, time(0, 0), FUSO)
    faturas = conexao.execute(
        "SELECT id, emitida_em, vencimento FROM fatura ORDER BY id"
    ).fetchall()

    pagamentos: list[tuple[datetime, int]] = []
    for fatura_id, emitida_em, vencimento in faturas:
        sorteio = rng.random()
        vence = datetime.combine(vencimento, time(18, 0), FUSO)
        if sorteio < 0.78:
            janela = max(1, int((vence - emitida_em).total_seconds() // 60))
            pago_em = emitida_em + timedelta(minutes=rng.randrange(janela))
        elif sorteio < 0.90:
            pago_em = vence + timedelta(days=rng.randrange(1, 46), hours=rng.randrange(9, 18))
        else:
            continue
        if pago_em < limite:
            pagamentos.append((pago_em, fatura_id))

    with conexao.cursor() as cursor:
        cursor.executemany(
            "UPDATE fatura SET estado = 'paga', paga_em = %s WHERE id = %s", pagamentos
        )

    return ResumoDeFaturas(
        competencias=competencias,
        faturas=len(faturas),
        pagas=len(pagamentos),
        em_aberto=len(faturas) - len(pagamentos),
    )
