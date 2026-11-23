-- Índice candidato: cliente e data de abertura, na ordem da consulta.
CREATE INDEX lab_chamado_cliente_abertura ON chamado (cliente_id, aberto_em DESC);
