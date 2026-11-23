"""Perfis de massa.

Dois perfis de propósito (decisão D11): o pequeno é determinístico e roda na
esteira em segundos; o grande existe para os índices fazerem diferença visível
no laboratório. Gerar o grande na esteira inviabilizaria o tempo de cada PR.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Perfil:
    """Tamanho de uma carga de massa fictícia."""

    nome: str
    clientes: int
    agentes: int
    chamados: int
    meses: int


PEQUENO = Perfil(nome="pequeno", clientes=12, agentes=5, chamados=2_000, meses=6)
GRANDE = Perfil(nome="grande", clientes=300, agentes=40, chamados=300_000, meses=18)

PERFIS: dict[str, Perfil] = {PEQUENO.nome: PEQUENO, GRANDE.nome: GRANDE}
