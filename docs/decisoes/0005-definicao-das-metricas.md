# ADR-0005 — Denominador dos percentis e definição das métricas

**Data:** 2026-11-23 · **Status:** aceita

## Contexto

O painel exibe p50, p90 e p95 de primeira resposta e de resolução. Antes de
escrever uma linha de SQL é preciso decidir sobre qual conjunto esses percentis
são calculados, porque a escolha muda o número e não há como inferi-la olhando o
gráfico.

## Opções consideradas

### A — Chamados abertos dentro da janela

Percentil sobre os chamados cuja data de **abertura** cai na janela.

- **A favor:** a coorte é estável; comparar janelas compara os mesmos chamados.
- **Contra:** os chamados lentos da janela ainda não resolveram quando a consulta
  roda, então ou ficam de fora — e o percentil sai otimista justamente onde dói —
  ou entram como "em aberto" e exigem decidir o que fazer com eles. Na prática a
  métrica melhora sozinha perto da borda da janela.

### B — Chamados resolvidos dentro da janela

Percentil sobre os chamados cuja data de **resolução** cai na janela.

- **A favor:** mede o que foi efetivamente entregue no período; nenhum chamado
  fica pendurado; é o denominador usado em relatório de SLA de contrato.
- **Contra:** um chamado antigo e muito lento, resolvido hoje, pesa na janela de
  hoje; a coorte muda entre janelas.

## O que a IA sugeriu

Recomendou a opção B, apontando que a opção A tem um viés que piora perto da
borda — os lentos ainda não terminaram — e que isso faz a métrica parecer melhor
exatamente quando é mais consultada. Sugeriu também escrever o glossário inteiro
antes das consultas, para que cada `.sql` nasça com a pergunta de negócio já
definida.

## O que eu decidi e por quê

Opção B. O painel responde "quanto da minha fila está atrasada e como estou
entregando", e entrega se mede pelo que foi resolvido.

Três definições derivadas foram decididas junto:

- Chamado sem nenhuma resposta pública fica **fora** do percentil de primeira
  resposta e aparece como contagem própria. Diluir o pior caso dentro do p95
  esconde justamente o caso que o painel deveria denunciar.
- Reabertura conta até a última resolução, e o chamado aparece uma vez só.
- Backlog usa **dias corridos**, não horas úteis, por ser leitura de fila. É a
  única exceção à regra de horas úteis, e está marcada no glossário.

## O que a IA errou ou eu corrigi

Nada neste registro até o momento. As definições ainda não encontraram os dados:
este registro deve ser revisitado quando as consultas rodarem contra a massa
fictícia, porque é ali que definição frágil aparece.

## Consequências

- A comparação entre duas janelas não compara a mesma coorte de chamados. Quem
  lê o painel precisa saber disso, e o glossário diz.
- Um chamado muito antigo resolvido hoje desloca o p95 de hoje. É o
  comportamento esperado e não será suavizado.
- **Reversão:** trocar o denominador é mudar a cláusula de janela de duas
  consultas. O custo não é técnico: é que toda a série histórica passa a medir
  outra coisa, então a troca exige refazer os números divulgados.
