-- Pergunta de negócio: quais clientes merecem atenção agora, considerando
-- volume, violação de SLA e idade do que está parado?
--
-- Métrica: docs/metricas.md, seção "Ranking de clientes críticos".
--
-- A ordenação combina os três sinais num escore simples e explícito. NTILE
-- separa os clientes em quartis de criticidade, que é o que a tela usa para
-- colorir a lista sem inventar faixas arbitrárias na camada de apresentação.
WITH por_cliente AS (
    SELECT
        c.cliente_id,
        count(*)                                        AS chamados,
        count(*) FILTER (WHERE c.resolvido_em IS NULL)  AS em_aberto,
        count(*) FILTER (WHERE c.prioridade IN ('alta', 'critica')) AS prioritarios,
        COALESCE(
            round(EXTRACT(EPOCH FROM max(
                CASE WHEN c.resolvido_em IS NULL
                     THEN %(agora)s::timestamptz - c.aberto_em END
            )) / 86400.0, 1),
            0
        )::float8 AS idade_maxima_dias
    FROM chamado c
    WHERE c.aberto_em >= %(inicio)s
      AND c.aberto_em <  %(fim)s
    GROUP BY c.cliente_id
),
com_escore AS (
    SELECT
        p.*,
        cl.nome,
        p.em_aberto * 3 + p.prioritarios + p.idade_maxima_dias AS escore
    FROM por_cliente p
    JOIN cliente cl ON cl.id = p.cliente_id
)
SELECT
    ROW_NUMBER() OVER (ORDER BY escore DESC, cliente_id) AS posicao,
    NTILE(4)     OVER (ORDER BY escore DESC)             AS quartil,
    cliente_id,
    nome,
    chamados,
    em_aberto,
    prioritarios,
    idade_maxima_dias,
    round(escore::numeric, 1)::float8 AS escore
FROM com_escore
ORDER BY posicao
LIMIT %(limite)s;
