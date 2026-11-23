# ADR-0002 — Acesso a dados com psycopg3 e SQL em arquivo, sem ORM

**Data:** 2026-11-23 · **Status:** aceita

## Contexto

O projeto precisa escolher como falar com o PostgreSQL, sabendo que as consultas
analíticas vão usar CTEs encadeadas, funções de janela, `PERCENTILE_CONT`,
agregação condicional com `FILTER` e junção lateral, e que cada uma delas será
medida com `EXPLAIN (ANALYZE, BUFFERS)` no laboratório de índices.

## Opções consideradas

### A — psycopg3 e SQL puro em arquivos versionados

- **A favor:** uma forma só de falar com o banco; o SQL é exatamente o que roda,
  então o `EXPLAIN` do laboratório mede o mesmo texto que está no repositório;
  DDL escrito à mão força pensar constraint e chave.
- **Contra:** mapeamento de linha para dataclass escrito à mão; sem portabilidade
  entre bancos; `alembic autogenerate` deixa de funcionar.

### B — SQLAlchemy Core na escrita e SQL puro na leitura

- **A favor:** construção de query mais segura na escrita; `autogenerate` nas
  migrações.
- **Contra:** duas formas de falar com o banco, dobrando superfície de
  aprendizado e de bug, para comprar portabilidade que este projeto não usa.

### C — ORM completo

- **A favor:** menos código de mapeamento na escrita.
- **Contra:** esconde o SQL, que é o produto aqui; o `EXPLAIN` passa a medir algo
  que ninguém escreveu.

## O que a IA sugeriu

Recomendou a opção A, observando que a perda do `autogenerate` é desejável neste
projeto — DDL escrito à mão é o que obriga a decidir constraint, chave e índice
de propósito — e que o custo do mapeamento manual se resolve com um auxiliar
pequeno de linha para dataclass.

## O que eu decidi e por quê

Decidi pela opção A, e pelo Alembic com revisões de SQL escrito à mão para as
migrações, mantendo uma toolchain só em Python.

## O que a IA errou ou eu corrigi

Minha instrução para esta decisão foi ditada por voz e chegou transcrita como
"PyScope 3 com MySQL puro e envio de arquivos em ORM". A IA não assumiu o que
estava escrito: devolveu a leitura dela — psycopg3, PostgreSQL, sem ORM — para
confirmação antes de escrever qualquer linha. Era o que eu queria dizer. Aceitar
a transcrição literal teria trocado o banco do projeto.

## Consequências

- Não há `autogenerate`: cada migração é escrita e revisada à mão.
- Trocar de banco deixa de ser barato. É aceitável: o projeto usa recursos de
  PostgreSQL de propósito.
- **Reversão:** introduzir SQLAlchemy Core apenas na escrita é possível sem tocar
  o domínio, porque a escrita já passa por portas de repositório. A leitura
  analítica não seria revertida: ela é o produto.
