"""Repositório do faturamento sobre PostgreSQL."""

from __future__ import annotations

from datetime import date, datetime

import psycopg

from sdledger.application.portas.faturamento import CondicoesDoPlano
from sdledger.domain.comum.dinheiro import Dinheiro
from sdledger.domain.comum.duracao import Duracao
from sdledger.domain.contrato.franquia import Franquia
from sdledger.domain.faturamento.fatura import FaturaCalculada, primeiro_dia_do_mes_seguinte

FUSO = "America/Sao_Paulo"


class RepositorioDeFaturamentoEmPostgres:
    def __init__(self, conexao: psycopg.Connection) -> None:
        self._conexao = conexao

    def condicoes_da_competencia(self, competencia: date) -> dict[int, CondicoesDoPlano]:
        """O plano mais recente de cada cliente dentro da competência.

        Quem trocou de plano no meio do mês paga o plano novo; quem saiu no meio
        do mês ainda paga o mês em que teve contrato (ADR-0009).
        """
        linhas = self._conexao.execute(
            """
            SELECT DISTINCT ON (ct.cliente_id)
                   ct.cliente_id, p.mensalidade_centavos, p.franquia_minutos,
                   p.preco_hora_excedente_centavos
            FROM contrato ct
            JOIN plano p ON p.id = ct.plano_id
            WHERE ct.vigencia && daterange(%(inicio)s, %(fim)s)
            ORDER BY ct.cliente_id, lower(ct.vigencia) DESC
            """,
            {"inicio": competencia, "fim": primeiro_dia_do_mes_seguinte(competencia)},
        ).fetchall()
        return {
            cliente_id: CondicoesDoPlano(
                mensalidade=Dinheiro(mensalidade),
                franquia=Franquia(Duracao(franquia), Dinheiro(excedente)),
            )
            for cliente_id, mensalidade, franquia, excedente in linhas
        }

    def consumo_da_competencia(self, competencia: date) -> dict[int, Duracao]:
        """Minutos apontados no mês, no fuso da análise, por cliente."""
        linhas = self._conexao.execute(
            f"""
            SELECT c.cliente_id, sum(a.minutos)
            FROM apontamento a
            JOIN chamado c ON c.id = a.chamado_id
            WHERE a.apontado_em >= (%(inicio)s::timestamp AT TIME ZONE '{FUSO}')
              AND a.apontado_em <  (%(fim)s::timestamp AT TIME ZONE '{FUSO}')
            GROUP BY c.cliente_id
            """,
            {"inicio": competencia, "fim": primeiro_dia_do_mes_seguinte(competencia)},
        ).fetchall()
        return {cliente_id: Duracao(int(minutos)) for cliente_id, minutos in linhas}

    def clientes_ja_fechados(self, competencia: date) -> set[int]:
        linhas = self._conexao.execute(
            "SELECT cliente_id FROM ciclo_faturamento WHERE competencia = %s", (competencia,)
        ).fetchall()
        return {cliente_id for (cliente_id,) in linhas}

    def gravar_fechamento(
        self,
        cliente_id: int,
        fatura: FaturaCalculada,
        emitida_em: datetime,
        vencimento: date,
    ) -> None:
        ciclo = self._conexao.execute(
            """
            INSERT INTO ciclo_faturamento (cliente_id, competencia, fechado_em)
            VALUES (%s, %s, %s) RETURNING id
            """,
            (cliente_id, fatura.competencia, emitida_em),
        ).fetchone()
        assert ciclo is not None
        registro = self._conexao.execute(
            """
            INSERT INTO fatura (ciclo_id, estado, emitida_em, vencimento, total_centavos)
            VALUES (%s, 'emitida', %s, %s, %s) RETURNING id
            """,
            (ciclo[0], emitida_em, vencimento, fatura.total.centavos),
        ).fetchone()
        assert registro is not None
        with self._conexao.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO fatura_item (fatura_id, tipo, descricao, quantidade,
                                         valor_unitario_centavos, valor_centavos)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        registro[0],
                        item.tipo,
                        item.descricao,
                        item.quantidade,
                        item.valor_unitario.centavos,
                        item.valor.centavos,
                    )
                    for item in fatura.itens
                ],
            )
