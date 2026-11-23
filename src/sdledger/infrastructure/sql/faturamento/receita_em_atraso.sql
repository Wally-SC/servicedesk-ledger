-- Pergunta de negócio: quanto dinheiro está vencido e não pago hoje, de quantos
-- clientes, e há quanto tempo?
--
-- Métrica: docs/metricas.md, seção "Receita em atraso".
-- Fatura que vence hoje ainda não está atrasada: o corte é vencimento ANTES da
-- data de referência. As faixas de atraso saem de FILTER numa varredura só.
WITH vencidas AS (
    SELECT
        cf.cliente_id,
        f.total_centavos,
        %(referencia)s::date - f.vencimento AS dias_de_atraso
    FROM fatura f
    JOIN ciclo_faturamento cf ON cf.id = f.ciclo_id
    WHERE f.estado = 'emitida'
      AND f.vencimento < %(referencia)s
)
SELECT
    count(*)                                                                   AS faturas,
    count(DISTINCT cliente_id)                                                 AS clientes,
    COALESCE(sum(total_centavos), 0)                                           AS total_centavos,
    COALESCE(sum(total_centavos) FILTER (WHERE dias_de_atraso <= 30), 0)       AS ate_30_dias_centavos,
    COALESCE(sum(total_centavos) FILTER (WHERE dias_de_atraso BETWEEN 31 AND 90), 0) AS de_31_a_90_dias_centavos,
    COALESCE(sum(total_centavos) FILTER (WHERE dias_de_atraso > 90), 0)        AS mais_de_90_dias_centavos
FROM vencidas;
