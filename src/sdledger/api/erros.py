"""Tradução de erro para HTTP.

Erro de domínio é regra de negócio violada: vira 422 com a mensagem da regra.
Qualquer outra exceção continua sendo 500, porque é defeito de programa e não
deve ser mascarada como erro do cliente.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from sdledger.domain.comum.erros import ErroDeDominio


def registrar(app: FastAPI) -> None:
    @app.exception_handler(ErroDeDominio)
    async def _erro_de_dominio(_: Request, erro: Exception) -> JSONResponse:
        return JSONResponse(status_code=422, content={"erro": str(erro)})
