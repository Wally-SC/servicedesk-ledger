"""Tradução de erro para HTTP.

Erro de domínio é regra de negócio violada: vira 422 com a mensagem da regra.
Qualquer outra exceção continua sendo 500, porque é defeito de programa e não
deve ser mascarada como erro do cliente.
"""

from __future__ import annotations

import psycopg
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from sdledger.domain.comum.erros import Conflito, ErroDeDominio, NaoEncontrado

STATUS_POR_ERRO: tuple[tuple[type[ErroDeDominio], int], ...] = (
    (NaoEncontrado, 404),
    (Conflito, 409),
)


def registrar(app: FastAPI) -> None:
    @app.exception_handler(ErroDeDominio)
    async def _erro_de_dominio(_: Request, erro: Exception) -> JSONResponse:
        codigo = next((c for tipo, c in STATUS_POR_ERRO if isinstance(erro, tipo)), 422)
        return JSONResponse(status_code=codigo, content={"erro": str(erro)})

    @app.exception_handler(psycopg.errors.UndefinedTable)
    async def _banco_sem_esquema(_: Request, erro: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"erro": "banco sem esquema: rode make migrar ou make laboratorio-preparar"},
        )
