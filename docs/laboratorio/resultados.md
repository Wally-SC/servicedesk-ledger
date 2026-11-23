# Resultados do laboratório de índices

Cada experimento mede uma consulta pesada sem e com o índice candidato, no banco
próprio do laboratório, com o protocolo do
[ADR-0008](../decisoes/0008-protocolo-de-medicao.md).

## Ambiente

| | |
|---|---|
| Banco | PostgreSQL 16.15, `shared_buffers` padrão de 128 MB |
| Máquina | contêiner Linux com 2 vCPUs e 7 GB de RAM |
| Massa | perfil grande, semente 42, data final 2026-11-23: 300.000 chamados, 872.802 eventos, 411.256 apontamentos |
| Estado da tabela | depois de `VACUUM (ANALYZE)` |
| Protocolo | cache quente, 1 execução de aquecimento descartada, mediana de 9 execuções |

Os números abaixo foram medidos nesse ambiente, durante o desenvolvimento. Na sua
máquina eles serão outros. Para reproduzir:

```bash
make laboratorio-preparar
make laboratorio-medir
```

## Uma rodada completa

| experimento | sem índice | com índice | ganho |
|---|---:|---:|---:|
| `resolvidos_na_janela` | 18,3 ms | 6,29 ms | 2,9x |
| `backlog_em_aberto` | 19,3 ms | 0,56 ms | 34,7x |
| `historico_do_cliente` | 28,0 ms | 0,04 ms | 735,7x |
| `respostas_na_janela` | 43,9 ms | 6,12 ms | 7,2x |
| `consumo_do_mes` | 53,6 ms | 47,0 ms | 1,1x |

## Variação entre rodadas

Tempos abaixo de 10 ms oscilam bastante num ambiente de 2 vCPUs. Por isso o
número que vale é a faixa de três rodadas de nove execuções, e não a rodada mais
bonita:

| experimento | ganho, rodada 1 | rodada 2 | rodada 3 |
|---|---:|---:|---:|
| `resolvidos_na_janela` | 2,9x | 2,8x | 1,9x |
| `backlog_em_aberto` | 34,7x | 30,9x | 41,7x |
| `historico_do_cliente` | 735,7x | 865,7x | 401,3x |
| `respostas_na_janela` | 7,2x | 6,7x | 5,6x |
| `consumo_do_mes` | 1,1x | 1,0x | 1,1x |

A ordem e a grandeza são estáveis. O multiplicador exato não é.

## O que cada resultado ensina

**`historico_do_cliente` — índice na ordem da consulta.** Já existia índice em
`cliente_id`, criado por integridade. Ele acha as cerca de 61 mil linhas do
maior cliente, mas fora de ordem: o banco busca todas, ordena em paralelo e lê 4.171
blocos para devolver 50. O índice `(cliente_id, aberto_em DESC)` entrega as 50
primeiras já ordenadas e para — 53 blocos.

**`backlog_em_aberto` — índice parcial.** Menos de dois em cada cem chamados
estão em aberto. O índice `WHERE resolvido_em IS NULL` guarda só esses, é
minúsculo, e responde sem tocar no resto da tabela.

**`respostas_na_janela` — índice parcial na maior tabela.** `chamado_evento` tem
quase 900 mil linhas, e a consulta quer um tipo de evento numa janela de datas.
O índice guarda só as respostas públicas, por data.

**`resolvidos_na_janela` — ganho modesto, e por quê.** O filtro da janela
seleciona cerca de 12 mil chamados de 300 mil — 4% da tabela. O índice evita a
varredura, mas o custo que sobra é buscar essas 12 mil linhas espalhadas pela
tabela, e acima de alguns por cento o índice deixa de ser muito melhor que ler
tudo em sequência.

**`consumo_do_mes` — índice no lado errado do problema.** O planejador usa o
índice: o lado de `apontamento` cai de 36 para 20 ms. Mas a consulta precisa do
cliente de cada apontamento, e para isso continua varrendo os 300 mil chamados
inteiros na junção. O gargalo é a junção, não o filtro de data, e índice em
`apontado_em` não alcança o gargalo. Esse experimento fica no catálogo de
propósito: é o resultado que mostra que índice não é resposta automática.

## O que não foi feito

**Nenhuma view materializada.** A decisão D14 era materializar só o que a medição
mostrasse lento. Com 300 mil chamados, a consulta mais pesada do painel — a
tendência semanal — leva cerca de 875 ms, e as demais ficam entre 19 e 680 ms.
Materializar agora seria pagar o custo de atualizar a view sem um problema medido
que o justificasse.

**Cache frio.** Todos os números são de cache quente, e estão declarados assim.
Medir cache frio exigiria reiniciar o PostgreSQL e limpar o cache do sistema
operacional entre execuções, o que o laboratório não faz.
