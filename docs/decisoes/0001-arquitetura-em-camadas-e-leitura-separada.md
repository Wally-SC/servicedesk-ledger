# ADR-0001 — Arquitetura em camadas com leitura separada da escrita

**Data:** 2026-11-23 · **Status:** aceita

## Contexto

O projeto tem duas naturezas no mesmo banco. A escrita é transacional e cheia de
invariante: abrir chamado, registrar primeira resposta, apontar horas, fechar
ciclo de faturamento. A leitura é analítica e agregada: percentis de primeira
resposta e resolução, backlog por prioridade e faixa de idade, taxa de
cumprimento de SLA, tendência semanal, ranking de clientes.

A restrição que define o projeto é que **todo cálculo analítico é feito em SQL**.
A outra restrição é arquitetura em camadas com dependências apontando para dentro.
As duas entram em conflito direto na leitura.

## Opções consideradas

### A — Tudo pelo repositório e pela entidade

Toda leitura carrega entidades de domínio por um repositório e agrega em Python.

- **A favor:** uma única forma de acessar dados; o domínio é o único vocabulário.
- **Contra:** materializar centenas de milhares de chamados para calcular um p95
  é o oposto do que o projeto quer demonstrar; o SQL fica escondido dentro do
  repositório; aparece muito mapeamento sem valor.

### B — CQRS-lite: escrita pelo domínio, leitura por consulta dedicada

A escrita passa por caso de uso, entidade e repositório. A leitura analítica vai
do arquivo `.sql` direto para um DTO declarado em `application/consultas`, por
uma porta que a infraestrutura implementa.

- **A favor:** o SQL fica visível e revisável, que é o ponto do projeto; a
  consulta pesada roda no banco; a regra de dependência continua valendo, porque
  a rota depende da porta e não do SQL.
- **Contra:** dois caminhos para explicar em vez de um; o DTO de leitura duplica
  nomes que também existem no domínio; exige disciplina para não começar a
  escrever pelo caminho de leitura.

## O que a IA sugeriu

Recomendou a opção B, com o argumento de que o conflito não é defeito do escopo
e sim uma decisão que precisa ser tomada e registrada: um revisor que encontre
consulta analítica fora do domínio sem explicação vai ler como "ele quebrou a
própria arquitetura", enquanto a mesma estrutura com a decisão escrita vira
resposta de entrevista. Apontou também que a opção A produz mapeamento inútil e
esconde justamente a parte que o projeto quer exibir.

## O que eu decidi e por quê

Decidi pela opção B, concordando com a recomendação sem contraproposta. O projeto
existe para mostrar proficiência em SQL e em engenharia de software ao mesmo
tempo; a opção A sacrificaria a primeira para parecer mais pura na segunda.

## O que a IA errou ou eu corrigi

Nada neste registro até o momento. Esta seção é atualizada se algo aparecer na
implementação das consultas.

## Consequências

- `application/consultas` passa a existir com DTOs que não são entidades, e isso
  precisa estar claro para quem lê o código pela primeira vez.
- Nenhuma escrita pode usar o caminho de leitura. Se isso acontecer, a invariante
  escapa do domínio e o teste de arquitetura não pega — é revisão de PR que pega.
- **Reversão:** trocar as implementações das portas de consulta por repositórios
  que devolvem entidades. As rotas não mudam, porque dependem da porta. O custo
  real não é técnico: é perder o motivo de o projeto existir.
