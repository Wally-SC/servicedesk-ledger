"""Dependências das rotas.

É aqui, e só aqui, que a API escolhe a implementação concreta de cada porta. Os
testes trocam estas funções por dublês sem tocar nas rotas.
"""

from __future__ import annotations

from collections.abc import Iterator

import psycopg
from fastapi import Depends, Request
from psycopg_pool import ConnectionPool

from sdledger.application.portas.consultas import ConsultasDoPainel
from sdledger.application.portas.relogio import Relogio
from sdledger.infrastructure.consultas.painel import ConsultasDoPainelEmPostgres
from sdledger.infrastructure.relogio import RelogioDoSistema


def obter_pool(request: Request) -> ConnectionPool:
    pool: ConnectionPool = request.app.state.pool
    return pool


def obter_conexao(pool: ConnectionPool = Depends(obter_pool)) -> Iterator[psycopg.Connection]:
    with pool.connection() as conexao:
        yield conexao


def obter_consultas_do_painel(
    conexao: psycopg.Connection = Depends(obter_conexao),
) -> ConsultasDoPainel:
    return ConsultasDoPainelEmPostgres(conexao)


def obter_relogio() -> Relogio:
    return RelogioDoSistema()
