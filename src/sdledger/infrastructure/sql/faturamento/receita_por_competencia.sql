-- Pergunta de negócio: quanto foi faturado em cada competência, quanto disso é
-- mensalidade e quanto é hora excedente, e como variou em relação ao mês anterior?
--
-- Métrica: docs/metricas.md, seção "Receita do mês".
-- Receita reconhecida, não caixa: entra a fatura emitida ou paga, fica de fora
-- a cancelada. A divisão por tipo de item sai de FILTER sobre a mesma junção, e
-- a variação de LAG sobre a própria série.
WITH por_competencia AS (
    SELECT
        cf.competencia,
        count(DISTINCT f.id)                                             AS faturas,
        COALESCE(sum(fi.valor_centavos) FILTER (WHERE fi.tipo = 'mensalidade'), 0)    AS mensalidades_centavos,
        COALESCE(sum(fi.valor_centavos) FILTER (WHERE fi.tipo = 'hora_excedente'), 0) AS excedente_centavos,
        sum(fi.valor_centavos)                                           AS receita_centavos
    FROM ciclo_faturamento cf
    JOIN fatura f       ON f.ciclo_id = cf.id AND f.estado <> 'cancelada'
    JOIN fatura_item fi ON fi.fatura_id = f.id
    WHERE cf.competencia >= %(inicio)s
      AND cf.competencia <  %(fim)s
    GROUP BY cf.competencia
)
SELECT
    competencia,
    faturas,
    mensalidades_centavos,
    excedente_centavos,
    receita_centavos,
    round(
        100.0 * (receita_centavos - LAG(receita_centavos) OVER serie)
        / NULLIF(LAG(receita_centavos) OVER serie, 0),
        1
    )::float8 AS variacao_percentual
FROM por_competencia
WINDOW serie AS (ORDER BY competencia)
ORDER BY competencia;
