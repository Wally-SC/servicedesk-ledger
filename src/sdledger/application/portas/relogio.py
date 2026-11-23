"""Porta do relógio.

O domínio recebe o instante de fora. Caso de uso que chama `datetime.now()` por
dentro não tem como ser testado em borda de horário.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class Relogio(Protocol):
    def agora(self) -> datetime: ...
