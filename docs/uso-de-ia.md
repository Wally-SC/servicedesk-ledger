# Como a IA foi usada neste projeto

Este arquivo existe porque esconder o uso de IA num projeto de 2026 seria menos
honesto do que descrevê-lo. O que segue é o método real, não uma declaração de
intenção.

## O papel de cada um

A IA trabalha como um engenheiro sênior em revisão de design: antes de cada
decisão relevante ela apresenta as opções, os prós e contras e uma recomendação.
Eu decido. A decisão vira um registro em `docs/decisoes`, escrito no mesmo pull
request que a implementa.

A responsabilidade técnica é minha. Os commits são assinados pela minha chave,
porque cada um passa pela minha máquina depois de eu ler o que vai entrar.

## O que isso significa na prática

- **A IA escreveu a maior parte do código e dos textos deste repositório.** Dizer
  o contrário seria mentira, e o histórico de commits não sustentaria.
- **O escopo, as decisões e os cortes são meus.** Onde eu segui a recomendação
  sem discordar, o registro diz exatamente isso, em vez de inventar uma
  deliberação que não houve.
- **A IA foi instruída a questionar, não a concordar.** O primeiro retorno dela
  sobre o escopo começou dizendo que o projeto estava grande demais, que os pesos
  60/20/20 estavam errados e que as metas numéricas de Git (40 commits, 10 PRs)
  eram armadilha — e essas três objeções mudaram o plano.
- **Erro de IA é registrado, não apagado.** Os registros de decisão têm uma seção
  para isso e ela só é preenchida quando algo deu errado de verdade. Exemplos que
  já aconteceram estão no [ADR-0004](decisoes/0004-processo-de-pull-request.md).

## O que eu não deixei a IA fazer

- Decidir o escopo sozinha.
- Escrever registro de decisão sobre deliberação que não aconteceu.
- Afirmar no README funcionalidade que ainda não existe.
- Assinar commit no meu lugar: a chave de assinatura nunca saiu da minha máquina,
  e por isso cada pull request passa por um comando que eu rodo.

## Como ler o histórico

O primeiro commit da `main` carrega o esqueleto do projeto inteiro — ele não veio
pelo fluxo de pull request. O porquê, e a decisão de não reescrever a história
para esconder isso, estão no
[ADR-0004](decisoes/0004-processo-de-pull-request.md).
