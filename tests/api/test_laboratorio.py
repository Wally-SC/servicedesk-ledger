"""Rotas do laboratório: token, interruptor e execução em segundo plano."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from sdledger.api import dependencias
from sdledger.api.main import app
from sdledger.application.portas.laboratorio import ExecucaoDoLaboratorio
from sdledger.infrastructure.config import obter_config

PLANO = [
    {
        "Plan": {
            "Node Type": "Seq Scan",
            "Relation Name": "chamado",
            "Actual Total Time": 18.0,
            "Actual Rows": 4,
            "Actual Loops": 1,
        },
        "Execution Time": 18.2,
    }
]


class RepositorioFalso:
    def __init__(self) -> None:
        self.execucoes: list[ExecucaoDoLaboratorio] = []

    def em_andamento(self) -> ExecucaoDoLaboratorio | None:
        return next((e for e in self.execucoes if e.estado == "pendente"), None)

    def solicitar(self, experimento: str, repeticoes: int) -> ExecucaoDoLaboratorio:
        execucao = ExecucaoDoLaboratorio(
            len(self.execucoes) + 1,
            experimento,
            "pendente",
            datetime.now(UTC),
            None,
            None,
            repeticoes,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        self.execucoes.append(execucao)
        return execucao

    def obter(self, execucao_id: int) -> ExecucaoDoLaboratorio | None:
        if execucao_id != 99:
            return None
        return ExecucaoDoLaboratorio(
            99,
            "backlog_em_aberto",
            "concluida",
            datetime.now(UTC),
            None,
            None,
            5,
            18.2,
            0.5,
            PLANO,
            PLANO,
            "PostgreSQL 16",
            None,
        )

    def ultimas_por_experimento(self) -> dict[str, ExecucaoDoLaboratorio]:
        return {}


@pytest.fixture
def chamadas() -> list[tuple[str, int]]:
    return []


@pytest.fixture
def laboratorio(
    monkeypatch: pytest.MonkeyPatch, chamadas: list[tuple[str, int]]
) -> Iterator[TestClient]:
    monkeypatch.setenv("LAB_TOKEN", "segredo-de-teste")
    monkeypatch.setenv("LAB_HABILITADO", "true")
    obter_config.cache_clear()
    repositorio = RepositorioFalso()
    app.dependency_overrides[dependencias.obter_repositorio_de_execucoes] = lambda: repositorio
    app.dependency_overrides[dependencias.obter_dsn_do_laboratorio] = lambda: "dsn-falso"
    app.dependency_overrides[dependencias.obter_executor_de_medicao] = lambda: (
        lambda dsn, execucao_id: chamadas.append((dsn, execucao_id))
    )
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        obter_config.cache_clear()


def test_lista_o_catalogo_com_o_sql(laboratorio: TestClient) -> None:
    corpo = laboratorio.get("/api/laboratorio/experimentos").json()

    nomes = [e["nome"] for e in corpo]
    assert "historico_do_cliente" in nomes
    assert all(e["ddl"].lstrip().startswith("--") for e in corpo)


def test_medicao_sem_token_e_recusada(laboratorio: TestClient, chamadas: list) -> None:
    resposta = laboratorio.post(
        "/api/laboratorio/medicoes", json={"experimento": "backlog_em_aberto"}
    )

    assert resposta.status_code == 401
    assert chamadas == []


def test_medicao_com_token_e_aceita_e_agendada(laboratorio: TestClient, chamadas: list) -> None:
    resposta = laboratorio.post(
        "/api/laboratorio/medicoes",
        json={"experimento": "backlog_em_aberto", "repeticoes": 3},
        headers={"X-Lab-Token": "segredo-de-teste"},
    )

    assert resposta.status_code == 202
    assert resposta.json()["estado"] == "pendente"
    assert chamadas == [("dsn-falso", 1)]


def test_experimento_desconhecido_vira_404(laboratorio: TestClient) -> None:
    resposta = laboratorio.post(
        "/api/laboratorio/medicoes",
        json={"experimento": "DROP TABLE chamado"},
        headers={"X-Lab-Token": "segredo-de-teste"},
    )

    assert resposta.status_code == 404


def test_segunda_medicao_vira_409(laboratorio: TestClient) -> None:
    cabecalho = {"X-Lab-Token": "segredo-de-teste"}
    pedido = {"experimento": "backlog_em_aberto"}
    laboratorio.post("/api/laboratorio/medicoes", json=pedido, headers=cabecalho)

    resposta = laboratorio.post("/api/laboratorio/medicoes", json=pedido, headers=cabecalho)

    assert resposta.status_code == 409


def test_laboratorio_desligado_recusa_mesmo_com_token(
    laboratorio: TestClient, monkeypatch: pytest.MonkeyPatch, chamadas: list
) -> None:
    monkeypatch.setenv("LAB_HABILITADO", "false")
    obter_config.cache_clear()

    resposta = laboratorio.post(
        "/api/laboratorio/medicoes",
        json={"experimento": "backlog_em_aberto"},
        headers={"X-Lab-Token": "segredo-de-teste"},
    )

    assert resposta.status_code == 403
    assert chamadas == []


def test_medicao_concluida_devolve_os_planos_resumidos(laboratorio: TestClient) -> None:
    corpo = laboratorio.get("/api/laboratorio/medicoes/99").json()

    assert corpo["plano_sem_indice"][0]["operacao"] == "Seq Scan"
    assert corpo["plano_sem_indice"][0]["detalhe"] == "em chamado"


def test_medicao_inexistente_vira_404(laboratorio: TestClient) -> None:
    assert laboratorio.get("/api/laboratorio/medicoes/1").status_code == 404
