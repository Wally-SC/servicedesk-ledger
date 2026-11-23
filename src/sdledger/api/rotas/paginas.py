"""Páginas servidas pelo próprio projeto.

As páginas são casca: o conteúdo vem da API pelo navegador. Assim a mesma rota
que a tela usa é a que os testes e qualquer outro cliente usam.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import sdledger.web

PASTA_WEB = Path(sdledger.web.__file__).parent
TEMPLATES = Jinja2Templates(directory=str(PASTA_WEB / "templates"))

router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def painel(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(request, "painel.html", {"pagina": "painel"})


@router.get("/cobranca", response_class=HTMLResponse)
def cobranca(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(request, "cobranca.html", {"pagina": "cobranca"})


@router.get("/laboratorio", response_class=HTMLResponse)
def laboratorio(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(request, "laboratorio.html", {"pagina": "laboratorio"})
