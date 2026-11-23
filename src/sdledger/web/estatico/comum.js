// Utilitários compartilhados pelas telas.
"use strict";

const CORES = {
  verde: "#3ddc84", ambar: "#f5a524", vermelho: "#f0506e", azul: "#5aa9ff",
  suave: "#8b98a5", borda: "#1f2a37", texto: "#e6edf3",
};

async function buscar(caminho, opcoes) {
  const resposta = await fetch(caminho, opcoes);
  const corpo = await resposta.json().catch(() => ({}));
  if (!resposta.ok) {
    throw new Error(corpo.erro || corpo.detail || `falha em ${caminho}: HTTP ${resposta.status}`);
  }
  return corpo;
}

function avisar(mensagem) {
  const aviso = document.getElementById("aviso");
  aviso.textContent = mensagem;
  aviso.hidden = !mensagem;
}

function formatarMinutos(minutos) {
  if (minutos === null || minutos === undefined) return "—";
  const total = Math.round(minutos);
  if (total < 60) return `${total} min`;
  const horas = Math.floor(total / 60);
  const resto = total % 60;
  return resto ? `${horas}h ${resto}min` : `${horas}h`;
}

function formatarNumero(valor) {
  return new Intl.NumberFormat("pt-BR").format(valor);
}

function formatarReais(centavos) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(centavos / 100);
}

function textoSeguro(valor) {
  const elemento = document.createElement("span");
  elemento.textContent = String(valor);
  return elemento.innerHTML;
}

function configurarGraficos() {
  if (!window.Chart) return;
  Chart.defaults.color = CORES.suave;
  Chart.defaults.borderColor = CORES.borda;
  Chart.defaults.font.family = "Inter, 'Segoe UI', system-ui, sans-serif";
  Chart.defaults.plugins.legend.labels.boxWidth = 12;
  Chart.defaults.animation = false;
}
