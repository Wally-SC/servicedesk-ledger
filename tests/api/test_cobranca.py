"""Rotas da cobrança."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient


def test_receita_usa_so_competencias_fechadas(cliente_cobranca: TestClient, cobranca_falsa) -> None:
    resposta = cliente_cobranca.get("/api/cobranca/receita", params={"meses": 3})

    assert resposta.status_code == 200
    assert resposta.json()[0]["receita_centavos"] == 200000
    assert cobranca_falsa.intervalos[-1] == (date(2026, 8, 1), date(2026, 11, 1))


def test_atraso_devolve_as_faixas(cliente_cobranca: TestClient) -> None:
    corpo = cliente_cobranca.get("/api/cobranca/atraso").json()

    assert corpo["total_centavos"] == 90000
    assert corpo["mais_de_90_dias_centavos"] == 50000


def test_serie_fora_do_limite_e_recusada(cliente_cobranca: TestClient) -> None:
    assert cliente_cobranca.get("/api/cobranca/churn", params={"meses": 0}).status_code == 422
    assert cliente_cobranca.get("/api/cobranca/churn", params={"meses": 37}).status_code == 422
