"""Prioridade do chamado."""

from __future__ import annotations

from enum import StrEnum


class Prioridade(StrEnum):
    """Os mesmos valores do enum do banco."""

    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"
