"""Estados do chamado e as transições permitidas.

O grafo fica num lugar só. Espalhar `if estado ==` pelos casos de uso é como
essas regras se perdem.
"""

from __future__ import annotations

from enum import StrEnum


class Estado(StrEnum):
    ABERTO = "aberto"
    EM_ATENDIMENTO = "em_atendimento"
    AGUARDANDO_CLIENTE = "aguardando_cliente"
    RESOLVIDO = "resolvido"
    FECHADO = "fechado"


TRANSICOES: dict[Estado, frozenset[Estado]] = {
    Estado.ABERTO: frozenset({Estado.EM_ATENDIMENTO, Estado.RESOLVIDO}),
    Estado.EM_ATENDIMENTO: frozenset({Estado.AGUARDANDO_CLIENTE, Estado.RESOLVIDO}),
    Estado.AGUARDANDO_CLIENTE: frozenset({Estado.EM_ATENDIMENTO, Estado.RESOLVIDO}),
    Estado.RESOLVIDO: frozenset({Estado.FECHADO, Estado.ABERTO}),
    Estado.FECHADO: frozenset(),
}


def permite(origem: Estado, destino: Estado) -> bool:
    return destino in TRANSICOES[origem]
