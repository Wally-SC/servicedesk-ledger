"""Registro e execução das medições do laboratório.

A execução roda fora da requisição HTTP: criar um índice em 300 mil linhas leva
mais do que uma requisição deveria esperar. A requisição só registra o pedido,
e a tela acompanha o estado pelo registro.
"""

from __future__ import annotations

import psycopg
from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from sdledger.application.portas.laboratorio import ExecucaoDoLaboratorio
from sdledger.infrastructure.laboratorio.catalogo import obter
from sdledger.infrastructure.laboratorio.medicao import comparar

# Número arbitrário e fixo: identifica a trava do laboratório no banco.
TRAVA_DO_LABORATORIO = 4_240_001

COLUNAS = """id, experimento, estado, solicitada_em, iniciada_em, concluida_em, repeticoes,
             sem_indice_ms, com_indice_ms, plano_sem_indice, plano_com_indice, ambiente, erro"""


class RepositorioDeExecucoesEmPostgres:
    def __init__(self, conexao: psycopg.Connection) -> None:
        self._conexao = conexao

    def _uma(self, consulta: str, valores: tuple[object, ...] = ()) -> ExecucaoDoLaboratorio | None:
        with self._conexao.cursor(row_factory=class_row(ExecucaoDoLaboratorio)) as cursor:
            cursor.execute(consulta, valores)
            return cursor.fetchone()

    def em_andamento(self) -> ExecucaoDoLaboratorio | None:
        return self._uma(
            f"""
            SELECT {COLUNAS} FROM laboratorio_execucao
            WHERE estado IN ('pendente', 'rodando') ORDER BY id DESC LIMIT 1
            """
        )

    def solicitar(self, experimento: str, repeticoes: int) -> ExecucaoDoLaboratorio:
        execucao = self._uma(
            f"""
            INSERT INTO laboratorio_execucao (experimento, repeticoes)
            VALUES (%s, %s) RETURNING {COLUNAS}
            """,
            (experimento, repeticoes),
        )
        assert execucao is not None
        return execucao

    def obter(self, execucao_id: int) -> ExecucaoDoLaboratorio | None:
        return self._uma(
            f"SELECT {COLUNAS} FROM laboratorio_execucao WHERE id = %s", (execucao_id,)
        )

    def ultimas_por_experimento(self) -> dict[str, ExecucaoDoLaboratorio]:
        with self._conexao.cursor(row_factory=class_row(ExecucaoDoLaboratorio)) as cursor:
            cursor.execute(
                f"""
                SELECT DISTINCT ON (experimento) {COLUNAS}
                FROM laboratorio_execucao
                ORDER BY experimento, id DESC
                """
            )
            return {execucao.experimento: execucao for execucao in cursor.fetchall()}


def processar(conexao: psycopg.Connection, execucao_id: int) -> None:
    """Executa uma medição registrada, atualizando o registro a cada passo."""
    travou = conexao.execute("SELECT pg_try_advisory_lock(%s)", (TRAVA_DO_LABORATORIO,)).fetchone()
    if travou is None or not travou[0]:
        _falhar(conexao, execucao_id, "outra medição está rodando neste banco")
        return
    try:
        linha = conexao.execute(
            "SELECT experimento, repeticoes FROM laboratorio_execucao WHERE id = %s",
            (execucao_id,),
        ).fetchone()
        if linha is None:
            return
        experimento = obter(linha[0])
        if experimento is None:
            _falhar(conexao, execucao_id, f"experimento fora do catálogo: {linha[0]}")
            return
        conexao.execute(
            "UPDATE laboratorio_execucao SET estado = 'rodando', iniciada_em = now() WHERE id = %s",
            (execucao_id,),
        )
        resultado = comparar(conexao, experimento, linha[1] or 5)
        conexao.execute(
            """
            UPDATE laboratorio_execucao
            SET estado = 'concluida', concluida_em = now(),
                sem_indice_ms = %s, com_indice_ms = %s,
                plano_sem_indice = %s, plano_com_indice = %s, ambiente = %s
            WHERE id = %s
            """,
            (
                resultado.sem_indice.mediana_ms,
                resultado.com_indice.mediana_ms,
                Jsonb(resultado.sem_indice.plano),
                Jsonb(resultado.com_indice.plano),
                resultado.ambiente,
                execucao_id,
            ),
        )
    except psycopg.Error as erro:
        _falhar(conexao, execucao_id, str(erro).strip() or erro.__class__.__name__)
    finally:
        conexao.execute("SELECT pg_advisory_unlock(%s)", (TRAVA_DO_LABORATORIO,))


def _falhar(conexao: psycopg.Connection, execucao_id: int, motivo: str) -> None:
    conexao.execute(
        """
        UPDATE laboratorio_execucao SET estado = 'falhou', concluida_em = now(), erro = %s
        WHERE id = %s
        """,
        (motivo, execucao_id),
    )


def executar_em_segundo_plano(dsn: str, execucao_id: int) -> None:
    """Ponto de entrada da tarefa em segundo plano: conexão própria, autocommit."""
    with psycopg.connect(dsn, autocommit=True) as conexao:
        processar(conexao, execucao_id)
