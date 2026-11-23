"""Rotas do painel: tradução de HTTP, não regra de negócio."""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient


def test_percentis_usa_a_janela_pedida(cliente: TestClient, painel_falso, agora: datetime) -> None:
    resposta = cliente.get("/api/painel/percentis", params={"dias": 7})

    assert resposta.status_code == 200
    assert resposta.json()["resolucao_p95"] == 2100.0
    janela = painel_falso.janelas[-1]
    assert janela.fim == agora
    assert janela.fim - janela.inicio == timedelta(days=7)


def test_janela_padrao_e_de_30_dias(cliente: TestClient, painel_falso) -> None:
    cliente.get("/api/painel/sla")

    janela = painel_falso.janelas[-1]
    assert janela.fim - janela.inicio == timedelta(days=30)


def test_janela_fora_do_limite_e_recusada(cliente: TestClient) -> None:
    assert cliente.get("/api/painel/percentis", params={"dias": 0}).status_code == 422
    assert cliente.get("/api/painel/percentis", params={"dias": 366}).status_code == 422


def test_backlog_devolve_as_faixas(cliente: TestClient) -> None:
    corpo = cliente.get("/api/painel/backlog").json()

    assert corpo == [
        {
            "prioridade": "critica",
            "total": 10,
            "ate_1_dia": 1,
            "de_1_a_3_dias": 2,
            "de_3_a_7_dias": 3,
            "mais_de_7_dias": 4,
            "idade_maxima_dias": 12.5,
        }
    ]


def test_tendencia_serializa_a_semana_como_data(cliente: TestClient) -> None:
    corpo = cliente.get("/api/painel/tendencia").json()

    assert corpo[0]["semana"] == "2026-11-09"
    assert corpo[0]["variacao_p95"] is None


def test_ranking_respeita_o_limite(cliente: TestClient) -> None:
    assert cliente.get("/api/painel/clientes", params={"limite": 51}).status_code == 422
    corpo = cliente.get("/api/painel/clientes", params={"limite": 1}).json()
    assert len(corpo) == 1 and corpo[0]["nome"] == "Cliente 0007"


def test_tendencia_usa_so_semanas_completas(cliente: TestClient, painel_falso) -> None:
    cliente.get("/api/painel/tendencia", params={"semanas": 4})

    janela = painel_falso.janelas[-1]
    assert janela.fim.weekday() == 0 and janela.fim.hour == 0
    assert janela.fim - janela.inicio == timedelta(weeks=4)
