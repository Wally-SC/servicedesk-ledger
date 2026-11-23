"""Erros de domínio.

Erro de domínio é regra de negócio violada, não defeito de programa. A API
traduz estes erros para 4xx; qualquer outra exceção é 500.
"""

from __future__ import annotations


class ErroDeDominio(Exception):
    """Base de toda regra de negócio violada."""


class TransicaoInvalida(ErroDeDominio):
    """Mudança de estado que o ciclo de vida do chamado não permite."""


class ValorInvalido(ErroDeDominio):
    """Valor que não existe no domínio, como duração negativa."""
