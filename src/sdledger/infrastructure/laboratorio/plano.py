"""Leitura do plano de execução.

O JSON do EXPLAIN é completo e ilegível. Aqui ele vira uma lista de nós em
profundidade, com o que importa para comparar dois planos: a operação, sobre
qual tabela e índice, quanto tempo levou e quanto leu de disco e de cache.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NoDoPlano:
    """Um nó do plano.

    O tempo é por laço, como o próprio EXPLAIN reporta. Multiplicar pelo número
    de laços parece somar o custo total, mas em plano paralelo os laços são os
    workers rodando ao mesmo tempo: a primeira versão fazia essa conta e
    mostrava um Sort de 140 ms dentro de uma consulta de 53 ms.
    """

    profundidade: int
    operacao: str
    detalhe: str
    tempo_ms: float
    lacos: int
    linhas: int
    blocos_em_cache: int
    blocos_lidos: int


def tempo_de_execucao(plano: list[dict[str, Any]]) -> float:
    return float(plano[0]["Execution Time"])


def resumir(plano: list[dict[str, Any]]) -> list[NoDoPlano]:
    """Achata a árvore do plano, pai antes dos filhos."""
    nos: list[NoDoPlano] = []

    def visitar(no: dict[str, Any], profundidade: int) -> None:
        partes = []
        if "Relation Name" in no:
            partes.append(f"em {no['Relation Name']}")
        if "Index Name" in no:
            partes.append(f"usando {no['Index Name']}")
        lacos = int(no.get("Actual Loops", 1)) or 1
        nos.append(
            NoDoPlano(
                profundidade=profundidade,
                operacao=str(no["Node Type"]),
                detalhe=" ".join(partes),
                tempo_ms=float(no.get("Actual Total Time", 0.0)),
                lacos=lacos,
                linhas=int(no.get("Actual Rows", 0)) * lacos,
                blocos_em_cache=int(no.get("Shared Hit Blocks", 0)),
                blocos_lidos=int(no.get("Shared Read Blocks", 0)),
            )
        )
        for filho in no.get("Plans", []):
            visitar(filho, profundidade + 1)

    visitar(plano[0]["Plan"], 0)
    return nos


def usa_indice(plano: list[dict[str, Any]], indice: str) -> bool:
    return any(indice in no.detalhe for no in resumir(plano))
