"""Leitura do plano de execução."""

from __future__ import annotations

from typing import Any

from sdledger.infrastructure.laboratorio.plano import resumir, tempo_de_execucao, usa_indice

PLANO: list[dict[str, Any]] = [
    {
        "Plan": {
            "Node Type": "Limit",
            "Actual Total Time": 0.031,
            "Actual Rows": 50,
            "Actual Loops": 1,
            "Shared Hit Blocks": 53,
            "Plans": [
                {
                    "Node Type": "Index Scan",
                    "Relation Name": "chamado",
                    "Index Name": "lab_chamado_cliente_abertura",
                    "Actual Total Time": 0.024,
                    "Actual Rows": 50,
                    "Actual Loops": 1,
                    "Shared Hit Blocks": 53,
                    "Shared Read Blocks": 2,
                }
            ],
        },
        "Execution Time": 0.05,
    }
]

PARALELO: list[dict[str, Any]] = [
    {
        "Plan": {
            "Node Type": "Gather",
            "Actual Total Time": 53.0,
            "Actual Rows": 3,
            "Actual Loops": 1,
            "Plans": [
                {
                    "Node Type": "Sort",
                    "Actual Total Time": 46.8,
                    "Actual Rows": 249,
                    "Actual Loops": 3,
                }
            ],
        },
        "Execution Time": 53.4,
    }
]


def test_achata_a_arvore_com_profundidade() -> None:
    nos = resumir(PLANO)

    assert [(n.profundidade, n.operacao) for n in nos] == [(0, "Limit"), (1, "Index Scan")]
    assert nos[1].detalhe == "em chamado usando lab_chamado_cliente_abertura"
    assert nos[1].blocos_lidos == 2


def test_tempo_e_por_laco_e_nao_somado_entre_workers() -> None:
    """Somar os três workers daria 140 ms dentro de uma consulta de 53 ms."""
    sort = resumir(PARALELO)[1]

    assert sort.tempo_ms == 46.8
    assert sort.lacos == 3
    assert sort.linhas == 747
    assert sort.tempo_ms <= tempo_de_execucao(PARALELO)


def test_detecta_uso_do_indice() -> None:
    assert usa_indice(PLANO, "lab_chamado_cliente_abertura")
    assert not usa_indice(PLANO, "outro_indice")
