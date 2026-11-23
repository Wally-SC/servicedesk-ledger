-- Pergunta de negócio: o atendimento está melhorando ou piorando semana a
-- semana?
--
-- Métrica: docs/metricas.md, seção "Tendência semanal".
-- A variação sai de LAG sobre a própria série, e o acumulado de SUM OVER: as
-- duas coisas em uma varredura, sem autojunção.
WITH por_semana AS (
    SELECT
        date_trunc('week', c.resolvido_em AT TIME ZONE 'America/Sao_Paulo')::date AS semana,
        count(*) AS resolvidos,
        percentile_cont(0.95) WITHIN GROUP (
            ORDER BY minutos_uteis(c.aberto_em, c.resolvido_em)
        ) AS resolucao_p95
    FROM chamado c
    WHERE c.resolvido_em >= %(inicio)s
      AND c.resolvido_em <  %(fim)s
    GROUP BY 1
)
SELECT
    semana,
    resolvidos,
    round(resolucao_p95::numeric, 1)::float8 AS resolucao_p95,
    round(
        (resolucao_p95 - LAG(resolucao_p95) OVER (ORDER BY semana))::numeric, 1
    )::float8 AS variacao_p95,
    resolvidos - LAG(resolvidos) OVER (ORDER BY semana) AS variacao_resolvidos,
    SUM(resolvidos) OVER (ORDER BY semana) AS resolvidos_acumulados
FROM por_semana
ORDER BY semana;
