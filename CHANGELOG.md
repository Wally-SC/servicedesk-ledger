# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
Cada versão aponta o pull request que a fechou.

## [1.0.0] — 2026-11-23

### Adicionado
- Resultados do laboratório em `docs/laboratorio/resultados.md`, com três rodadas
  de medição e a explicação de cada resultado, inclusive o que não melhora.
- README final com capturas de tela, destaques de SQL e resultados medidos.
- Glossário de métricas apontando o arquivo que implementa cada uma.

### Corrigido
- A imagem Docker não incluía o `alembic.ini`: migrar, testar e preparar o
  laboratório falhavam dentro do contêiner.

## [0.4.0] — 2026-11-23

### Adicionado
- Laboratório de índices: cinco experimentos declarados em catálogo, protocolo de
  medição com `EXPLAIN (ANALYZE, BUFFERS)` e mediana, banco próprio.
- Medição por HTTP em segundo plano, com token, interruptor por ambiente e trava
  consultiva no PostgreSQL contra execução simultânea.
- Tela com os dois planos de execução lado a lado.

## [0.3.0] — 2026-11-23

### Adicionado
- Domínio da fatura: mensalidade, franquia e excedente em blocos de 15 minutos.
- Fechamento de ciclo idempotente.
- Massa fictícia com saída de clientes e histórico de faturas emitido pelo próprio
  caso de uso de fechamento.
- Consultas de receita por competência, receita em atraso por faixa e churn.
- API e tela da cobrança.

### Corrigido
- Percentuais e números no formato brasileiro nas duas telas.

## [0.2.0] — 2026-11-23

### Adicionado
- API do painel com janela validada e erros de domínio traduzidos para HTTP.
- Tela do painel servida pelo próprio projeto, com Chart.js incluído no
  repositório.

### Corrigido
- A tendência semanal passou a usar só semanas completas.

## [0.1.0] — 2026-11-23

### Adicionado
- Ambiente em Docker Compose, CI com PostgreSQL de serviço, teste de arquitetura.
- Modelo de dados com constraints de exclusão, política de SLA com vigência e
  relógio em horas úteis.
- Gerador de massa fictícia reproduzível em dois perfis.
- Domínio do chamado, tipos de valor, política de SLA e franquia.
- As cinco consultas do painel.
