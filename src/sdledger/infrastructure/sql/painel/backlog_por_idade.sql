-- Pergunta de negócio: o que está parado na fila agora, por prioridade e há
-- quanto tempo?
--
-- Métrica: docs/metricas.md, seção "Backlog".
-- A idade é em DIAS CORRIDOS, não em horas úteis, e é a única exceção à regra
-- de expediente: quem olha a fila pensa "parado há cinco dias".
WITH em_aberto AS (
    SELECT
        c.prioridade,
        %(agora)s::timestamptz - c.aberto_em AS idade
    FROM chamado c
    WHERE c.resolvido_em IS NULL
)
SELECT
    prioridade,
    count(*) AS total,
    count(*) FILTER (WHERE idade <  interval '1 day')  AS ate_1_dia,
    count(*) FILTER (WHERE idade >= interval '1 day'
                       AND idade <  interval '3 days') AS de_1_a_3_dias,
    count(*) FILTER (WHERE idade >= interval '3 days'
                       AND idade <  interval '7 days') AS de_3_a_7_dias,
    count(*) FILTER (WHERE idade >= interval '7 days')  AS mais_de_7_dias,
    round(EXTRACT(EPOCH FROM max(idade)) / 86400.0, 1)::float8 AS idade_maxima_dias
FROM em_aberto
GROUP BY prioridade
ORDER BY
    CASE prioridade
        WHEN 'critica' THEN 1 WHEN 'alta' THEN 2
        WHEN 'media'   THEN 3 ELSE 4
    END;
