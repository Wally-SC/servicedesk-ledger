"""Fechamento de ciclo com repositório em memória."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from sdledger.application.casos_de_uso.fechar_ciclo import FecharCiclo
from sdledger.application.portas.faturamento import CondicoesDoPlano
from sdledger.domain.comum.dinheiro import Dinheiro
from sdledger.domain.comum.duracao import Duracao
from sdledger.domain.comum.erros import ValorInvalido
from sdledger.domain.contrato.franquia import Franquia
from sdledger.domain.faturamento.fatura import FaturaCalculada

PLANO = CondicoesDoPlano(Dinheiro(49900), Franquia(Duracao(600), Dinheiro(12000)))
MAIO = date(2026, 5, 1)


class RepositorioEmMemoria:
    def __init__(self) -> None:
        self.condicoes = {1: PLANO, 2: PLANO, 3: PLANO}
        self.consumo = {1: Duracao(900), 2: Duracao(100)}
        self.fechados: set[int] = set()
        self.gravadas: list[tuple[int, FaturaCalculada, datetime, date]] = []

    def condicoes_da_competencia(self, competencia: date) -> dict[int, CondicoesDoPlano]:
        return self.condicoes

    def consumo_da_competencia(self, competencia: date) -> dict[int, Duracao]:
        return self.consumo

    def clientes_ja_fechados(self, competencia: date) -> set[int]:
        return set(self.fechados)

    def gravar_fechamento(
        self, cliente_id: int, fatura: FaturaCalculada, emitida_em: datetime, vencimento: date
    ) -> None:
        self.gravadas.append((cliente_id, fatura, emitida_em, vencimento))
        self.fechados.add(cliente_id)


def test_emite_uma_fatura_por_cliente_com_contrato() -> None:
    repositorio = RepositorioEmMemoria()

    resumo = FecharCiclo(repositorio).executar(MAIO)

    assert resumo.faturas_emitidas == 3
    assert [cliente for cliente, *_ in repositorio.gravadas] == [1, 2, 3]


def test_cliente_sem_apontamento_paga_so_a_mensalidade() -> None:
    repositorio = RepositorioEmMemoria()

    FecharCiclo(repositorio).executar(MAIO)

    fatura_do_3 = next(f for c, f, *_ in repositorio.gravadas if c == 3)
    assert fatura_do_3.total == Dinheiro(49900)


def test_rodar_de_novo_nao_duplica_fatura() -> None:
    """Fechamento é o tipo de operação que alguém repete depois de uma falha."""
    repositorio = RepositorioEmMemoria()
    caso = FecharCiclo(repositorio)

    caso.executar(MAIO)
    segunda = caso.executar(MAIO)

    assert segunda.faturas_emitidas == 0
    assert segunda.ja_fechados == 3
    assert len(repositorio.gravadas) == 3


def test_total_emitido_soma_as_faturas() -> None:
    """Cliente 1 consumiu 900 min: 300 além da franquia, R$ 600 de excedente."""
    resumo = FecharCiclo(RepositorioEmMemoria()).executar(MAIO)

    assert resumo.total_emitido == Dinheiro(49900 * 3 + 60000)


def test_competencia_invalida_nem_consulta_o_repositorio() -> None:
    with pytest.raises(ValorInvalido):
        FecharCiclo(RepositorioEmMemoria()).executar(date(2026, 5, 2))
