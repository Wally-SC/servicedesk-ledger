"""Chamados, eventos e períodos de estado.

Revisão: 0002
Revisão anterior: 0001
"""

from __future__ import annotations

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: None = None
depends_on: None = None


def upgrade() -> None:
    op.execute("CREATE TYPE prioridade AS ENUM ('baixa', 'media', 'alta', 'critica')")
    op.execute("""
        CREATE TYPE estado_chamado AS ENUM (
            'aberto', 'em_atendimento', 'aguardando_cliente', 'resolvido', 'fechado'
        )
    """)
    # O tipo do evento é o que define o que conta como primeira resposta:
    # nota interna e mensagem do cliente não contam (docs/metricas.md).
    op.execute("""
        CREATE TYPE tipo_evento AS ENUM (
            'abertura', 'resposta_publica', 'nota_interna',
            'mensagem_cliente', 'mudanca_estado', 'resolucao', 'reabertura'
        )
    """)

    op.execute("""
        CREATE TABLE agente (
            id    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            nome  text NOT NULL,
            ativo boolean NOT NULL DEFAULT true,
            CONSTRAINT agente_nome_nao_vazio CHECK (length(btrim(nome)) > 0)
        )
    """)

    # As colunas primeira_resposta_em e resolvido_em são derivadas dos eventos e
    # mantidas pelo caso de uso (decisão D05). Os eventos continuam sendo a
    # fonte da verdade; estas colunas existem para o painel não reconstruir a
    # linha do tempo de centenas de milhares de chamados a cada consulta.
    op.execute("""
        CREATE TABLE chamado (
            id                   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            cliente_id           bigint NOT NULL REFERENCES cliente(id) ON DELETE RESTRICT,
            responsavel_id       bigint REFERENCES agente(id) ON DELETE SET NULL,
            prioridade           prioridade NOT NULL,
            estado               estado_chamado NOT NULL DEFAULT 'aberto',
            assunto              text NOT NULL,
            aberto_em            timestamptz NOT NULL,
            primeira_resposta_em timestamptz,
            resolvido_em         timestamptz,
            CONSTRAINT chamado_assunto_nao_vazio
                CHECK (length(btrim(assunto)) > 0),
            CONSTRAINT chamado_resposta_apos_abertura
                CHECK (primeira_resposta_em IS NULL OR primeira_resposta_em >= aberto_em),
            CONSTRAINT chamado_resolucao_apos_abertura
                CHECK (resolvido_em IS NULL OR resolvido_em >= aberto_em),
            CONSTRAINT chamado_resolvido_tem_data
                CHECK ((estado IN ('resolvido', 'fechado')) = (resolvido_em IS NOT NULL))
        )
    """)

    op.execute("""
        CREATE TABLE chamado_evento (
            id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            chamado_id      bigint NOT NULL REFERENCES chamado(id) ON DELETE CASCADE,
            tipo            tipo_evento NOT NULL,
            autor_agente_id bigint REFERENCES agente(id) ON DELETE SET NULL,
            ocorrido_em     timestamptz NOT NULL,
            CONSTRAINT evento_de_agente_tem_autor
                CHECK (
                    (tipo IN ('resposta_publica', 'nota_interna'))
                    = (autor_agente_id IS NOT NULL)
                )
        )
    """)

    # Períodos de estado existem desde já porque o backlog por idade depende
    # deles e porque o desconto das pausas no relógio de SLA (decisão D07) entra
    # numa fatia posterior — e retroagir isso seria reescrever migração.
    op.execute("""
        CREATE TABLE chamado_periodo_estado (
            id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            chamado_id bigint NOT NULL REFERENCES chamado(id) ON DELETE CASCADE,
            estado     estado_chamado NOT NULL,
            periodo    tstzrange NOT NULL,
            CONSTRAINT periodo_nao_vazio
                CHECK (NOT isempty(periodo)),
            CONSTRAINT periodo_sem_sobreposicao
                EXCLUDE USING gist (chamado_id WITH =, periodo WITH &&)
        )
    """)

    # Só os índices que a integridade e a navegação por chamado exigem. Os
    # índices dos caminhos analíticos ficam de fora de propósito: eles são o
    # objeto do laboratório, e criá-los agora tiraria o antes/depois da medição.
    op.execute("""
        CREATE INDEX chamado_evento_por_chamado
            ON chamado_evento (chamado_id, ocorrido_em)
    """)
    op.execute("CREATE INDEX chamado_por_cliente ON chamado (cliente_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS chamado_periodo_estado")
    op.execute("DROP TABLE IF EXISTS chamado_evento")
    op.execute("DROP TABLE IF EXISTS chamado")
    op.execute("DROP TABLE IF EXISTS agente")
    op.execute("DROP TYPE IF EXISTS tipo_evento")
    op.execute("DROP TYPE IF EXISTS estado_chamado")
    op.execute("DROP TYPE IF EXISTS prioridade")
