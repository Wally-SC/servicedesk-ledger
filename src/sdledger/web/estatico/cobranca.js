// Tela da cobrança: receita, atraso e churn.
"use strict";

configurarGraficos();
const graficos = {};

function desenhar(id, configuracao) {
  if (graficos[id]) graficos[id].destroy();
  graficos[id] = new Chart(document.getElementById(id), configuracao);
}

function rotuloDoMes(iso) {
  const [ano, mes] = iso.split("-");
  return `${mes}/${ano.slice(2)}`;
}

function indicadores(receita, atraso, churn) {
  const ultima = receita[receita.length - 1];
  if (ultima) {
    document.getElementById("k-receita").textContent = formatarReais(ultima.receita_centavos);
    const variacao = ultima.variacao_percentual;
    document.getElementById("k-receita-nota").textContent =
      variacao === null ? rotuloDoMes(ultima.competencia)
        : `${rotuloDoMes(ultima.competencia)} · ${variacao > 0 ? "+" : ""}${variacao.toFixed(1)}% no mês`;
    document.getElementById("k-excedente").textContent =
      `${(100 * ultima.excedente_centavos / ultima.receita_centavos).toFixed(0)}%`;
    document.getElementById("k-faturas").textContent = formatarNumero(ultima.faturas);
  }
  document.getElementById("k-atraso").textContent = formatarReais(atraso.total_centavos);
  document.getElementById("k-atraso-nota").textContent =
    `${formatarNumero(atraso.faturas)} faturas de ${formatarNumero(atraso.clientes)} clientes`;
  const ultimoChurn = churn[churn.length - 1];
  if (ultimoChurn) {
    document.getElementById("k-churn").textContent =
      ultimoChurn.churn_percentual === null ? "—" : `${ultimoChurn.churn_percentual.toFixed(2)}%`;
    document.getElementById("k-churn-nota").textContent =
      `${ultimoChurn.perdidos} de ${ultimoChurn.ativos_no_mes_anterior} clientes`;
  }
}

function graficoDeReceita(receita) {
  desenhar("grafico-receita", {
    type: "bar",
    data: {
      labels: receita.map((r) => rotuloDoMes(r.competencia)),
      datasets: [
        { label: "mensalidades", data: receita.map((r) => r.mensalidades_centavos / 100), backgroundColor: CORES.verde, borderRadius: 3 },
        { label: "hora excedente", data: receita.map((r) => r.excedente_centavos / 100), backgroundColor: CORES.azul, borderRadius: 3 },
      ],
    },
    options: {
      maintainAspectRatio: false,
      scales: {
        x: { stacked: true },
        y: { stacked: true, ticks: { callback: (valor) => formatarReais(valor * 100).replace(",00", "") } },
      },
      plugins: {
        legend: { position: "bottom" },
        tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ${formatarReais(c.raw * 100)}` } },
      },
    },
  });
}

function barrasDeAtraso(atraso) {
  const faixas = [
    ["até 30 dias", atraso.ate_30_dias_centavos, CORES.ambar],
    ["31 a 90 dias", atraso.de_31_a_90_dias_centavos, CORES.vermelho],
    ["mais de 90 dias", atraso.mais_de_90_dias_centavos, "#b4234a"],
  ];
  const total = atraso.total_centavos || 1;
  document.getElementById("atraso").innerHTML = faixas.map(([rotulo, valor, cor]) => `
    <div class="barra-linha largo">
      <span class="barra-nome">${rotulo}</span>
      <div class="barra-trilho"><div class="barra-preenchida" style="width:${100 * valor / total}%;background:${cor}"></div></div>
      <span class="barra-valor">${formatarReais(valor)}</span>
    </div>`).join("");
}

function graficoDeChurn(churn) {
  desenhar("grafico-churn", {
    type: "line",
    data: {
      labels: churn.map((m) => rotuloDoMes(m.mes)),
      datasets: [{
        label: "churn %", data: churn.map((m) => m.churn_percentual),
        borderColor: CORES.ambar, backgroundColor: CORES.ambar, tension: .3, pointRadius: 3,
      }],
    },
    options: {
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true, ticks: { callback: (v) => `${v}%` } } },
      plugins: { legend: { display: false } },
    },
  });
}

async function carregar() {
  const meses = document.getElementById("meses").value;
  try {
    const [receita, atraso, churn] = await Promise.all([
      buscar(`/api/cobranca/receita?meses=${meses}`),
      buscar("/api/cobranca/atraso"),
      buscar(`/api/cobranca/churn?meses=${meses}`),
    ]);
    avisar("");
    indicadores(receita, atraso, churn);
    graficoDeReceita(receita);
    barrasDeAtraso(atraso);
    graficoDeChurn(churn);
  } catch (erro) {
    avisar(`Não foi possível carregar a cobrança: ${erro.message}`);
  }
}

document.getElementById("meses").addEventListener("change", carregar);
carregar();
