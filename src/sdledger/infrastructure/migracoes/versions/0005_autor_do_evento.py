"""Corrige a regra de autor do evento de chamado.

Revisão: 0005
Revisão anterior: 0004
"""

from __future__ import annotations

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: None = None
depends_on: None = None


def upgrade() -> None:
    # A regra da 0002 exigia autor apenas para resposta pública e nota interna,
    # e proibia autor em qualquer outro tipo. Isso recusa um evento de resolução,
    # que é feito por um agente e tem autor. O defeito só apareceu quando a massa
    # fictícia tentou gravar a linha do tempo completa de um chamado.
    #
    # O que importa para as métricas continua garantido: mensagem do cliente
    # nunca tem autor agente, e resposta pública e nota interna sempre têm.
    op.execute("ALTER TABLE chamado_evento DROP CONSTRAINT evento_de_agente_tem_autor")
    op.execute("""
        ALTER TABLE chamado_evento ADD CONSTRAINT evento_autor_coerente CHECK (
            CASE tipo
                WHEN 'mensagem_cliente' THEN autor_agente_id IS NULL
                WHEN 'resposta_publica' THEN autor_agente_id IS NOT NULL
                WHEN 'nota_interna'     THEN autor_agente_id IS NOT NULL
                ELSE true
            END
        )
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE chamado_evento DROP CONSTRAINT evento_autor_coerente")
    op.execute("""
        ALTER TABLE chamado_evento ADD CONSTRAINT evento_de_agente_tem_autor CHECK (
            (tipo IN ('resposta_publica', 'nota_interna')) = (autor_agente_id IS NOT NULL)
        )
    """)
