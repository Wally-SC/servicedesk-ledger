"""Gerador de massa fictícia.

Reproduzível: mesma semente e mesma data final produzem exatamente o mesmo
banco. A data final é parâmetro porque o painel olha os últimos dias — fixá-la
no código deixaria a demonstração velha em uma semana.

A função não faz commit. Quem chama decide, e é isso que permite ao teste de
integração gerar massa dentro de uma transação desfeita no fim.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

import psycopg

from sdledger.infrastructure.massa.perfis import Perfil

FUSO = timezone(timedelta(hours=-3))

TABELAS_DE_DADOS = (
    "fatura_item",
    "fatura",
    "ciclo_faturamento",
    "apontamento",
    "chamado_periodo_estado",
    "chamado_evento",
    "chamado",
    "contrato",
    "politica_sla",
    "agente",
    "plano",
    "cliente",
    "feriado",
)

PLANOS = (
    # nome, franquia em minutos, mensalidade, preço da hora excedente
    ("Essencial", 600, 49_900, 18_000),
    ("Pro", 1_800, 129_900, 15_000),
    ("Enterprise", 6_000, 349_900, 12_000),
)

PRIORIDADES = ("baixa", "media", "alta", "critica")
PESO_PRIORIDADE = (0.40, 0.35, 0.20, 0.05)

# minutos úteis de prazo por prioridade: primeira resposta e resolução
PRAZOS = {
    "baixa": (480, 4_800),
    "media": (240, 2_400),
    "alta": (60, 960),
    "critica": (30, 240),
}

FERIADOS = (
    ("2025-09-07", "Independência"),
    ("2025-10-12", "Nossa Senhora Aparecida"),
    ("2025-11-02", "Finados"),
    ("2025-11-15", "Proclamação da República"),
    ("2025-12-25", "Natal"),
    ("2026-01-01", "Confraternização Universal"),
    ("2026-02-17", "Carnaval"),
    ("2026-04-03", "Sexta-feira Santa"),
    ("2026-04-21", "Tiradentes"),
    ("2026-05-01", "Dia do Trabalho"),
    ("2026-09-07", "Independência"),
    ("2026-10-12", "Nossa Senhora Aparecida"),
    ("2026-11-02", "Finados"),
    ("2026-11-15", "Proclamação da República"),
)

# Chance de o dia da semana receber um chamado, relativa à segunda-feira.
PESO_DIA = (1.0, 1.0, 1.0, 1.0, 0.9, 0.15, 0.08)  # segunda a domingo

ASSUNTOS = (
    "Impressora não responde",
    "Lentidão no sistema",
    "Erro ao emitir nota",
    "Acesso bloqueado",
    "Backup não concluiu",
    "Integração fora do ar",
    "Solicitação de novo usuário",
    "Dúvida sobre relatório",
)


@dataclass(frozen=True)
class Resumo:
    """O que foi gerado, para o chamador relatar."""

    clientes: int
    agentes: int
    chamados: int
    eventos: int
    periodos: int
    apontamentos: int


def _sorteia_dia(rng: random.Random, inicio: date, dias: int) -> date:
    """Sorteia um dia com peso por dia da semana, para a fila ter sazonalidade."""
    while True:
        dia = inicio + timedelta(days=rng.randrange(dias))
        if rng.random() < PESO_DIA[dia.weekday()]:
            return dia


def _sorteia_abertura(rng: random.Random, dia: date) -> datetime:
    """Hora de abertura concentrada no expediente, com uma cauda fora dele."""
    dentro_do_expediente = rng.random() < 0.85
    hora = rng.randrange(9, 18) if dentro_do_expediente else rng.choice([7, 8, 18, 19, 20, 21])
    return datetime.combine(dia, time(hora, rng.randrange(60), rng.randrange(60)), FUSO)


def _atraso(rng: random.Random, mediana_min: float, sigma: float, teto_min: float) -> float:
    """Atraso lognormal: mediana baixa com cauda longa, como fila de suporte."""
    import math

    valor = rng.lognormvariate(math.log(mediana_min), sigma)
    return min(valor, teto_min)


def limpar(conexao: psycopg.Connection) -> None:
    """Esvazia as tabelas de dados, preservando o expediente da migração."""
    # A lista de tabelas é constante do módulo, não vem de fora.
    conexao.execute(f"TRUNCATE {', '.join(TABELAS_DE_DADOS)} RESTART IDENTITY CASCADE")


def gerar(conexao: psycopg.Connection, perfil: Perfil, semente: int, fim: date) -> Resumo:
    """Gera a massa do perfil. Não faz commit."""
    rng = random.Random(semente)
    limpar(conexao)

    inicio = fim - timedelta(days=perfil.meses * 30)
    dias = (fim - inicio).days

    saidas = _catalogo(conexao, rng, perfil, inicio, fim)
    return _chamados(conexao, rng, perfil, inicio, dias, fim, saidas)


def _catalogo(
    conexao: psycopg.Connection, rng: random.Random, perfil: Perfil, inicio: date, fim: date
) -> dict[int, date]:
    """Feriados, planos, políticas de SLA, agentes, clientes e contratos.

    Devolve o dia em que cada cliente que cancelou deixou de ter contrato.
    """
    with conexao.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO feriado (dia, descricao) VALUES (%s, %s)",
            [
                (dia, descricao)
                for dia, descricao in FERIADOS
                if inicio <= date.fromisoformat(dia) <= fim
            ],
        )

        for nome, franquia, mensalidade, excedente in PLANOS:
            cursor.execute(
                """
                INSERT INTO plano (nome, franquia_minutos, mensalidade_centavos,
                                   preco_hora_excedente_centavos)
                VALUES (%s, %s, %s, %s)
                """,
                (nome, franquia, mensalidade, excedente),
            )

        # O plano Pro muda de prazo no meio da janela: é o que faz a vigência da
        # política de SLA valer alguma coisa nos dados, e não só no esquema.
        virada = inicio + timedelta(days=(fim - inicio).days // 2)
        for plano_id, (nome, *_) in enumerate(PLANOS, start=1):
            for prioridade in PRIORIDADES:
                resposta, resolucao = PRAZOS[prioridade]
                if nome == "Pro":
                    cursor.execute(
                        """
                        INSERT INTO politica_sla (plano_id, prioridade,
                            minutos_uteis_primeira_resposta, minutos_uteis_resolucao, vigencia)
                        VALUES (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s)
                        """,
                        (
                            plano_id,
                            prioridade,
                            resposta * 2,
                            resolucao * 2,
                            f"[{inicio},{virada})",
                            plano_id,
                            prioridade,
                            resposta,
                            resolucao,
                            f"[{virada},{fim + timedelta(days=365)})",
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO politica_sla (plano_id, prioridade,
                            minutos_uteis_primeira_resposta, minutos_uteis_resolucao, vigencia)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            plano_id,
                            prioridade,
                            resposta,
                            resolucao,
                            f"[{inicio},{fim + timedelta(days=365)})",
                        ),
                    )

        cursor.executemany(
            "INSERT INTO agente (nome) VALUES (%s)",
            [(f"Agente {n:03d}",) for n in range(1, perfil.agentes + 1)],
        )

        cursor.executemany(
            "INSERT INTO cliente (nome, documento) VALUES (%s, %s)",
            [(f"Cliente {n:04d}", f"{n:014d}") for n in range(1, perfil.clientes + 1)],
        )

        # Parte dos clientes cancela no meio da janela e não volta. Sem isso o
        # churn do painel de cobrança seria sempre zero. A quantidade é fixa,
        # não sorteada, para o perfil pequeno também ter pelo menos um caso.
        quantos_saem = max(1, round(perfil.clientes * 0.12))
        saem = set(rng.sample(range(1, perfil.clientes + 1), quantos_saem))
        saidas: dict[int, date] = {}

        # Um contrato por cliente; parte deles troca de plano no meio da janela,
        # com períodos colados, que é o caso que a constraint de exclusão aceita.
        for cliente_id in range(1, perfil.clientes + 1):
            plano_id = rng.randrange(1, len(PLANOS) + 1)
            if cliente_id in saem:
                saida = inicio + timedelta(
                    days=rng.randrange(90, max(91, (fim - inicio).days - 20))
                )
                saidas[cliente_id] = saida
                cursor.execute(
                    "INSERT INTO contrato (cliente_id, plano_id, vigencia) VALUES (%s, %s, %s)",
                    (cliente_id, plano_id, f"[{inicio},{saida})"),
                )
            elif rng.random() < 0.2:
                troca = inicio + timedelta(
                    days=rng.randrange(60, max(61, (fim - inicio).days - 30))
                )
                outro = 1 + (plano_id % len(PLANOS))
                cursor.execute(
                    "INSERT INTO contrato (cliente_id, plano_id, vigencia) VALUES (%s, %s, %s)",
                    (cliente_id, plano_id, f"[{inicio},{troca})"),
                )
                cursor.execute(
                    "INSERT INTO contrato (cliente_id, plano_id, vigencia) VALUES (%s, %s, %s)",
                    (cliente_id, outro, f"[{troca},{fim + timedelta(days=365)})"),
                )
            else:
                cursor.execute(
                    "INSERT INTO contrato (cliente_id, plano_id, vigencia) VALUES (%s, %s, %s)",
                    (cliente_id, plano_id, f"[{inicio},{fim + timedelta(days=365)})"),
                )

    return saidas


def _sorteia_clientes(rng: random.Random, clientes: int, quantidade: int) -> list[int]:
    """Distribui os chamados entre os clientes com cauda do tipo Zipf.

    Poucos clientes concentram muito chamado, que é como fila de suporte se
    comporta. Sem essa assimetria o ranking de clientes críticos do painel vira
    uma lista sem ordem interessante.

    O sorteio é feito de uma vez, com pesos acumulados calculados uma única vez:
    chamar `choices` por chamado recalcularia a soma dos pesos trezentas mil
    vezes.
    """
    pesos = [1.0 / (posicao**1.1) for posicao in range(1, clientes + 1)]
    acumulados: list[float] = []
    total = 0.0
    for peso in pesos:
        total += peso
        acumulados.append(total)
    return rng.choices(range(1, clientes + 1), cum_weights=acumulados, k=quantidade)


def _chamados(
    conexao: psycopg.Connection,
    rng: random.Random,
    perfil: Perfil,
    inicio: date,
    dias: int,
    fim: date,
    saidas: dict[int, date],
) -> Resumo:
    """Gera chamados, eventos, períodos de estado e apontamentos via COPY."""
    limite = datetime.combine(fim, time(23, 59), FUSO)

    linhas_chamado: list[tuple[object, ...]] = []
    linhas_evento: list[tuple[object, ...]] = []
    linhas_periodo: list[tuple[object, ...]] = []
    linhas_apontamento: list[tuple[object, ...]] = []

    clientes_sorteados = _sorteia_clientes(rng, perfil.clientes, perfil.chamados)

    for indice in range(perfil.chamados):
        chamado_id = indice + 1
        cliente_id = clientes_sorteados[indice]
        responsavel = rng.randrange(1, perfil.agentes + 1)
        prioridade = rng.choices(PRIORIDADES, weights=PESO_PRIORIDADE)[0]
        dia = _sorteia_dia(rng, inicio, dias)
        if cliente_id in saidas and dia >= saidas[cliente_id]:
            # cliente que cancelou não abre chamado depois de sair
            dia = _sorteia_dia(rng, inicio, (saidas[cliente_id] - inicio).days)
        abertura = _sorteia_abertura(rng, dia)

        respondido: datetime | None = None
        if rng.random() < 0.92:
            candidato = abertura + timedelta(minutes=_atraso(rng, 40, 1.5, 60 * 24 * 10))
            if candidato < limite:
                respondido = candidato

        resolvido: datetime | None = None
        if respondido is not None and rng.random() < 0.93:
            candidato = respondido + timedelta(minutes=_atraso(rng, 360, 1.8, 60 * 24 * 45))
            if candidato < limite:
                resolvido = candidato

        # Chamado antigo não fica parado para sempre: ou foi resolvido, ou foi
        # encerrado sem resposta pública — duplicado, trote, resolvido por fora.
        # Sem isto o backlog acumularia chamados de centenas de dias e a métrica
        # de "sem primeira resposta" nunca teria um caso, embora exista.
        if resolvido is None and abertura < limite - timedelta(days=45):
            candidato = abertura + timedelta(minutes=_atraso(rng, 2_880, 1.0, 60 * 24 * 40))
            resolvido = min(candidato, limite - timedelta(days=1))

        estado = "resolvido" if resolvido else ("em_atendimento" if respondido else "aberto")
        linhas_chamado.append(
            (
                cliente_id,
                responsavel,
                prioridade,
                estado,
                rng.choice(ASSUNTOS),
                abertura,
                respondido,
                resolvido,
            )
        )

        linhas_evento.append((chamado_id, "abertura", None, abertura))
        if respondido is not None:
            linhas_evento.append((chamado_id, "resposta_publica", responsavel, respondido))
        if resolvido is not None:
            autor = responsavel if respondido is not None else None
            linhas_evento.append((chamado_id, "resolucao", autor, resolvido))

        primeiro_fim = respondido or resolvido or limite
        if primeiro_fim > abertura:
            linhas_periodo.append((chamado_id, "aberto", f"[{abertura},{primeiro_fim})"))
        if respondido is not None:
            fim_atendimento = resolvido or limite
            if fim_atendimento > respondido:
                estado_periodo = "em_atendimento"
                linhas_periodo.append(
                    (chamado_id, estado_periodo, f"[{respondido},{fim_atendimento})")
                )

        # Um ou dois lançamentos de 10 a 60 minutos: perto de uma hora por
        # chamado, que é o que suporte de verdade gasta. A primeira versão
        # lançava até três blocos de três horas e a receita da massa grande
        # passava de R$ 100 milhões.
        if resolvido is not None and respondido is not None:
            for _ in range(rng.randrange(1, 3)):
                linhas_apontamento.append(
                    (chamado_id, responsavel, rng.randrange(10, 61), resolvido)
                )

    _copiar(
        conexao,
        "chamado",
        "cliente_id, responsavel_id, prioridade, estado, assunto, aberto_em,"
        " primeira_resposta_em, resolvido_em",
        linhas_chamado,
    )
    _copiar(
        conexao, "chamado_evento", "chamado_id, tipo, autor_agente_id, ocorrido_em", linhas_evento
    )
    _copiar(conexao, "chamado_periodo_estado", "chamado_id, estado, periodo", linhas_periodo)
    _copiar(
        conexao, "apontamento", "chamado_id, agente_id, minutos, apontado_em", linhas_apontamento
    )

    return Resumo(
        clientes=perfil.clientes,
        agentes=perfil.agentes,
        chamados=len(linhas_chamado),
        eventos=len(linhas_evento),
        periodos=len(linhas_periodo),
        apontamentos=len(linhas_apontamento),
    )


def _copiar(
    conexao: psycopg.Connection, tabela: str, colunas: str, linhas: list[tuple[object, ...]]
) -> None:
    """Carga em massa por COPY.

    INSERT linha a linha levaria minutos no perfil grande; COPY leva segundos.
    Como as tabelas foram truncadas com RESTART IDENTITY, os ids saem em
    sequência na ordem da carga, e é por isso que o chamado de índice i tem id
    i+1 — relação que os eventos e os períodos usam.
    """
    if not linhas:
        return
    # Tabela e colunas vêm de chamadas internas deste módulo, nunca de entrada
    # do usuário: COPY não aceita parâmetro no nome do destino.
    with (
        conexao.cursor() as cursor,
        cursor.copy(f"COPY {tabela} ({colunas}) FROM STDIN") as copia,
    ):
        for linha in linhas:
            copia.write_row(linha)
