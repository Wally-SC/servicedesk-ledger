"""Relógio do sistema, no fuso da análise."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

FUSO_DA_ANALISE = timezone(timedelta(hours=-3))


class RelogioDoSistema:
    """Implementação real da porta Relogio."""

    def agora(self) -> datetime:
        return datetime.now(FUSO_DA_ANALISE)
