-- Pergunta: quantos minutos cada cliente consumiu no último mês?
--
-- É a leitura que o fechamento de ciclo faz para calcular hora excedente. O
-- único índice de apontamento é por chamado, criado por integridade.
SELECT c.cliente_id, sum(a.minutos) AS minutos
FROM apontamento a
JOIN chamado c ON c.id = a.chamado_id
WHERE a.apontado_em >= %(inicio)s
  AND a.apontado_em <  %(fim)s
GROUP BY c.cliente_id;
