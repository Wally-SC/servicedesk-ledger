# ADR-0007 — Regras de fechamento do ciclo de faturamento

**Data:** 2026-11-23 · **Status:** aceita

## Contexto

O escopo dizia "o sistema fecha o ciclo, gera faturas, calcula horas excedentes e
marca atrasos", mas não dizia como resolver os casos que mudam o valor da fatura:
cliente que troca de plano no meio do mês, cliente que sai no meio do mês,
apontamento feito na virada do mês, e o que acontece quando o fechamento roda
duas vezes.

## Opções consideradas

### Plano cobrado quando há troca no mês

- **A — plano vigente no primeiro dia.** Simples, mas cobra o plano antigo de
  quem já migrou e está consumindo a franquia nova.
- **B — proporcional aos dias de cada plano.** Mais justo, mas a franquia também
  teria de ser rateada, e a conta de excedente passa a depender de qual minuto
  caiu em qual plano.
- **C — plano mais recente dentro da competência.** Quem trocou paga o plano
  novo no mês inteiro; quem saiu paga o mês em que teve contrato.

### Fechamento repetido

- **A — falhar se já existe ciclo.** Seguro, mas quem repete depois de uma queda
  no meio precisa limpar à mão o que já foi emitido.
- **B — pular cliente já fechado.** Idempotente: rodar de novo emite só o que
  faltou.

## O que a IA sugeriu

Plano mais recente dentro da competência, consumo medido pela data do
apontamento no fuso de São Paulo, emissão no primeiro dia do mês seguinte às 9h,
vencimento no dia 10, e fechamento idempotente pulando cliente já fechado. O
argumento central foi que fechamento é a operação que alguém repete depois de
uma falha, então ela precisa ser segura de repetir.

## O que eu decidi e por quê

Essas regras foram tomadas pela IA dentro da delegação que eu dei para o lote
final ("finalize o projeto"), e não houve deliberação específica minha sobre
cada uma. Registro assim, em vez de inventar uma discussão. Revisei o resultado
e mantive as regras: elas são simples de explicar e cada uma está coberta por
teste.

## O que a IA errou ou eu corrigi

1. **A massa não tinha cliente saindo.** Todo contrato ia até depois da data
   final, então o churn do painel de cobrança sairia sempre zero. Percebido ao
   desenhar a consulta de churn, antes de rodar: a massa passou a encerrar o
   contrato de 12% dos clientes, e cliente que saiu não abre chamado depois.

2. **A receita da massa grande passou de R$ 107 milhões.** O gerador lançava de
   um a três apontamentos de até três horas por chamado — quase quatro horas por
   atendimento. Medido no banco, corrigido para um ou dois lançamentos de 10 a 60
   minutos: 52 minutos por chamado, fatura mediana de R$ 2.434.

## Consequências

- Cliente que troca de plano no fim do mês paga o plano novo no mês inteiro. É
  uma simplificação consciente, e a reversão é trocar a ordenação de uma consulta
  no repositório.
- Apontamento às 00h30 do dia 1º em São Paulo é do mês novo, e há teste para isso.
- O pagamento na massa é simulado (78% em dia, 12% atrasado, 10% não paga) e
  nunca acontece depois da data final: a massa descreve o passado.
