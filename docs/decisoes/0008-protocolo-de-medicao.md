# ADR-0008 — Protocolo de medição do laboratório de índices

**Data:** 2026-11-23 · **Status:** aceita

## Contexto

O laboratório existe para mostrar, com número, o que um índice faz por uma
consulta. O número vai para o README, e é exatamente o número que alguém
experiente vai tentar derrubar: rodar a consulta duas vezes e comparar mede
cache, não índice.

## Opções consideradas

### A — Tempo de relógio de uma execução de cada lado

- **A favor:** trivial.
- **Contra:** a primeira execução lê do disco e a segunda do cache; o "ganho"
  pode ser inteiro de cache.

### B — `EXPLAIN (ANALYZE, BUFFERS)`, aquecimento descartado, mediana de N

- **A favor:** os dois lados partem do mesmo estado de cache, declarado; a
  mediana resiste a uma execução atípica; o plano de cada lado fica guardado
  para mostrar *por que* ficou mais rápido.
- **Contra:** mede cache quente, que é o cenário favorável. Isso precisa estar
  escrito junto do número, e está.

## O que a IA sugeriu

O protocolo da opção B, fixado antes de escrever o runner: `statement_timeout` e
`lock_timeout` na sessão; índice removido e tabela analisada antes do "sem";
uma execução de aquecimento descartada; N execuções com `EXPLAIN (ANALYZE,
BUFFERS)`; índice criado e tabela analisada de novo; mesma medição; índice
removido no fim, inclusive se a medição falhar no meio.

## O que eu decidi e por quê

Aceitei o protocolo como decisão D13 do planejamento, antes da primeira linha de
código. O que mudou no caminho, abaixo, foi descoberto medindo — e cada mudança
está no código e neste registro.

## O que a IA errou ou eu corrigi

1. **`%` em comentário derrubou a execução.** O psycopg interpreta `%` em
   qualquer parte da consulta, inclusive em comentário. A IA tinha acabado de
   checar que nenhum arquivo `.sql` tinha `%` solto e, em seguida, escreveu "5%"
   no comentário de um experimento. Corrigido o texto, e a checagem virou teste
   (`tests/unidade/test_arquivos_sql.py`) para não depender de lembrar.

2. **Tempo de plano paralelo somado entre workers.** A primeira leitura do plano
   multiplicava o tempo de cada nó pelo número de laços. Em plano paralelo os
   laços são workers rodando ao mesmo tempo, e a tela mostraria um `Sort` de
   140 ms dentro de uma consulta de 53 ms. Detectado lendo o plano; agora o
   tempo é por laço, como o próprio PostgreSQL reporta.

3. **Tabela recém-carregada mede pior do que produção.** A primeira medição pelo
   comando oficial deu 7,6x para o índice parcial do backlog, contra 32x medidos
   antes no banco da aplicação. A diferença era o estado da tabela: carregada
   por `COPY` e nunca aspirada, sem mapa de visibilidade, nenhum *index-only
   scan* evita ir à tabela. Produção vive com autovacuum, então o preparo do
   laboratório passou a terminar com `VACUUM (ANALYZE)`.

4. **Variação entre rodadas.** Num ambiente de 2 vCPUs, tempos abaixo de 10 ms
   oscilam bastante. Em três rodadas de nove execuções, o histórico do cliente
   ficou entre 401x e 866x. A ordem e a grandeza são estáveis; o multiplicador
   exato não é. Por isso a documentação publica a faixa das três rodadas, e não
   a rodada mais bonita.

## Consequências

- Todo número do laboratório vem com o ambiente: versão do PostgreSQL, cache
  quente declarado, número de execuções.
- O resultado mais útil é o que não melhora: o índice de `consumo_do_mes` é
  usado pelo planejador e o ganho fica em 1,1x, porque o gargalo é a junção com
  os 300 mil chamados, e não o filtro de data. Ele fica no catálogo de propósito.
- **Reversão:** o protocolo é uma função. Trocar mediana por percentil ou cache
  quente por cache frio é mudar `medir`, e os testes continuam valendo.
