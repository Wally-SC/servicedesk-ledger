# ADR-0006 — Massa fictícia em dois perfis

**Data:** 2026-11-23 · **Status:** aceita

## Contexto

O laboratório de índices só prova alguma coisa se o banco tiver volume: com mil
chamados, qualquer consulta roda rápido com ou sem índice, e a tabela de antes e
depois do README vira enfeite. O escopo pede centenas de milhares de chamados.

Ao mesmo tempo, a esteira roda em todo pull request e os testes de integração
precisam de dados. Gerar centenas de milhares de linhas a cada execução
inviabilizaria o tempo de cada PR.

## Opções consideradas

### A — Um perfil só, grande

- **A favor:** um caminho de código, nenhum parâmetro.
- **Contra:** a esteira passaria minutos gerando massa em todo PR, e o teste de
  reprodutibilidade ficaria caro demais para existir.

### B — Dois perfis, mesmo gerador

Um perfil pequeno, determinístico, para teste e esteira; um grande, para o
laboratório e a demonstração local.

- **A favor:** o mesmo código serve aos dois, então o que a esteira exercita é o
  que roda em produção de mentira; o teste de reprodutibilidade cabe em segundos.
- **Contra:** um parâmetro a mais e a tentação de só testar o pequeno.

## O que a IA sugeriu

Recomendou a opção B e, junto, duas coisas que não estavam no escopo: carga por
`COPY` em vez de `INSERT` linha a linha, e a data final da janela como parâmetro
em vez de constante. O argumento da segunda foi que uma janela fixa no código
deixa a demonstração velha em uma semana — o painel olha os últimos dias, e eles
precisam existir.

## O que eu decidi e por quê

Opção B, com `COPY` e com `--fim` parametrizado. A reprodutibilidade passa a ser
por par (semente, data final), e isso está escrito no módulo e coberto por teste:
sem ela, nenhum número do laboratório pode ser comparado com outro, porque não
dá para saber se a diferença veio do índice ou de dados diferentes.

## O que a IA errou ou eu corrigi

Duas coisas, e as duas só apareceram porque a massa foi gerada de verdade:

1. **A constraint de autor do evento estava errada no esquema.** A migração 0002
   exigia autor apenas em resposta pública e nota interna, e o proibia em
   qualquer outro tipo. Resolver um chamado é ato de um agente e o evento de
   resolução tem autor, então o banco recusou a primeira carga. A regra foi
   corrigida na migração 0005: mensagem do cliente nunca tem autor agente,
   resposta pública e nota interna sempre têm, os demais tipos são livres.
   O esquema tinha passado por revisão e por teste de integração sem que o
   defeito aparecesse — faltava dado realista.

2. **A distribuição de chamados por cliente nascia achatada.** A primeira versão
   sorteava o cliente com uma gaussiana e um resto de divisão, e o resto
   embrulhava a cauda: o maior cliente tinha 2,5 vezes a média. Fila de suporte
   não se comporta assim. Com pesos do tipo Zipf, 10% dos clientes passaram a
   concentrar 70% dos chamados, que é o que torna o ranking de clientes críticos
   uma informação e não uma lista.

## Consequências

- O perfil grande leva cerca de 50 segundos e deixa o banco em torno de 300 MB.
  É local: nenhum tier gratuito de PostgreSQL aguenta isso com folga.
- Trocar a semente ou a data final muda todos os números medidos. Qualquer
  resultado publicado no README precisa dizer com qual par foi obtido.
- **Reversão:** apagar o perfil grande é trivial. O que não se recupera é a
  capacidade de medir índice: sem volume, o laboratório não tem o que mostrar.
