"""Apontamentos, ciclos de faturamento, faturas e itens.

Revisão: 0004
Revisão anterior: 0003
"""

from __future__ import annotations

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: None = None
depends_on: None = None


def upgrade() -> None:
    # As horas que o chamado consome do plano. Minutos inteiros: o arredondamento
    # em blocos de 15 acontece no fechamento do ciclo, no domínio, e não aqui.
    op.execute("""
        CREATE TABLE apontamento (
            id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            chamado_id  bigint NOT NULL REFERENCES chamado(id) ON DELETE CASCADE,
            agente_id   bigint NOT NULL REFERENCES agente(id) ON DELETE RESTRICT,
            minutos     integer NOT NULL,
            apontado_em timestamptz NOT NULL,
            CONSTRAINT apontamento_minutos_positivos CHECK (minutos > 0)
        )
    """)
    op.execute("CREATE INDEX apontamento_por_chamado ON apontamento (chamado_id)")

    op.execute("CREATE TYPE estado_fatura AS ENUM ('aberta', 'emitida', 'paga', 'cancelada')")
    op.execute("CREATE TYPE tipo_item AS ENUM ('mensalidade', 'hora_excedente')")

    # Um ciclo por cliente e competência. A competência é sempre o primeiro dia
    # do mês, para não existirem duas representações do mesmo período.
    op.execute("""
        CREATE TABLE ciclo_faturamento (
            id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            cliente_id  bigint NOT NULL REFERENCES cliente(id) ON DELETE RESTRICT,
            competencia date NOT NULL,
            fechado_em  timestamptz,
            CONSTRAINT ciclo_competencia_e_primeiro_dia
                CHECK (competencia = date_trunc('month', competencia)::date),
            CONSTRAINT ciclo_unico_por_cliente_e_competencia
                UNIQUE (cliente_id, competencia)
        )
    """)

    # Os estados são amarrados por constraint: fatura paga sem data de pagamento
    # e fatura aberta com data de emissão não entram no banco.
    op.execute("""
        CREATE TABLE fatura (
            id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            ciclo_id       bigint NOT NULL UNIQUE
                               REFERENCES ciclo_faturamento(id) ON DELETE CASCADE,
            estado         estado_fatura NOT NULL DEFAULT 'aberta',
            emitida_em     timestamptz,
            vencimento     date,
            paga_em        timestamptz,
            total_centavos integer NOT NULL DEFAULT 0,
            CONSTRAINT fatura_total_nao_negativo
                CHECK (total_centavos >= 0),
            CONSTRAINT fatura_aberta_nao_tem_emissao
                CHECK (estado <> 'aberta' OR (emitida_em IS NULL AND paga_em IS NULL)),
            CONSTRAINT fatura_emitida_tem_vencimento
                CHECK (emitida_em IS NULL OR vencimento IS NOT NULL),
            CONSTRAINT fatura_paga_tem_data_e_emissao
                CHECK (estado <> 'paga' OR (paga_em IS NOT NULL AND emitida_em IS NOT NULL)),
            CONSTRAINT fatura_pagamento_so_se_paga
                CHECK (paga_em IS NULL OR estado = 'paga')
        )
    """)

    op.execute("""
        CREATE TABLE fatura_item (
            id                      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            fatura_id               bigint NOT NULL REFERENCES fatura(id) ON DELETE CASCADE,
            tipo                    tipo_item NOT NULL,
            descricao               text NOT NULL,
            quantidade              numeric(10, 2) NOT NULL,
            valor_unitario_centavos integer NOT NULL,
            valor_centavos          integer NOT NULL,
            CONSTRAINT item_quantidade_positiva CHECK (quantidade > 0),
            CONSTRAINT item_valores_nao_negativos
                CHECK (valor_unitario_centavos >= 0 AND valor_centavos >= 0)
        )
    """)
    op.execute("CREATE INDEX fatura_item_por_fatura ON fatura_item (fatura_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS fatura_item")
    op.execute("DROP TABLE IF EXISTS fatura")
    op.execute("DROP TABLE IF EXISTS ciclo_faturamento")
    op.execute("DROP TABLE IF EXISTS apontamento")
    op.execute("DROP TYPE IF EXISTS tipo_item")
    op.execute("DROP TYPE IF EXISTS estado_fatura")
