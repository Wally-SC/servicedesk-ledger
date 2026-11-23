-- Pergunta: quantas respostas públicas os agentes deram por dia nos últimos 30 dias?
--
-- chamado_evento é a maior tabela do banco. A consulta quer um tipo de evento
-- numa janela de datas: o índice parcial guarda só esse tipo, por data.
SELECT (ocorrido_em AT TIME ZONE 'America/Sao_Paulo')::date AS dia, count(*) AS respostas
FROM chamado_evento
WHERE tipo = 'resposta_publica'
  AND ocorrido_em >= %(inicio)s
  AND ocorrido_em <  %(fim)s
GROUP BY 1
ORDER BY 1;
