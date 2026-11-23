# Glossário de métricas

Toda métrica do painel e da cobrança é definida aqui antes de existir em SQL.
Número de painel sem definição escrita é número indefensável: "p95 de quê, sobre
qual janela, contando chamado aberto ou resolvido no período?" é a primeira
pergunta de qualquer entrevista.

Cada métrica aponta o arquivo `.sql` que a implementa. Enquanto o arquivo não
existe, a linha diz que está planejada.

## Convenções

- **Fuso:** todo agrupamento por dia, semana ou mês usa `America/Sao_Paulo`.
  Os instantes são gravados em `timestamptz`.
- **Janela padrão:** 30 dias encerrando na data de referência, salvo indicação.
- **Semana:** semana ISO (segunda a domingo).
- **Horas úteis:** a duração de SLA é contada em minutos de expediente, a partir
  da tabela de expediente e feriados, e não em horas corridas.

## Chamados

### Tempo de primeira resposta

Minutos úteis entre a abertura do chamado e o primeiro evento de resposta pública
de um agente.

Não conta como primeira resposta: nota interna, mensagem automática de abertura e
qualquer mensagem do próprio solicitante. Chamado que nunca teve resposta pública
não entra no cálculo e aparece separado, como contagem de chamados sem primeira
resposta — diluí-lo no percentil esconderia o pior caso.

*Planejada: `infrastructure/sql/painel/percentis_primeira_resposta.sql`*

### Tempo de resolução

Minutos úteis entre a abertura e o evento de resolução. Em caso de reabertura,
conta até a **última** resolução, e o chamado aparece uma vez só.

Na primeira versão o relógio não para enquanto o chamado está aguardando o
cliente. O desconto desses períodos entra depois, num pull request próprio, com os
números antes e depois — é mudança de métrica e precisa ser visível.

*Planejada: `infrastructure/sql/painel/percentis_resolucao.sql`*

### p50, p90 e p95

`PERCENTILE_CONT` sobre o conjunto de chamados **resolvidos dentro da janela**,
agrupados pela data de resolução.

O denominador é chamado resolvido, não chamado aberto. O porquê está no
[ADR-0005](decisoes/0005-definicao-das-metricas.md).

### Taxa de cumprimento de SLA

Percentual de chamados resolvidos na janela cujo tempo de resolução ficou dentro
do prazo da política de SLA **vigente na data de abertura** do chamado.

A política varia por prioridade e por plano e tem vigência: um chamado aberto
antes de o cliente trocar de plano é medido pelo prazo que valia naquele dia.

*Planejada: `infrastructure/sql/painel/taxa_sla.sql`*

### Backlog

Chamados não resolvidos no instante da consulta, quebrados por prioridade e por
faixa de idade.

As faixas são `0–1`, `1–3`, `3–7` e `mais de 7` dias, em **dias corridos** — e
não em horas úteis. Backlog é leitura de fila, e quem olha a fila pensa em "esse
chamado está parado há cinco dias", não em expediente. É a única métrica do painel
que usa tempo corrido, e está marcada assim de propósito.

*Planejada: `infrastructure/sql/painel/backlog_por_idade.sql`*

### Tendência semanal

Série dos percentis e da taxa de SLA por semana ISO, com a variação em relação à
semana anterior obtida por função de janela.

*Planejada: `infrastructure/sql/painel/tendencia_semanal.sql`*

### Ranking de clientes críticos

Clientes ordenados por uma combinação de volume na janela, taxa de violação de SLA
e idade do backlog. A fórmula exata entra junto da consulta e é registrada aqui
quando existir.

*Planejada: `infrastructure/sql/painel/ranking_clientes.sql`*

## Cobrança

### Horas consumidas e horas excedentes

Horas consumidas no ciclo são a soma dos apontamentos dos chamados do cliente.
Horas excedentes são o que passa da franquia do plano, arredondado **para cima em
blocos de 15 minutos**, no fechamento do ciclo.

O arredondamento é regra de negócio e mora no domínio, não no SQL.

### Receita do mês

Soma do valor das faturas com competência no mês, emitidas ou não pagas. É receita
reconhecida, não caixa.

*Planejada: `infrastructure/sql/faturamento/receita_do_mes.sql`*

### Receita em atraso

Soma do valor das faturas vencidas e não pagas na data de referência. Fatura
vencida hoje ainda não é atraso.

*Planejada: `infrastructure/sql/faturamento/receita_em_atraso.sql`*

### Churn mensal

Clientes com plano ativo no mês anterior e sem plano ativo no mês de referência,
dividido pelo total de ativos no mês anterior.

Cliente que nunca teve plano ativo não entra em nenhum dos dois lados. Troca de
plano não é churn.

*Planejada: `infrastructure/sql/faturamento/churn_mensal.sql`*
