// Tela do painel: busca as cinco consultas e desenha.
"use strict";

configurarGraficos();
const graficos = {};

function desenhar(id, configuracao) {
  if (graficos[id]) graficos[id].destroy();
  graficos[id] = new Chart(document.getElementById(id), configuracao);
}

function indicadores(percentis, sla) {
  document.getElementById("k-resolvidos").textContent = formatarNumero(percentis.resolvidos);
  document.getElementById("k-resp-p50").textContent = formatarMinutos(percentis.resposta_p50);
  document.getElementById("k-resp-p95").textContent = `p95 ${formatarMinutos(percentis.resposta_p95)}`;
  document.getElementById("k-res-p50").textContent = formatarMinutos(percentis.resolucao_p50);
  document.getElementById("k-res-p95").textContent = `p95 ${formatarMinutos(percentis.resolucao_p95)}`;
  document.getElementById("k-sem-resposta").textContent = formatarNumero(percentis.sem_primeira_resposta);

  const entregues = sla.reduce((soma, linha) => soma + linha.entregues, 0);
  const noPrazo = sla.reduce((soma, linha) => soma + linha.dentro_do_prazo, 0);
  document.getElementById("k-sla").textContent =
    entregues ? formatarPercentual(100 * noPrazo / entregues) : "—";
}

function barrasDeSla(sla) {
  const alvo = document.getElementById("sla");
  alvo.innerHTML = sla.map((linha) => {
    const cor = linha.taxa_percentual >= 95 ? CORES.verde : linha.taxa_percentual >= 80 ? CORES.ambar : CORES.vermelho;
    return `
      <div class="barra-linha">
        <span class="barra-nome">${textoSeguro(nomeDaPrioridade(linha.prioridade))}</span>
        <div class="barra-trilho"><div class="barra-preenchida" style="width:${linha.taxa_percentual}%;background:${cor}"></div></div>
        <span class="barra-valor">${formatarPercentual(linha.taxa_percentual)}</span>
        <span class="barra-sub">${formatarNumero(linha.dentro_do_prazo)} de ${formatarNumero(linha.entregues)} no prazo</span>
      </div>`;
  }).join("");
}

function graficoDeBacklog(backlog) {
  const faixas = [
    ["ate_1_dia", "até 1 dia", CORES.verde],
    ["de_1_a_3_dias", "1 a 3 dias", CORES.azul],
    ["de_3_a_7_dias", "3 a 7 dias", CORES.ambar],
    ["mais_de_7_dias", "mais de 7 dias", CORES.vermelho],
  ];
  desenhar("grafico-backlog", {
    type: "bar",
    data: {
      labels: backlog.map((linha) => nomeDaPrioridade(linha.prioridade)),
      datasets: faixas.map(([campo, rotulo, cor]) => ({
        label: rotulo, data: backlog.map((linha) => linha[campo]), backgroundColor: cor, borderRadius: 3,
      })),
    },
    options: {
      maintainAspectRatio: false, indexAxis: "y",
      scales: { x: { stacked: true }, y: { stacked: true } },
      plugins: { legend: { position: "bottom" } },
    },
  });
}

function graficoDeTendencia(semanas) {
  desenhar("grafico-tendencia", {
    data: {
      labels: semanas.map((s) => s.semana.split("-").reverse().slice(0, 2).join("/")),
      datasets: [
        {
          type: "line", label: "p95 de resolução (min úteis)", yAxisID: "minutos",
          data: semanas.map((s) => s.resolucao_p95), borderColor: CORES.verde,
          backgroundColor: CORES.verde, tension: .3, pointRadius: 3,
        },
        {
          type: "bar", label: "resolvidos", yAxisID: "quantidade",
          data: semanas.map((s) => s.resolvidos), backgroundColor: "rgba(90,169,255,.35)", borderRadius: 3,
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      scales: {
        minutos: { position: "left", beginAtZero: true },
        quantidade: { position: "right", beginAtZero: true, grid: { drawOnChartArea: false } },
      },
      plugins: { legend: { position: "bottom" } },
    },
  });
}

function ranking(clientes) {
  document.getElementById("ranking").innerHTML = clientes.map((c) => `
    <tr>
      <td>${c.posicao}</td>
      <td>${textoSeguro(c.nome)}</td>
      <td class="num">${formatarNumero(c.chamados)}</td>
      <td class="num">${formatarNumero(c.em_aberto)}</td>
      <td class="num">${formatarNumero(c.prioritarios)}</td>
      <td class="num">${formatarDecimal(c.idade_maxima_dias)} d</td>
      <td><span class="selo q${c.quartil}">Q${c.quartil}</span></td>
    </tr>`).join("");
}

async function carregar() {
  const dias = document.getElementById("janela").value;
  try {
    const [percentis, sla, backlog, tendencia, clientes] = await Promise.all([
      buscar(`/api/painel/percentis?dias=${dias}`),
      buscar(`/api/painel/sla?dias=${dias}`),
      buscar("/api/painel/backlog"),
      buscar("/api/painel/tendencia?semanas=12"),
      buscar(`/api/painel/clientes?dias=${dias}&limite=8`),
    ]);
    avisar("");
    indicadores(percentis, sla);
    barrasDeSla(sla);
    graficoDeBacklog(backlog);
    graficoDeTendencia(tendencia);
    ranking(clientes);
    document.getElementById("atualizado").textContent =
      `atualizado às ${new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}`;
  } catch (erro) {
    avisar(`Não foi possível carregar o painel: ${erro.message}`);
  }
}

document.getElementById("janela").addEventListener("change", carregar);
carregar();
