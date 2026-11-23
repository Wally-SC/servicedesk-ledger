-- Pergunta de negócio: que fração da carteira ativa em um mês deixou de ter
-- contrato no mês seguinte?
--
-- Métrica: docs/metricas.md, seção "Churn mensal".
-- Ativo no mês é ter contrato cuja vigência toca o mês. Troca de plano não é
-- churn, porque o cliente continua ativo. A série começa um mês antes da janela
-- para o primeiro mês ter com quem se comparar.
WITH meses AS (
    SELECT serie::date AS mes
    FROM generate_series(
        date_trunc('month', %(inicio)s::date) - interval '1 month',
        date_trunc('month', %(fim)s::date)    - interval '1 month',
        interval '1 month'
    ) AS serie
),
ativos AS (
    SELECT DISTINCT m.mes, ct.cliente_id
    FROM meses m
    JOIN contrato ct
      ON ct.vigencia && daterange(m.mes, (m.mes + interval '1 month')::date)
)
SELECT
    m.mes,
    anterior.total                                    AS ativos_no_mes_anterior,
    perdidos.total                                    AS perdidos,
    round(100.0 * perdidos.total / NULLIF(anterior.total, 0), 2)::float8 AS churn_percentual
FROM meses m
CROSS JOIN LATERAL (
    SELECT count(*) AS total
    FROM ativos a
    WHERE a.mes = (m.mes - interval '1 month')::date
) AS anterior
CROSS JOIN LATERAL (
    SELECT count(*) AS total
    FROM ativos a
    WHERE a.mes = (m.mes - interval '1 month')::date
      AND NOT EXISTS (
          SELECT 1 FROM ativos b
          WHERE b.mes = m.mes AND b.cliente_id = a.cliente_id
      )
) AS perdidos
WHERE m.mes >= date_trunc('month', %(inicio)s::date)
ORDER BY m.mes;
