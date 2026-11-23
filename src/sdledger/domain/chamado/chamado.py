"""Entidade Chamado: o ciclo de vida e o que ele registra.

A entidade acumula os eventos que a transição produziu. Quem persiste é o caso
de uso: o domínio não conhece banco.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from sdledger.domain.chamado.estado import Estado, permite
from sdledger.domain.chamado.prioridade import Prioridade
from sdledger.domain.comum.erros import TransicaoInvalida, ValorInvalido


@dataclass(frozen=True)
class Evento:
    """Algo que aconteceu na linha do tempo do chamado."""

    tipo: str
    ocorrido_em: datetime
    autor_agente_id: int | None = None


@dataclass
class Chamado:
    """Chamado de suporte."""

    cliente_id: int
    prioridade: Prioridade
    assunto: str
    aberto_em: datetime
    id: int | None = None
    responsavel_id: int | None = None
    estado: Estado = Estado.ABERTO
    primeira_resposta_em: datetime | None = None
    resolvido_em: datetime | None = None
    eventos: list[Evento] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.assunto.strip():
            raise ValorInvalido("o chamado precisa de assunto")

    @classmethod
    def abrir(
        cls,
        cliente_id: int,
        prioridade: Prioridade,
        assunto: str,
        aberto_em: datetime,
    ) -> Chamado:
        chamado = cls(
            cliente_id=cliente_id,
            prioridade=prioridade,
            assunto=assunto,
            aberto_em=aberto_em,
        )
        chamado.eventos.append(Evento("abertura", aberto_em))
        return chamado

    def _ir_para(self, destino: Estado, quando: datetime) -> None:
        if quando < self.aberto_em:
            raise ValorInvalido("um evento não pode acontecer antes da abertura")
        if not permite(self.estado, destino):
            raise TransicaoInvalida(f"não é possível ir de {self.estado} para {destino}")
        self.estado = destino

    def registrar_resposta(self, quando: datetime, agente_id: int) -> None:
        """Primeira resposta pública de um agente.

        Só a primeira grava `primeira_resposta_em`: a métrica é primeira
        resposta, e sobrescrever a cada resposta apagaria o atraso real.
        """
        self._ir_para(Estado.EM_ATENDIMENTO, quando)
        if self.primeira_resposta_em is None:
            self.primeira_resposta_em = quando
        self.responsavel_id = agente_id
        self.eventos.append(Evento("resposta_publica", quando, agente_id))

    def aguardar_cliente(self, quando: datetime) -> None:
        self._ir_para(Estado.AGUARDANDO_CLIENTE, quando)
        self.eventos.append(Evento("mudanca_estado", quando))

    def retomar(self, quando: datetime) -> None:
        self._ir_para(Estado.EM_ATENDIMENTO, quando)
        self.eventos.append(Evento("mudanca_estado", quando))

    def resolver(self, quando: datetime, agente_id: int) -> None:
        self._ir_para(Estado.RESOLVIDO, quando)
        self.resolvido_em = quando
        self.eventos.append(Evento("resolucao", quando, agente_id))

    def reabrir(self, quando: datetime) -> None:
        """Reabrir limpa a resolução.

        O chamado volta a contar como aberto, e o tempo de resolução passa a ser
        medido até a próxima resolução (docs/metricas.md).
        """
        self._ir_para(Estado.ABERTO, quando)
        self.resolvido_em = None
        self.eventos.append(Evento("reabertura", quando))

    def fechar(self, quando: datetime) -> None:
        self._ir_para(Estado.FECHADO, quando)
        self.eventos.append(Evento("mudanca_estado", quando))
