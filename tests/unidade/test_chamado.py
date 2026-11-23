"""Ciclo de vida do chamado."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from sdledger.domain.chamado.chamado import Chamado
from sdledger.domain.chamado.estado import Estado
from sdledger.domain.chamado.prioridade import Prioridade
from sdledger.domain.comum.erros import TransicaoInvalida, ValorInvalido

FUSO = timezone(timedelta(hours=-3))
ABERTURA = datetime(2026, 11, 23, 9, 0, tzinfo=FUSO)


def _chamado() -> Chamado:
    return Chamado.abrir(1, Prioridade.ALTA, "Impressora parada", ABERTURA)


def test_abrir_registra_evento_de_abertura() -> None:
    chamado = _chamado()

    assert chamado.estado is Estado.ABERTO
    assert [evento.tipo for evento in chamado.eventos] == ["abertura"]


def test_chamado_sem_assunto_nao_existe() -> None:
    with pytest.raises(ValorInvalido):
        Chamado.abrir(1, Prioridade.BAIXA, "   ", ABERTURA)


def test_primeira_resposta_nao_e_sobrescrita_pela_segunda() -> None:
    """A métrica é primeira resposta: sobrescrever apagaria o atraso real."""
    chamado = _chamado()
    primeira = ABERTURA + timedelta(minutes=30)
    chamado.registrar_resposta(primeira, agente_id=7)

    chamado.aguardar_cliente(primeira + timedelta(hours=1))
    chamado.retomar(primeira + timedelta(hours=2))

    assert chamado.primeira_resposta_em == primeira


def test_fluxo_completo_ate_fechar() -> None:
    chamado = _chamado()
    chamado.registrar_resposta(ABERTURA + timedelta(minutes=10), agente_id=7)
    chamado.resolver(ABERTURA + timedelta(hours=3), agente_id=7)
    chamado.fechar(ABERTURA + timedelta(days=1))

    assert chamado.estado is Estado.FECHADO
    assert chamado.resolvido_em == ABERTURA + timedelta(hours=3)
    assert [evento.tipo for evento in chamado.eventos] == [
        "abertura",
        "resposta_publica",
        "resolucao",
        "mudanca_estado",
    ]


def test_chamado_fechado_nao_aceita_mais_transicao() -> None:
    chamado = _chamado()
    chamado.resolver(ABERTURA + timedelta(hours=1), agente_id=7)
    chamado.fechar(ABERTURA + timedelta(hours=2))

    with pytest.raises(TransicaoInvalida):
        chamado.reabrir(ABERTURA + timedelta(hours=3))


def test_reabrir_limpa_a_resolucao() -> None:
    """O tempo passa a ser medido até a próxima resolução."""
    chamado = _chamado()
    chamado.resolver(ABERTURA + timedelta(hours=1), agente_id=7)
    chamado.reabrir(ABERTURA + timedelta(hours=5))

    assert chamado.estado is Estado.ABERTO
    assert chamado.resolvido_em is None


def test_nao_se_pode_aguardar_cliente_antes_de_atender() -> None:
    chamado = _chamado()

    with pytest.raises(TransicaoInvalida):
        chamado.aguardar_cliente(ABERTURA + timedelta(minutes=5))


def test_evento_antes_da_abertura_e_recusado() -> None:
    chamado = _chamado()

    with pytest.raises(ValorInvalido):
        chamado.registrar_resposta(ABERTURA - timedelta(minutes=1), agente_id=7)


def test_chamado_pode_ser_resolvido_sem_resposta() -> None:
    """Acontece, e o painel conta esses chamados à parte, fora do percentil."""
    chamado = _chamado()
    chamado.resolver(ABERTURA + timedelta(minutes=20), agente_id=7)

    assert chamado.estado is Estado.RESOLVIDO
    assert chamado.primeira_resposta_em is None
