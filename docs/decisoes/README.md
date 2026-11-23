# Registros de decisão

Um arquivo por decisão relevante, numerado, escrito no mesmo pull request que
implementa a decisão. Cada registro tem contexto, opções consideradas com prós e
contras, o que a IA sugeriu, o que eu decidi e por quê, o que deu errado no
caminho e as consequências, incluindo como reverter.

Decisão que não aconteceu não vira registro. Seção sem conteúdo real fica escrita
como "nada até o momento", e não preenchida com texto genérico.

| # | Decisão | Status |
|---|---------|--------|
| [0001](0001-arquitetura-em-camadas-e-leitura-separada.md) | Arquitetura em camadas com leitura separada da escrita | aceita |
| [0002](0002-acesso-a-dados-sem-orm.md) | Acesso a dados com psycopg3 e SQL em arquivo, sem ORM | aceita |
| [0003](0003-tipagem-estrita-e-teste-de-arquitetura.md) | Tipagem estrita e teste de arquitetura desde o primeiro commit | aceita |
| [0004](0004-processo-de-pull-request.md) | Processo de pull request trabalhando sozinho | aceita |
| [0005](0005-definicao-das-metricas.md) | Denominador dos percentis e definição das métricas | aceita |

O método de trabalho com a IA está em [../uso-de-ia.md](../uso-de-ia.md).
