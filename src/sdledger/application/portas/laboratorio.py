"""Porta do registro de execuções do laboratório."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol


@dataclass(frozen=True)
class ExecucaoDoLaboratorio:
    id: int
    experimento: str
    estado: str
    solicitada_em: datetime
    iniciada_em: datetime | None
    concluida_em: datetime | None
    repeticoes: int | None
    sem_indice_ms: float | None
    com_indice_ms: float | None
    plano_sem_indice: list[dict[str, Any]] | None
    plano_com_indice: list[dict[str, Any]] | None
    ambiente: str | None
    erro: str | None


class RepositorioDeExecucoes(Protocol):
    def em_andamento(self) -> ExecucaoDoLaboratorio | None: ...

    def solicitar(self, experimento: str, repeticoes: int) -> ExecucaoDoLaboratorio: ...

    def obter(self, execucao_id: int) -> ExecucaoDoLaboratorio | None: ...

    def ultimas_por_experimento(self) -> dict[str, ExecucaoDoLaboratorio]: ...
