"""${message}

Revisão: ${up_revision}
Revisão anterior: ${down_revision | comma,n}
Criada em: ${create_date}
"""

from __future__ import annotations

from alembic import op

revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: None = None
depends_on: None = None


def upgrade() -> None:
    op.execute("""
    """)


def downgrade() -> None:
    op.execute("""
    """)
