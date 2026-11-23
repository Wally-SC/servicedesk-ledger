-- Pergunta de negócio: dos chamados entregues na janela, quanto tempo útil
-- levou para dar a primeira resposta e para resolver, e quantos saíram sem
-- nenhuma resposta pública?
--
-- Métrica: docs/metricas.md, seção "p50, p90 e p95".
-- O denominador é chamado RESOLVIDO na janela, não aberto (ADR-0005).
-- Primeira resposta e resolução vêm na mesma consulta porque compartilham a
-- mesma coorte: separá-las custaria duas varreduras do mesmo conjunto.
WITH entregues AS (
    SELECT
        CASE
            WHEN c.primeira_resposta_em IS NULL THEN NULL
            ELSE minutos_uteis(c.aberto_em, c.primeira_resposta_em)
        END AS minutos_resposta,
        minutos_uteis(c.aberto_em, c.resolvido_em) AS minutos_resolucao
    FROM chamado c
    WHERE c.resolvido_em >= %(inicio)s
      AND c.resolvido_em <  %(fim)s
)
SELECT
    count(*)                                       AS resolvidos,
    count(*) FILTER (WHERE minutos_resposta IS NULL) AS sem_primeira_resposta,
    percentile_cont(0.50) WITHIN GROUP (ORDER BY minutos_resposta)::float8  AS resposta_p50,
    percentile_cont(0.90) WITHIN GROUP (ORDER BY minutos_resposta)::float8  AS resposta_p90,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY minutos_resposta)::float8  AS resposta_p95,
    percentile_cont(0.50) WITHIN GROUP (ORDER BY minutos_resolucao)::float8 AS resolucao_p50,
    percentile_cont(0.90) WITHIN GROUP (ORDER BY minutos_resolucao)::float8 AS resolucao_p90,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY minutos_resolucao)::float8 AS resolucao_p95
FROM entregues;
