# ADR-0009 — Laboratório isolado, por catálogo e protegido

**Data:** 2026-11-23 · **Status:** aceita

## Contexto

O escopo pedia um botão que "cria e remove o índice de verdade". Isso significa
DDL disparado por HTTP, contra um banco com centenas de milhares de linhas. Três
riscos concretos: o DDL travar ou corromper os dados da aplicação; alguém mandar
SQL arbitrário pelo navegador; e duas medições simultâneas criando e removendo
índices uma por cima da outra, invalidando os números das duas.

## Opções consideradas

### Onde roda

- **A — no banco da aplicação.** Nenhuma infraestrutura a mais, mas um `CREATE
  INDEX` segura lock na tabela que o painel está lendo.
- **B — em banco próprio na mesma instância.** Isolamento dos dados com um
  contêiner só; o laboratório tem a própria massa e o próprio registro.

### O que a tela pode pedir

- **A — SQL livre.** Flexível, e uma porta aberta no banco.
- **B — nome de experimento de um catálogo versionado.** Só roda o que foi
  declarado e revisado num pull request.

### Como impedir duas medições ao mesmo tempo

- **A — checar no caso de uso se há medição em andamento.** Simples, mas dois
  pedidos no mesmo instante passam os dois pela checagem.
- **B — trava consultiva no PostgreSQL (`pg_try_advisory_lock`).** A garantia
  fica no banco, que é quem de fato serializa.

## O que a IA sugeriu

Banco próprio na mesma instância (decisão D12), catálogo em vez de SQL livre,
token obrigatório e um interruptor por variável de ambiente que desliga o DDL
mesmo para quem tem o token (decisão D15), execução fora da requisição HTTP, e as
duas barreiras contra concorrência juntas: a checagem no caso de uso, que dá uma
resposta 409 clara, e a trava no banco, que é a garantia de verdade.

## O que eu decidi e por quê

As decisões D12 e D15 foram aprovadas no planejamento. Os detalhes de
implementação — trava consultiva, código 409, execução em segundo plano — foram
tomados pela IA dentro da delegação do lote final, e eu os mantive na revisão.

## O que a IA errou ou eu corrigi

1. **Mensagem de erro apontando para um comando que não existe.** O erro de
   banco sem esquema mandava rodar `make laboratorio`, mas o alvo se chama
   `make laboratorio-preparar`. Pego na revisão antes de entregar.

2. **Numeração deste registro.** O corpo do PR do ambiente Docker prometia este
   registro como "ADR-0010 no PR 32", da numeração planejada. A numeração real
   segue a ordem em que as decisões aconteceram, e ele ficou sendo o 0009.

## Consequências

- O laboratório precisa do próprio preparo (`make laboratorio-preparar`), que
  migra o banco dele e gera a massa grande — cerca de um minuto.
- Num deploy público, `LAB_HABILITADO=false` desliga criação e remoção de
  índice; a tela continua mostrando os resultados já registrados.
- **Reversão:** trocar o banco do laboratório pelo da aplicação é uma variável de
  ambiente. Não recomendado: o lock do `CREATE INDEX` passaria a competir com o
  painel.
