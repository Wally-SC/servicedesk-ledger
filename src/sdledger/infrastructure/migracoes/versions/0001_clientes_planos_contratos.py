"""Clientes, planos e contratos com vigência.

Revisão: 0001
Revisão anterior: nenhuma
"""

from __future__ import annotations

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: None = None
depends_on: None = None


def upgrade() -> None:
    # btree_gist permite misturar igualdade (cliente_id) com sobreposição de
    # intervalo (vigencia) na mesma constraint de exclusão.
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    op.execute("""
        CREATE TABLE cliente (
            id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            nome      text NOT NULL,
            documento text NOT NULL UNIQUE,
            criado_em timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT cliente_nome_nao_vazio CHECK (length(btrim(nome)) > 0)
        )
    """)

    # Dinheiro em centavos inteiros: ponto flutuante não é tipo para dinheiro, e
    # inteiro evita a discussão de arredondamento no meio do faturamento.
    op.execute("""
        CREATE TABLE plano (
            id                            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            nome                          text NOT NULL UNIQUE,
            franquia_minutos              integer NOT NULL,
            mensalidade_centavos          integer NOT NULL,
            preco_hora_excedente_centavos integer NOT NULL,
            CONSTRAINT plano_franquia_positiva
                CHECK (franquia_minutos > 0),
            CONSTRAINT plano_mensalidade_nao_negativa
                CHECK (mensalidade_centavos >= 0),
            CONSTRAINT plano_excedente_nao_negativo
                CHECK (preco_hora_excedente_centavos >= 0)
        )
    """)

    # O contrato liga cliente e plano por um período. A constraint de exclusão é
    # o que impede dois contratos do mesmo cliente valendo no mesmo dia — sem
    # ela, "qual SLA vale para este chamado?" passa a ter duas respostas.
    op.execute("""
        CREATE TABLE contrato (
            id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            cliente_id bigint NOT NULL REFERENCES cliente(id) ON DELETE RESTRICT,
            plano_id   bigint NOT NULL REFERENCES plano(id) ON DELETE RESTRICT,
            vigencia   daterange NOT NULL,
            CONSTRAINT contrato_vigencia_nao_vazia
                CHECK (NOT isempty(vigencia)),
            CONSTRAINT contrato_sem_sobreposicao
                EXCLUDE USING gist (cliente_id WITH =, vigencia WITH &&)
        )
    """)

    op.execute("CREATE INDEX contrato_por_plano ON contrato (plano_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS contrato")
    op.execute("DROP TABLE IF EXISTS plano")
    op.execute("DROP TABLE IF EXISTS cliente")
