"""Teste de arquitetura: as dependências das camadas apontam para dentro.

Existe para que a regra da arquitetura seja verificada pela esteira, e não apenas
prometida no README. Lê o código com `ast` e falha quando uma camada importa uma
camada de fora ou um framework que ela não deveria conhecer.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PACOTE = Path(__file__).resolve().parents[2] / "src" / "sdledger"

FRAMEWORKS = (
    "fastapi",
    "starlette",
    "uvicorn",
    "psycopg",
    "sqlalchemy",
    "alembic",
    "jinja2",
    "pydantic",
    "pydantic_settings",
)

PROIBIDOS: dict[str, tuple[str, ...]] = {
    "domain": (
        *FRAMEWORKS,
        "sdledger.application",
        "sdledger.infrastructure",
        "sdledger.api",
        "sdledger.web",
    ),
    "application": (
        *FRAMEWORKS,
        "sdledger.infrastructure",
        "sdledger.api",
        "sdledger.web",
    ),
    "infrastructure": (
        "fastapi",
        "starlette",
        "uvicorn",
        "sdledger.api",
        "sdledger.web",
    ),
}


def _pacote_do_arquivo(arquivo: Path) -> tuple[str, ...]:
    """Devolve, em partes, o pacote ao qual o arquivo pertence."""
    partes = arquivo.relative_to(PACOTE.parent).with_suffix("").parts
    return partes[:-1]


def _importados(arquivo: Path) -> list[str]:
    """Lista os módulos importados pelo arquivo, resolvendo import relativo."""
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"), filename=str(arquivo))
    nomes: list[str] = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes.extend(apelido.name for apelido in no.names)
        elif isinstance(no, ast.ImportFrom):
            if no.level:
                pacote = _pacote_do_arquivo(arquivo)
                base = list(pacote[: len(pacote) - (no.level - 1)])
                nomes.append(".".join([*base, no.module] if no.module else base))
            elif no.module:
                nomes.append(no.module)
    return nomes


@pytest.mark.parametrize("camada", sorted(PROIBIDOS))
def test_camada_nao_importa_para_fora(camada: str) -> None:
    violacoes: list[str] = []
    for arquivo in sorted((PACOTE / camada).rglob("*.py")):
        for importado in _importados(arquivo):
            for proibido in PROIBIDOS[camada]:
                if importado == proibido or importado.startswith(f"{proibido}."):
                    violacoes.append(f"{arquivo.relative_to(PACOTE)} importa {importado}")
    assert not violacoes, "dependência apontando para fora:\n" + "\n".join(violacoes)


def test_todas_as_camadas_existem() -> None:
    esperadas = ("domain", "application", "infrastructure", "api", "web")
    faltando = [nome for nome in esperadas if not (PACOTE / nome).is_dir()]
    assert not faltando, f"camadas ausentes: {faltando}"
