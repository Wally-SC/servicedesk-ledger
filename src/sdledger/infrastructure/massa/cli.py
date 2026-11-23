"""Linha de comando da geração de massa.

python -m sdledger.infrastructure.massa.cli --perfil pequeno --semente 42
"""

from __future__ import annotations

import argparse
from datetime import date

import psycopg

from sdledger.infrastructure.config import obter_config
from sdledger.infrastructure.massa.gerador import gerar
from sdledger.infrastructure.massa.perfis import PERFIS


def principal() -> None:
    analisador = argparse.ArgumentParser(description="Gera massa fictícia reproduzível.")
    analisador.add_argument("--perfil", choices=sorted(PERFIS), default="pequeno")
    analisador.add_argument("--semente", type=int, default=42)
    analisador.add_argument(
        "--fim",
        type=date.fromisoformat,
        default=date.today(),
        help="Último dia da janela gerada (padrão: hoje).",
    )
    argumentos = analisador.parse_args()

    perfil = PERFIS[argumentos.perfil]
    print(f"Gerando perfil {perfil.nome}: {perfil.chamados} chamados até {argumentos.fim}...")

    with psycopg.connect(obter_config().dsn) as conexao:
        resumo = gerar(conexao, perfil, argumentos.semente, argumentos.fim)
        conexao.commit()

    print(
        f"Pronto: {resumo.clientes} clientes, {resumo.agentes} agentes, "
        f"{resumo.chamados} chamados, {resumo.eventos} eventos, "
        f"{resumo.periodos} períodos, {resumo.apontamentos} apontamentos."
    )


if __name__ == "__main__":
    principal()
