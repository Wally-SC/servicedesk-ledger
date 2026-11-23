"""Protocolo de medição contra PostgreSQL real, com a massa pequena."""

from __future__ import annotations

from datetime import date

import psycopg
import pytest

from sdledger.infrastructure.laboratorio import medicao
from sdledger.infrastructure.laboratorio.catalogo import obter
from sdledger.infrastructure.massa.gerador import gerar
from sdledger.infrastructure.massa.perfis import PEQUENO

pytestmark = pytest.mark.integracao

EXPERIMENTO = obter("historico_do_cliente")


def _indice_existe(conexao: psycopg.Connection, nome: str) -> bool:
    linha = conexao.execute(
        "SELECT count(*) FROM pg_indexes WHERE indexname = %s", (nome,)
    ).fetchone()
    return linha is not None and linha[0] > 0


@pytest.fixture
def massa(conexao: psycopg.Connection) -> psycopg.Connection:
    gerar(conexao, PEQUENO, semente=42, fim=date(2026, 11, 23))
    return conexao


def test_compara_e_devolve_o_banco_como_achou(massa: psycopg.Connection) -> None:
    assert EXPERIMENTO is not None

    resultado = medicao.comparar(massa, EXPERIMENTO, repeticoes=3)

    assert len(resultado.sem_indice.tempos_ms) == 3
    assert resultado.sem_indice.mediana_ms > 0 and resultado.com_indice.mediana_ms > 0
    assert "mediana de 3" in resultado.ambiente
    assert not _indice_existe(massa, EXPERIMENTO.indice)


def test_remove_o_indice_mesmo_se_a_medicao_falhar(
    massa: psycopg.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """O laboratório não pode deixar índice esquecido no banco depois de um erro."""
    assert EXPERIMENTO is not None
    original = medicao.medir
    chamadas = {"n": 0}

    def medir_que_falha_na_segunda(*args: object, **kwargs: object) -> medicao.Medicao:
        chamadas["n"] += 1
        if chamadas["n"] == 2:
            raise RuntimeError("falha simulada durante a medição com índice")
        return original(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(medicao, "medir", medir_que_falha_na_segunda)

    with pytest.raises(RuntimeError):
        medicao.comparar(massa, EXPERIMENTO, repeticoes=1)

    assert not _indice_existe(massa, EXPERIMENTO.indice)


def test_parametros_saem_da_propria_massa(massa: psycopg.Connection) -> None:
    valores = medicao.parametros(massa)

    assert valores["fim"] > valores["inicio"]  # type: ignore[operator]
    assert isinstance(valores["cliente_id"], int)
