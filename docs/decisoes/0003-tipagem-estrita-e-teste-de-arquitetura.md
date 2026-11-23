# ADR-0003 — Tipagem estrita e teste de arquitetura desde o primeiro commit

**Data:** 2026-11-23 · **Status:** aceita

## Contexto

O projeto declara duas regras que são fáceis de escrever no README e fáceis de
furar no código: "dependências apontam para dentro" e "nenhuma regra de negócio
em rota ou em consulta solta". Um projeto de portfólio que afirma arquitetura e
não a verifica é exatamente o que um revisor experiente testa primeiro.

A mesma pergunta valia para tipagem: ligar `mypy` no começo ou depois.

## Opções consideradas

### A — Regra documentada, verificação por revisão

- **A favor:** nada a escrever agora.
- **Contra:** trabalhando sozinho, a revisão sou eu mesmo; a regra vale até o dia
  em que der preguiça.

### B — Regra verificada por teste automatizado

Um teste lê cada arquivo das camadas com `ast` e falha quando `domain` ou
`application` importam framework, banco ou camada de fora.

- **A favor:** a regra passa a ser executável; quebra na esteira, não na conversa.
- **Contra:** mais um teste para manter; precisa resolver import relativo
  corretamente, senão dá falso negativo.

Para tipagem, a escolha paralela era `mypy` estrito agora ou depois.

## O que a IA sugeriu

Propôs a opção B junto com `mypy --strict` já no primeiro commit, com dois
argumentos: ligar tipagem estrita depois, com código escrito, é retrabalho
garantido; e uma regra de arquitetura sem verificação automática é só uma frase
bonita no README.

## O que eu decidi e por quê

Aceitei a proposta como veio, sem contraproposta — registro isso de propósito, em
vez de inventar uma deliberação que não houve. O argumento que pesou foi o
segundo: o repositório inteiro existe para sustentar a afirmação de arquitetura,
e afirmação sem verificação é o ponto mais fácil de derrubar numa entrevista.

## O que a IA errou ou eu corrigi

A primeira versão do teste ignorava import relativo, o que deixaria passar um
`from ...infrastructure import x` dentro do domínio. Foi corrigido antes de
entregar, resolvendo o nome absoluto a partir do pacote do arquivo e do nível do
import.

A verificação de que o teste realmente morde foi feita na mão: inserir
`import fastapi` em `domain/chamado/__init__.py` e confirmar que a suíte falha
apontando o arquivo. Teste de guarda que nunca foi visto falhando não é guarda.

## Consequências

- Todo módulo novo nasce tipado; `mypy --strict` roda na esteira e no `make tipos`.
- Dependência nova de framework no núcleo quebra a suíte, de propósito. Se um dia
  houver motivo legítimo, a lista de proibidos é o lugar de registrar a exceção —
  e exige explicação no PR.
- **Reversão:** apagar o teste e afrouxar o `mypy` é trivial. O que não volta é a
  confiança de que a arquitetura descrita é a arquitetura real.
