"""Configuração do Alembic.

A URL do banco vem do ambiente, pela mesma Config do resto da aplicação. Não há
modelo declarativo: as migrações são SQL escrito à mão (decisão D03), então
`target_metadata` é None de propósito e `autogenerate` não funciona.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import engine_from_config, pool

from sdledger.infrastructure.config import obter_config

config = context.config
# O laboratório migra o próprio banco passando a URL por atributo; sem atributo,
# vale o banco da aplicação.
config.set_main_option(
    "sqlalchemy.url", config.attributes.get("url") or obter_config().dsn_sqlalchemy
)


def migrar_offline() -> None:
    """Gera o SQL sem conectar, para revisão."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def migrar_online() -> None:
    """Aplica as migrações conectando ao banco."""
    secao = config.get_section(config.config_ini_section) or {}
    engine = engine_from_config(secao, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with engine.connect() as conexao:
        context.configure(connection=conexao)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    migrar_offline()
else:
    migrar_online()
