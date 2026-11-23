-- Índice candidato: parcial, só com os chamados em aberto.
CREATE INDEX lab_chamado_em_aberto ON chamado (prioridade, aberto_em)
    WHERE resolvido_em IS NULL;
