# Consultas analíticas

Uma pergunta de negócio por arquivo. Todo arquivo começa com um comentário que diz
qual pergunta ele responde e qual métrica de `docs/metricas.md` ele implementa.

Organização:

- `painel/` — percentis, backlog, taxa de SLA, tendência e ranking de clientes
- `faturamento/` — receita do mês, receita em atraso e churn
- `laboratorio/experimentos/` — a consulta pesada de cada experimento
- `laboratorio/indices/` — o índice candidato de cada experimento

Não existe SQL solto no código Python: o arquivo é a unidade de revisão, porque é
nele que o `EXPLAIN` do laboratório é medido.
