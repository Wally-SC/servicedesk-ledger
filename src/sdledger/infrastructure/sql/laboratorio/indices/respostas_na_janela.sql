-- Índice candidato: parcial, só respostas públicas, por data.
CREATE INDEX lab_evento_resposta_publica ON chamado_evento (ocorrido_em)
    WHERE tipo = 'resposta_publica';
