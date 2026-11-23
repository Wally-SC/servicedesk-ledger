"""Aplicação FastAPI."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from psycopg_pool import ConnectionPool

from sdledger.api import erros
from sdledger.api.rotas import cobranca, paginas, painel
from sdledger.infrastructure.config import obter_config
from sdledger.infrastructure.db.conexao import banco_responde


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
    """Abre o pool de conexões na subida e fecha na descida.

    `wait=False` deixa a aplicação subir mesmo com o banco ainda acordando; a
    rota /saude é quem diz se ele respondeu.
    """
    pool = ConnectionPool(
        obter_config().dsn, min_size=1, max_size=5, open=False, kwargs={"autocommit": True}
    )
    pool.open(wait=False)
    app.state.pool = pool
    try:
        yield
    finally:
        pool.close()


app = FastAPI(title="ServiceDesk Ledger", version="0.2.0", lifespan=ciclo_de_vida)
erros.registrar(app)
app.include_router(painel.router)
app.include_router(cobranca.router)
app.include_router(paginas.router)
app.mount("/estatico", StaticFiles(directory=paginas.PASTA_WEB / "estatico"), name="estatico")


@app.get("/saude")
def saude(resposta: Response) -> dict[str, object]:
    """Diz se a aplicação subiu e se ela alcança o banco.

    Responde 503 quando o banco não responde: um health check que devolve 200
    com o banco fora não serve para nada.
    """
    config = obter_config()
    banco_ok = banco_responde(config.dsn)
    if not banco_ok:
        resposta.status_code = 503
    return {"status": "ok" if banco_ok else "degradado", "banco": banco_ok}
