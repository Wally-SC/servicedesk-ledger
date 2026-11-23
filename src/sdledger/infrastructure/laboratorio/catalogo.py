"""Catálogo de experimentos do laboratório.

Só roda o que está declarado aqui. A tela escolhe um experimento pelo nome e
nunca envia SQL: um botão que executa DDL a partir de texto vindo do navegador
seria uma porta aberta no banco (decisão D12).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Experimento:
    nome: str
    titulo: str
    tabela: str
    indice: str

    @property
    def consulta_sql(self) -> str:
        return f"laboratorio/experimentos/{self.nome}.sql"

    @property
    def indice_sql(self) -> str:
        return f"laboratorio/indices/{self.nome}.sql"


EXPERIMENTOS: tuple[Experimento, ...] = (
    Experimento(
        "resolvidos_na_janela",
        "Chamados entregues na janela",
        "chamado",
        "lab_chamado_resolvido_em",
    ),
    Experimento(
        "backlog_em_aberto",
        "Backlog em aberto, com índice parcial",
        "chamado",
        "lab_chamado_em_aberto",
    ),
    Experimento(
        "historico_do_cliente",
        "Histórico recente do maior cliente",
        "chamado",
        "lab_chamado_cliente_abertura",
    ),
    Experimento(
        "respostas_na_janela",
        "Respostas públicas por dia",
        "chamado_evento",
        "lab_evento_resposta_publica",
    ),
    Experimento(
        "consumo_do_mes",
        "Consumo de horas do mês, por cliente",
        "apontamento",
        "lab_apontamento_data",
    ),
)

POR_NOME = {experimento.nome: experimento for experimento in EXPERIMENTOS}


def obter(nome: str) -> Experimento | None:
    return POR_NOME.get(nome)
