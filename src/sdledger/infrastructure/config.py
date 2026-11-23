"""Configuração lida do ambiente.

Nenhuma credencial no código: tudo vem de variável de ambiente, com os mesmos
nomes documentados em `.env.example`.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Valores de ambiente da aplicação."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "sdledger"
    postgres_user: str = "sdledger"
    postgres_password: str = "troque-isto"
    lab_postgres_db: str = "sdledger_lab"
    tz_analise: str = "America/Sao_Paulo"
    lab_habilitado: bool = True
    lab_token: str = "troque-isto"

    def _dsn(self, banco: str) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{banco}"
        )

    @property
    def dsn(self) -> str:
        """Endereço do banco da aplicação."""
        return self._dsn(self.postgres_db)

    @property
    def dsn_laboratorio(self) -> str:
        """Endereço do banco onde o laboratório cria e remove índice."""
        return self._dsn(self.lab_postgres_db)


@lru_cache
def obter_config() -> Config:
    """Config da aplicação, lida uma vez por processo."""
    return Config()
