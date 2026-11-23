"""Protocolo de medição do laboratório (ADR-0008).

Rodar a consulta duas vezes e comparar mede cache, não índice. O protocolo:

1. `statement_timeout` e `lock_timeout` na sessão, para o laboratório nunca
   segurar o banco por tempo indeterminado;
2. o índice candidato é removido e a tabela é analisada, para o "sem índice"
   começar de estatística fresca;
3. uma execução de aquecimento é descartada — os números são de cache quente,
   e isso é declarado, não escondido;
4. N execuções com `EXPLAIN (ANALYZE, BUFFERS)`; vale a mediana;
5. o índice é criado, a tabela é analisada de novo, e o passo 3 e 4 se repetem;
6. o índice é removido no fim, para a próxima medição partir do mesmo estado.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import psycopg
from psycopg import sql

from sdledger.infrastructure.db.sql import carregar
from sdledger.infrastructure.laboratorio.catalogo import Experimento
from sdledger.infrastructure.laboratorio.plano import tempo_de_execucao

REPETICOES_PADRAO = 5


@dataclass(frozen=True)
class Medicao:
    tempos_ms: tuple[float, ...]
    mediana_ms: float
    plano: list[dict[str, Any]]


@dataclass(frozen=True)
class Comparacao:
    experimento: str
    sem_indice: Medicao
    com_indice: Medicao
    ambiente: str

    @property
    def ganho(self) -> float:
        """Quantas vezes mais rápido ficou. Abaixo de 1, o índice piorou."""
        return self.sem_indice.mediana_ms / max(self.com_indice.mediana_ms, 0.001)


def configurar_sessao(conexao: psycopg.Connection) -> None:
    conexao.execute("SET statement_timeout = '120s'")
    conexao.execute("SET lock_timeout = '5s'")


def parametros(conexao: psycopg.Connection) -> dict[str, object]:
    """Parâmetros relativos à própria massa, calculados fora da medição.

    A janela termina no último chamado aberto, e não em "agora": assim a mesma
    massa dá a mesma janela em qualquer dia em que o laboratório rode.
    """
    linha = conexao.execute(
        """
        SELECT max(aberto_em),
               (SELECT cliente_id FROM chamado GROUP BY cliente_id
                ORDER BY count(*) DESC, cliente_id LIMIT 1)
        FROM chamado
        """
    ).fetchone()
    if linha is None or linha[0] is None:
        raise RuntimeError("o banco do laboratório não tem chamados: rode o preparo")
    fim, cliente_id = linha
    return {"inicio": fim - timedelta(days=30), "fim": fim, "cliente_id": cliente_id}


def explicar(
    conexao: psycopg.Connection, consulta: str, valores: dict[str, object]
) -> list[dict[str, Any]]:
    """EXPLAIN com os valores já interpolados, como uma pessoa rodaria no psql.

    O cursor do lado do cliente evita que o planejador veja parâmetros genéricos
    em vez dos valores, o que mudaria o plano medido.
    """
    with psycopg.ClientCursor(conexao) as cursor:
        cursor.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)\n" + consulta, valores)
        linha = cursor.fetchone()
    if linha is None:  # pragma: no cover - EXPLAIN sempre devolve uma linha
        raise RuntimeError("EXPLAIN não devolveu plano")
    plano: list[dict[str, Any]] = linha[0]
    return plano


def medir(
    conexao: psycopg.Connection,
    consulta: str,
    valores: dict[str, object],
    repeticoes: int = REPETICOES_PADRAO,
) -> Medicao:
    explicar(conexao, consulta, valores)  # aquecimento, descartado
    planos = sorted(
        (explicar(conexao, consulta, valores) for _ in range(repeticoes)),
        key=tempo_de_execucao,
    )
    tempos = tuple(tempo_de_execucao(plano) for plano in planos)
    return Medicao(
        tempos_ms=tempos,
        mediana_ms=statistics.median(tempos),
        plano=planos[len(planos) // 2],
    )


def _remover_indice(conexao: psycopg.Connection, experimento: Experimento) -> None:
    conexao.execute(sql.SQL("DROP INDEX IF EXISTS {}").format(sql.Identifier(experimento.indice)))


def _analisar(conexao: psycopg.Connection, experimento: Experimento) -> None:
    conexao.execute(sql.SQL("ANALYZE {}").format(sql.Identifier(experimento.tabela)))


def descrever_ambiente(conexao: psycopg.Connection, repeticoes: int) -> str:
    linha = conexao.execute("SHOW server_version").fetchone()
    versao = linha[0] if linha else "desconhecida"
    return (
        f"PostgreSQL {versao}; cache quente (1 execução de aquecimento descartada); "
        f"mediana de {repeticoes} execuções"
    )


def comparar(
    conexao: psycopg.Connection,
    experimento: Experimento,
    repeticoes: int = REPETICOES_PADRAO,
) -> Comparacao:
    """Mede a consulta sem e com o índice candidato, e devolve o banco como achou.

    Não faz commit: com conexão em autocommit, cada passo vale na hora; dentro de
    uma transação de teste, tudo é desfeito no fim.
    """
    configurar_sessao(conexao)
    valores = parametros(conexao)
    consulta = carregar(experimento.consulta_sql)

    _remover_indice(conexao, experimento)
    _analisar(conexao, experimento)
    sem = medir(conexao, consulta, valores, repeticoes)

    conexao.execute(carregar(experimento.indice_sql))
    _analisar(conexao, experimento)
    try:
        com = medir(conexao, consulta, valores, repeticoes)
    finally:
        _remover_indice(conexao, experimento)

    return Comparacao(
        experimento=experimento.nome,
        sem_indice=sem,
        com_indice=com,
        ambiente=descrever_ambiente(conexao, repeticoes),
    )
