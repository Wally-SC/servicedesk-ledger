"""Caso de uso: solicitar uma medição ao laboratório."""

from __future__ import annotations

from sdledger.application.portas.laboratorio import ExecucaoDoLaboratorio, RepositorioDeExecucoes
from sdledger.domain.comum.erros import Conflito, NaoEncontrado, ValorInvalido

REPETICOES_MAXIMAS = 15


class SolicitarMedicao:
    """Registra o pedido; quem executa é o processo em segundo plano.

    A checagem de medição em andamento aqui é a primeira barreira, e não a
    única: dois pedidos no mesmo instante passariam os dois por ela. A garantia
    de verdade é a trava consultiva que o executor pega no PostgreSQL.
    """

    def __init__(self, repositorio: RepositorioDeExecucoes, experimentos: frozenset[str]) -> None:
        self._repositorio = repositorio
        self._experimentos = experimentos

    def executar(self, experimento: str, repeticoes: int) -> ExecucaoDoLaboratorio:
        if experimento not in self._experimentos:
            raise NaoEncontrado(f"experimento desconhecido: {experimento}")
        if not 1 <= repeticoes <= REPETICOES_MAXIMAS:
            raise ValorInvalido(f"repetições devem ficar entre 1 e {REPETICOES_MAXIMAS}")
        andamento = self._repositorio.em_andamento()
        if andamento is not None:
            raise Conflito(
                f"já existe uma medição em andamento: {andamento.experimento} (#{andamento.id})"
            )
        return self._repositorio.solicitar(experimento, repeticoes)
