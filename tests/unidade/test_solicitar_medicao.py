"""Pedido de medição ao laboratório."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from sdledger.application.casos_de_uso.solicitar_medicao import SolicitarMedicao
from sdledger.application.portas.laboratorio import ExecucaoDoLaboratorio
from sdledger.domain.comum.erros import Conflito, NaoEncontrado, ValorInvalido


def _execucao(id_: int, experimento: str, estado: str) -> ExecucaoDoLaboratorio:
    return ExecucaoDoLaboratorio(
        id_,
        experimento,
        estado,
        datetime.now(UTC),
        None,
        None,
        5,
        None,
        None,
        None,
        None,
        None,
        None,
    )


class RepositorioEmMemoria:
    def __init__(self) -> None:
        self.execucoes: list[ExecucaoDoLaboratorio] = []

    def em_andamento(self) -> ExecucaoDoLaboratorio | None:
        return next((e for e in self.execucoes if e.estado in {"pendente", "rodando"}), None)

    def solicitar(self, experimento: str, repeticoes: int) -> ExecucaoDoLaboratorio:
        execucao = _execucao(len(self.execucoes) + 1, experimento, "pendente")
        self.execucoes.append(execucao)
        return execucao

    def obter(self, execucao_id: int) -> ExecucaoDoLaboratorio | None:
        return None

    def ultimas_por_experimento(self) -> dict[str, ExecucaoDoLaboratorio]:
        return {}


CATALOGO = frozenset({"backlog_em_aberto"})


def test_registra_o_pedido() -> None:
    repositorio = RepositorioEmMemoria()

    execucao = SolicitarMedicao(repositorio, CATALOGO).executar("backlog_em_aberto", 5)

    assert execucao.estado == "pendente"


def test_experimento_fora_do_catalogo_e_recusado() -> None:
    """A tela escolhe pelo nome; nome fora do catálogo nunca vira SQL."""
    with pytest.raises(NaoEncontrado):
        SolicitarMedicao(RepositorioEmMemoria(), CATALOGO).executar("DROP TABLE chamado", 5)


def test_segunda_medicao_em_andamento_e_recusada() -> None:
    repositorio = RepositorioEmMemoria()
    caso = SolicitarMedicao(repositorio, CATALOGO)
    caso.executar("backlog_em_aberto", 5)

    with pytest.raises(Conflito):
        caso.executar("backlog_em_aberto", 5)


@pytest.mark.parametrize("repeticoes", [0, 16])
def test_repeticoes_fora_do_limite(repeticoes: int) -> None:
    with pytest.raises(ValorInvalido):
        SolicitarMedicao(RepositorioEmMemoria(), CATALOGO).executar("backlog_em_aberto", repeticoes)
