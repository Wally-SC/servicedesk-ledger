"""Linha de comando do laboratório.

    python -m sdledger.infrastructure.laboratorio.cli preparar
    python -m sdledger.infrastructure.laboratorio.cli medir --repeticoes 5

O laboratório roda no banco próprio (decisão D12): o DDL de verdade nunca toca o
banco da aplicação.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import psycopg
from alembic import command
from alembic.config import Config as ConfigAlembic

from sdledger.infrastructure.config import obter_config
from sdledger.infrastructure.laboratorio.catalogo import EXPERIMENTOS, obter
from sdledger.infrastructure.laboratorio.medicao import REPETICOES_PADRAO, comparar
from sdledger.infrastructure.massa.gerador import gerar
from sdledger.infrastructure.massa.perfis import GRANDE

RAIZ = Path(__file__).resolve().parents[4]


def preparar(semente: int, fim: date) -> None:
    config = obter_config()
    alembic = ConfigAlembic(str(RAIZ / "alembic.ini"))
    alembic.set_main_option(
        "script_location", str(RAIZ / "src" / "sdledger" / "infrastructure" / "migracoes")
    )
    alembic.attributes["url"] = config.dsn_laboratorio.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )
    command.upgrade(alembic, "head")
    print(f"Gerando o perfil grande no banco do laboratório ({GRANDE.chamados} chamados)...")
    with psycopg.connect(config.dsn_laboratorio) as conexao:
        gerar(conexao, GRANDE, semente, fim)
        conexao.commit()
    # Tabela recém-carregada por COPY não tem mapa de visibilidade: nenhum
    # index-only scan consegue evitar a ida à tabela, e o índice parece pior do
    # que é. Produção vive com autovacuum; o laboratório mede nesse estado.
    print("Rodando VACUUM (ANALYZE) para medir a tabela como produção a veria...")
    with psycopg.connect(config.dsn_laboratorio, autocommit=True) as conexao:
        conexao.execute("VACUUM (ANALYZE)")
    print("Laboratório preparado.")


def _ms(valor: float) -> str:
    return f"{valor:.2f} ms" if valor < 10 else f"{valor:.1f} ms"


def medir(nomes: list[str], repeticoes: int) -> None:
    escolhidos = [obter(nome) for nome in nomes] if nomes else list(EXPERIMENTOS)
    print("| experimento | sem índice | com índice | ganho |")
    print("|---|---:|---:|---:|")
    ambiente = ""
    with psycopg.connect(obter_config().dsn_laboratorio, autocommit=True) as conexao:
        for experimento in escolhidos:
            if experimento is None:
                raise SystemExit("experimento desconhecido")
            resultado = comparar(conexao, experimento, repeticoes)
            ambiente = resultado.ambiente
            print(
                f"| {experimento.nome} | {_ms(resultado.sem_indice.mediana_ms)} "
                f"| {_ms(resultado.com_indice.mediana_ms)} | {resultado.ganho:.1f}x |"
            )
    print(f"\n{ambiente}")


def principal() -> None:
    analisador = argparse.ArgumentParser(description="Laboratório de índices.")
    comandos = analisador.add_subparsers(dest="comando", required=True)

    prep = comandos.add_parser("preparar", help="Migra e semeia o banco do laboratório.")
    prep.add_argument("--semente", type=int, default=42)
    prep.add_argument("--fim", type=date.fromisoformat, default=date.today())

    med = comandos.add_parser("medir", help="Mede os experimentos e imprime a tabela.")
    med.add_argument("--experimento", action="append", default=[])
    med.add_argument("--repeticoes", type=int, default=REPETICOES_PADRAO)

    argumentos = analisador.parse_args()
    if argumentos.comando == "preparar":
        preparar(argumentos.semente, argumentos.fim)
    else:
        medir(argumentos.experimento, argumentos.repeticoes)


if __name__ == "__main__":
    principal()
