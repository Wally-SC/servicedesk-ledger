-- Pergunta de negócio: dos chamados entregues na janela, quantos ficaram
-- dentro do prazo que valia para aquele cliente no dia em que ele foi aberto?
--
-- Métrica: docs/metricas.md, seção "Taxa de cumprimento de SLA".
--
-- O prazo não é fixo: depende do plano do cliente e da política vigente na data
-- de ABERTURA. As duas junções laterais resolvem isso em um passo por chamado,
-- sem precisar materializar todo o histórico de contratos e políticas.
WITH entregues AS (
    SELECT
        c.id,
        c.cliente_id,
        c.prioridade,
        (c.aberto_em AT TIME ZONE 'America/Sao_Paulo')::date AS dia_de_abertura,
        minutos_uteis(c.aberto_em, c.resolvido_em) AS minutos_ate_resolver
    FROM chamado c
    WHERE c.resolvido_em >= %(inicio)s
      AND c.resolvido_em <  %(fim)s
)
SELECT
    e.prioridade,
    count(*)                                                  AS entregues,
    count(*) FILTER (WHERE e.minutos_ate_resolver <= p.prazo) AS dentro_do_prazo,
    round(
        100.0 * count(*) FILTER (WHERE e.minutos_ate_resolver <= p.prazo) / count(*),
        1
    )::float8 AS taxa_percentual
FROM entregues e
JOIN LATERAL (
    -- contrato vigente no dia da abertura
    SELECT ct.plano_id
    FROM contrato ct
    WHERE ct.cliente_id = e.cliente_id
      AND ct.vigencia @> e.dia_de_abertura
    LIMIT 1
) AS contrato ON true
JOIN LATERAL (
    -- política de SLA vigente no mesmo dia, para o plano e a prioridade
    SELECT ps.minutos_uteis_resolucao AS prazo
    FROM politica_sla ps
    WHERE ps.plano_id   = contrato.plano_id
      AND ps.prioridade = e.prioridade
      AND ps.vigencia  @> e.dia_de_abertura
    LIMIT 1
) AS p ON true
GROUP BY e.prioridade
ORDER BY
    CASE e.prioridade
        WHEN 'critica' THEN 1 WHEN 'alta' THEN 2
        WHEN 'media'   THEN 3 ELSE 4
    END;
