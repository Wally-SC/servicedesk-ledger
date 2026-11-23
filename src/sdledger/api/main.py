"""Aplicação FastAPI."""

from __future__ import annotations

from fastapi import FastAPI, Response

from sdledger.infrastructure.config import obter_config
from sdledger.infrastructure.db.conexao import banco_responde

app = FastAPI(title="ServiceDesk Ledger", version="0.1.0")


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
