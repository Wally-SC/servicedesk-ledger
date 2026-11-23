"""As páginas sobem e os estáticos são servidos pelo próprio projeto."""

from __future__ import annotations

from fastapi.testclient import TestClient

from sdledger.api.main import app

cliente = TestClient(app)


def test_painel_e_servido() -> None:
    resposta = cliente.get("/")

    assert resposta.status_code == 200
    assert "Painel de SLA e backlog" in resposta.text
    assert "/estatico/vendor/chart.umd.js" in resposta.text


def test_estaticos_sao_servidos() -> None:
    for caminho in ("/estatico/estilo.css", "/estatico/painel.js", "/estatico/vendor/chart.umd.js"):
        assert cliente.get(caminho).status_code == 200, caminho


def test_paginas_nao_aparecem_na_documentacao_da_api() -> None:
    caminhos = cliente.get("/openapi.json").json()["paths"]
    assert "/" not in caminhos


def test_cobranca_e_servida() -> None:
    resposta = cliente.get("/cobranca")

    assert resposta.status_code == 200
    assert "Cobrança recorrente" in resposta.text


def test_laboratorio_e_servido() -> None:
    resposta = cliente.get("/laboratorio")

    assert resposta.status_code == 200
    assert "Laboratório de índices" in resposta.text
    assert cliente.get("/estatico/laboratorio.js").status_code == 200
