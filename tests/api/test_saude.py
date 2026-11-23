"""A rota de saúde reflete o estado do banco, e não só o da aplicação."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from sdledger.api import main
from sdledger.api.main import app

cliente = TestClient(app)


def test_responde_200_quando_o_banco_responde(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "banco_responde", lambda _dsn: True)

    resposta = cliente.get("/saude")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "banco": True}


def test_responde_503_quando_o_banco_nao_responde(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "banco_responde", lambda _dsn: False)

    resposta = cliente.get("/saude")

    assert resposta.status_code == 503
    assert resposta.json() == {"status": "degradado", "banco": False}
