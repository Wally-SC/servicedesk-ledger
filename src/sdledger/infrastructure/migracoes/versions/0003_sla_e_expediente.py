"""Política de SLA com vigência, calendário de expediente e minutos úteis.

Revisão: 0003
Revisão anterior: 0002
"""

from __future__ import annotations

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: None = None
depends_on: None = None

FUSO = "America/Sao_Paulo"


def upgrade() -> None:
    # O prazo varia por plano e por prioridade, e muda ao longo do tempo. Sem
    # vigência, um chamado aberto antes de o cliente trocar de plano passaria a
    # ser medido por um prazo que não valia naquele dia.
    op.execute("""
        CREATE TABLE politica_sla (
            id                              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            plano_id                        bigint NOT NULL REFERENCES plano(id) ON DELETE RESTRICT,
            prioridade                      prioridade NOT NULL,
            minutos_uteis_primeira_resposta integer NOT NULL,
            minutos_uteis_resolucao         integer NOT NULL,
            vigencia                        daterange NOT NULL,
            CONSTRAINT politica_prazos_positivos
                CHECK (minutos_uteis_primeira_resposta > 0 AND minutos_uteis_resolucao > 0),
            CONSTRAINT politica_resolucao_nao_menor_que_resposta
                CHECK (minutos_uteis_resolucao >= minutos_uteis_primeira_resposta),
            CONSTRAINT politica_vigencia_nao_vazia
                CHECK (NOT isempty(vigencia)),
            CONSTRAINT politica_sem_sobreposicao
                EXCLUDE USING gist (
                    plano_id WITH =, prioridade WITH =, vigencia WITH &&
                )
        )
    """)

    op.execute("""
        CREATE TABLE expediente (
            dia_da_semana smallint PRIMARY KEY,
            inicio        time NOT NULL,
            fim           time NOT NULL,
            CONSTRAINT expediente_dia_valido CHECK (dia_da_semana BETWEEN 0 AND 6),
            CONSTRAINT expediente_fim_depois_do_inicio CHECK (fim > inicio)
        )
    """)

    op.execute("""
        CREATE TABLE feriado (
            dia       date PRIMARY KEY,
            descricao text NOT NULL,
            CONSTRAINT feriado_descricao_nao_vazia CHECK (length(btrim(descricao)) > 0)
        )
    """)

    # Segunda a sexta, 9h às 18h. É dado, não código: mudar o expediente é um
    # INSERT, não uma migração.
    op.execute("""
        INSERT INTO expediente (dia_da_semana, inicio, fim) VALUES
            (1, '09:00', '18:00'),
            (2, '09:00', '18:00'),
            (3, '09:00', '18:00'),
            (4, '09:00', '18:00'),
            (5, '09:00', '18:00')
    """)

    # Minutos de expediente entre dois instantes. O SLA é medido em horas úteis
    # (decisão D06), e isolar o cálculo numa função mantém as consultas do
    # painel legíveis em vez de repetirem esta junção toda vez.
    #
    # Intervalo invertido ou vazio devolve 0: generate_series não produz linha
    # quando o fim é anterior ao início.
    op.execute(f"""
        CREATE FUNCTION minutos_uteis(p_inicio timestamptz, p_fim timestamptz)
        RETURNS integer
        LANGUAGE sql
        STABLE
        AS $$
            WITH dias AS (
                SELECT serie::date AS dia
                FROM generate_series(
                    (p_inicio AT TIME ZONE '{FUSO}')::date,
                    (p_fim    AT TIME ZONE '{FUSO}')::date,
                    interval '1 day'
                ) AS serie
            ),
            janelas AS (
                SELECT
                    ((dias.dia + e.inicio) AT TIME ZONE '{FUSO}') AS abre,
                    ((dias.dia + e.fim)    AT TIME ZONE '{FUSO}') AS fecha
                FROM dias
                JOIN expediente e
                  ON e.dia_da_semana = EXTRACT(dow FROM dias.dia)::smallint
                WHERE NOT EXISTS (
                    SELECT 1 FROM feriado f WHERE f.dia = dias.dia
                )
            )
            SELECT COALESCE(SUM(
                GREATEST(
                    0,
                    EXTRACT(EPOCH FROM (
                        LEAST(janelas.fecha, p_fim) - GREATEST(janelas.abre, p_inicio)
                    )) / 60
                )
            )::integer, 0)
            FROM janelas
        $$
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS minutos_uteis(timestamptz, timestamptz)")
    op.execute("DROP TABLE IF EXISTS feriado")
    op.execute("DROP TABLE IF EXISTS expediente")
    op.execute("DROP TABLE IF EXISTS politica_sla")
