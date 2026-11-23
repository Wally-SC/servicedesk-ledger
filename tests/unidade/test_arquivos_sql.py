"""Regras sobre os arquivos .sql versionados.

O psycopg interpreta `%` em qualquer parte do texto da consulta, inclusive em
comentário: um "5%" escrito para explicar a consulta derruba a execução com
"incomplete placeholder". Aconteceu no laboratório; este teste impede que volte.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from sdledger.infrastructure.laboratorio.catalogo import EXPERIMENTOS

RAIZ_SQL = Path(__file__).resolve().parents[2] / "src" / "sdledger" / "infrastructure" / "sql"
ARQUIVOS = sorted(RAIZ_SQL.rglob("*.sql"))
PLACEHOLDER = re.compile(r"%\(\w+\)s")


@pytest.mark.parametrize("arquivo", ARQUIVOS, ids=lambda a: a.relative_to(RAIZ_SQL).as_posix())
def test_nenhum_percentual_solto(arquivo: Path) -> None:
    texto = PLACEHOLDER.sub("", arquivo.read_text(encoding="utf-8"))
    assert "%" not in texto, "use %% ou reescreva o comentário sem o símbolo"


@pytest.mark.parametrize("arquivo", ARQUIVOS, ids=lambda a: a.relative_to(RAIZ_SQL).as_posix())
def test_todo_arquivo_comeca_explicando_a_pergunta(arquivo: Path) -> None:
    primeira = arquivo.read_text(encoding="utf-8").lstrip().splitlines()[0]
    assert primeira.startswith("--"), "cada consulta começa dizendo o que responde"


@pytest.mark.parametrize("experimento", EXPERIMENTOS, ids=lambda e: e.nome)
def test_experimento_tem_consulta_e_indice_coerentes(experimento) -> None:
    consulta = RAIZ_SQL / experimento.consulta_sql
    indice = (RAIZ_SQL / experimento.indice_sql).read_text(encoding="utf-8")

    assert consulta.is_file()
    assert f"CREATE INDEX {experimento.indice} ON {experimento.tabela}" in " ".join(indice.split())
