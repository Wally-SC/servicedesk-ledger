"""Carregamento das consultas analíticas em arquivo.

O SQL vive em arquivo versionado, não em string no meio do Python (decisão D03):
é o arquivo que é revisado no pull request e medido no laboratório de índices.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1] / "sql"


@lru_cache
def carregar(caminho: str) -> str:
    """Devolve o conteúdo de uma consulta, por caminho relativo a sql/."""
    arquivo = RAIZ / caminho
    if not arquivo.is_file():
        raise FileNotFoundError(f"consulta não encontrada: {arquivo}")
    return arquivo.read_text(encoding="utf-8")
