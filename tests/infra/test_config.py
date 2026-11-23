"""A configuração vem do ambiente, e o DSN é montado a partir dela."""

from __future__ import annotations

import pytest

from sdledger.infrastructure.config import Config, obter_config


@pytest.fixture(autouse=True)
def _sem_cache() -> None:
    obter_config.cache_clear()


def test_dsn_usa_os_valores_do_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_HOST", "banco-de-teste")
    monkeypatch.setenv("POSTGRES_PORT", "6543")
    monkeypatch.setenv("POSTGRES_DB", "sdl")
    monkeypatch.setenv("POSTGRES_USER", "usuario")
    monkeypatch.setenv("POSTGRES_PASSWORD", "segredo")

    config = Config(_env_file=None)

    assert config.dsn == "postgresql://usuario:segredo@banco-de-teste:6543/sdl"


def test_dsn_do_laboratorio_aponta_para_outro_banco(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_DB", "sdl")
    monkeypatch.setenv("LAB_POSTGRES_DB", "sdl_lab")

    config = Config(_env_file=None)

    assert config.dsn != config.dsn_laboratorio
    assert config.dsn_laboratorio.endswith("/sdl_lab")
