-- Pergunta: quais são os 50 chamados mais recentes do maior cliente?
--
-- Já existe índice em cliente_id, criado pela migração por integridade. Ele
-- acha as linhas do cliente, mas não na ordem: o banco busca todas e ordena.
-- O índice composto entrega as 50 primeiras já ordenadas e para.
SELECT id, assunto, estado, aberto_em
FROM chamado
WHERE cliente_id = %(cliente_id)s
ORDER BY aberto_em DESC
LIMIT 50;
