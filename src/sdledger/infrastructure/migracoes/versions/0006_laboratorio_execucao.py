"""Registro das execuções do laboratório de índices.

Revisão: 0006
Revisão anterior: 0005
"""

from __future__ import annotations

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: None = None
depends_on: None = None


def upgrade() -> None:
    # Cada execução fica registrada com os dois planos, para o resultado poder
    # ser conferido depois e não só lido na tela no momento em que rodou.
    op.execute("""
        CREATE TABLE laboratorio_execucao (
            id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            experimento      text NOT NULL,
            estado           text NOT NULL DEFAULT 'pendente',
            solicitada_em    timestamptz NOT NULL DEFAULT now(),
            iniciada_em      timestamptz,
            concluida_em     timestamptz,
            repeticoes       integer,
            sem_indice_ms    double precision,
            com_indice_ms    double precision,
            plano_sem_indice jsonb,
            plano_com_indice jsonb,
            ambiente         text,
            erro             text,
            CONSTRAINT execucao_estado_valido
                CHECK (estado IN ('pendente', 'rodando', 'concluida', 'falhou')),
            CONSTRAINT execucao_concluida_tem_tempos
                CHECK (estado <> 'concluida'
                       OR (sem_indice_ms IS NOT NULL AND com_indice_ms IS NOT NULL)),
            CONSTRAINT execucao_falha_tem_motivo
                CHECK (estado <> 'falhou' OR erro IS NOT NULL)
        )
    """)
    op.execute("""
        CREATE INDEX laboratorio_execucao_recentes
            ON laboratorio_execucao (experimento, solicitada_em DESC)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS laboratorio_execucao")
