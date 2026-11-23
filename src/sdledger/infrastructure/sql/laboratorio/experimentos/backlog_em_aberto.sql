-- Pergunta: o que está parado na fila agora, por prioridade?
--
-- Menos de dois em cada cem chamados estão em aberto. Um índice parcial só com eles é
-- pequeno e responde sem tocar nos outros.
SELECT prioridade, count(*) AS em_aberto, min(aberto_em) AS mais_antigo
FROM chamado
WHERE resolvido_em IS NULL
GROUP BY prioridade
ORDER BY prioridade;
