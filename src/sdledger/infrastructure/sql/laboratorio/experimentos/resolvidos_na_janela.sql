-- Pergunta: quantos chamados foram entregues nos últimos 30 dias, por prioridade?
--
-- É o filtro que abre os percentis e a taxa de SLA do painel. Sem índice em
-- resolvido_em, o banco lê a tabela inteira para ficar com um vigésimo dela.
SELECT prioridade, count(*) AS entregues
FROM chamado
WHERE resolvido_em >= %(inicio)s
  AND resolvido_em <  %(fim)s
GROUP BY prioridade
ORDER BY prioridade;
