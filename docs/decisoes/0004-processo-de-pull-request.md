# ADR-0004 — Processo de pull request trabalhando sozinho

**Data:** 2026-11-23 · **Status:** aceita

## Contexto

O projeto adota "nada entra na `main` sem pull request", mas não existe um
segundo revisor: sou eu abrindo e eu mergeando. Sem resolver isso de propósito, o
pull request vira teatro.

Há ainda duas restrições concretas. O repositório nasceu privado, e no plano
gratuito do GitHub rulesets e proteção de branch só existem em repositório
público — ou seja, a `main` não pode ser protegida de verdade enquanto o projeto
não abrir. E a cadeia de ferramentas que eu uso coloca a chave de assinatura SSH
fora do alcance do ambiente onde a IA roda, então todo commit precisa passar pela
minha máquina.

## Opções consideradas

### A — Commitar direto na `main`

- **A favor:** sem cerimônia.
- **Contra:** joga fora o artefato mais valioso do repositório, que é o histórico
  mostrando trabalho fatiado e decisões em sequência.

### B — Pull request como registro de escopo, com a CI no papel de revisor

Cada PR faz uma coisa só, descreve o que, por quê e como testar, e só é mergeado
com a esteira verde. A proteção de branch entra quando o repositório abrir.

- **A favor:** o PR continua tendo função real — delimitar escopo e registrar
  raciocínio — mesmo sem segundo revisor; a CI reprova o que eu deixaria passar.
- **Contra:** nada impede, tecnicamente, um commit direto na `main` enquanto o
  repositório for privado. É disciplina, não trava.

## O que a IA sugeriu

Recomendou a opção B e foi contra as metas numéricas que estavam no escopo
original ("mais de 40 commits, pelo menos 10 PRs"), argumentando que meta de
commit produz commit falso e que o fatiamento natural do projeto ultrapassa esses
números sem esforço. Também recomendou merge commit em vez de rebase ou squash.

## O que eu decidi e por quê

Opção B, e abandonei as metas numéricas como meta.

Sobre a forma de merge: **merge commit**, não rebase nem squash. Rebase e squash
criam commits novos no servidor, e commits novos perdem a minha assinatura — o
repositório inteiro deixaria de aparecer como Verified. Entre histórico
perfeitamente linear e histórico assinado com os commits pequenos preservados,
escolhi o segundo. `git log --first-parent` continua dando a visão por PR.

## O que a IA errou ou eu corrigi

Quatro coisas concretas aconteceram, em ordem:

1. **Mensagens de commit com `\n` literal.** A primeira versão dos scripts montava
   `git commit -m 'título\n\ncorpo'` entre aspas simples, o que no bash não vira
   quebra de linha. Todos os corpos de mensagem sairiam numa linha só. Detectado
   ao reler o script gerado, antes de rodar; corrigido com `git commit -F -` e
   heredoc.

2. **Commit gigante na `main`.** O esqueleto do projeto — 24 arquivos, 240 linhas
   — entrou como commit raiz único, fora do fluxo de pull request, por uma
   ferramenta rodando `git add -A` na pasta. É exatamente o que o plano existia
   para evitar. A IA propôs rebobinar a `main`; depois mudou a própria
   recomendação quando o PR seguinte já estava aberto, porque refazer deixaria um
   pull request fechado sem merge no repositório para sempre. Decidi não
   reescrever: um primeiro commit carregando o esqueleto é comum e se explica em
   uma frase, e apagar o rastro seria pior do que o defeito. O raciocínio que
   ficou sem PR foi recuperado no [ADR-0003](0003-tipagem-estrita-e-teste-de-arquitetura.md).

3. **Uma PR engolindo arquivos da seguinte.** Com os arquivos de duas PRs soltos
   na mesma pasta, um `git add src/sdledger` da PR anterior commitaria arquivos
   da próxima. Detectado antes de entregar; resolvido entregando os arquivos de
   cada PR numa pasta de preparo, copiada para o repositório só depois de criar a
   branch.

4. **CRLF quebrando o contêiner.** Com `core.autocrlf=true` no Windows, um
   checkout limpo entregava `docker/init-lab.sh` com CRLF, e o entrypoint do
   PostgreSQL falharia com "bad interpreter" — o banco do laboratório nunca seria
   criado. O sinal foi um aviso do git no push, que seria fácil ignorar como
   ruído. Reproduzido num repositório de teste com `autocrlf=true` e corrigido com
   `.gitattributes`, dentro do mesmo pull request que introduziu o problema.

## Consequências

- Enquanto o repositório for privado, "nada entra na `main` sem PR" é convenção,
  não trava. Ao abrir, entra um ruleset exigindo a esteira verde.
- O histórico tem um merge commit por pull request. Para a visão por PR,
  `git log --first-parent`.
- O primeiro commit da `main` continua sendo um despejo de esqueleto, e o README
  e este registro dizem isso em vez de escondê-lo.
- **Reversão:** abrir o repositório e ligar o ruleset é uma configuração. Voltar
  atrás na forma de merge não é: o histórico já assinado ficaria reescrito e
  perderia o Verified.
