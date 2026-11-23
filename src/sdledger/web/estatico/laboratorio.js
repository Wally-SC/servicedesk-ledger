// Tela do laboratório: catálogo, pedido de medição e planos lado a lado.
"use strict";

const CHAVE_DO_TOKEN = "sdledger.lab_token";

function lerTokenSalvo() {
  try { return window.localStorage.getItem(CHAVE_DO_TOKEN) || ""; } catch { return ""; }
}

function salvarToken(valor) {
  try { window.localStorage.setItem(CHAVE_DO_TOKEN, valor); } catch { /* armazenamento indisponível */ }
}

function formatarMs(valor) {
  if (valor === null || valor === undefined) return "—";
  return valor < 10 ? `${formatarDecimal(valor, 2)} ms` : `${formatarDecimal(valor, 1)} ms`;
}

function arvore(plano, indice) {
  if (!plano) return '<p class="vazio">ainda não medido</p>';
  return `<ol class="plano">${plano.map((no) => {
    const classe = no.detalhe.includes(indice) ? "usa-indice" : no.operacao.startsWith("Seq Scan") ? "varredura" : "";
    const lacos = no.lacos > 1 ? ` × ${no.lacos}` : "";
    return `<li class="${classe}" style="--nivel:${no.profundidade}">
      <span class="op">${textoSeguro(no.operacao)}</span>
      <span class="det">${textoSeguro(no.detalhe)}</span>
      <span class="met">${formatarMs(no.tempo_ms)}${lacos} · ${formatarNumero(no.linhas)} linhas · ${formatarNumero(no.blocos_em_cache)} blocos em cache</span>
    </li>`;
  }).join("")}</ol>`;
}

function resultado(experimento, execucao) {
  if (!execucao) return '<div class="resultado vazio">Nenhuma medição ainda.</div>';
  if (execucao.estado === "falhou") return `<div class="resultado falha">Falhou: ${textoSeguro(execucao.erro)}</div>`;
  if (execucao.estado !== "concluida") return `<div class="resultado">Medindo… (${textoSeguro(execucao.estado)})</div>`;
  const ganho = execucao.sem_indice_ms / Math.max(execucao.com_indice_ms, 0.001);
  const destaque = ganho >= 10 ? "forte" : ganho >= 2 ? "medio" : "fraco";
  return `
    <div class="resultado">
      <div class="numeros">
        <div><span class="rotulo">sem índice</span><strong>${formatarMs(execucao.sem_indice_ms)}</strong></div>
        <div><span class="rotulo">com índice</span><strong>${formatarMs(execucao.com_indice_ms)}</strong></div>
        <div class="ganho ${destaque}"><span class="rotulo">ganho</span><strong>${formatarDecimal(ganho, 1)}x</strong></div>
      </div>
      <p class="ambiente">${textoSeguro(execucao.ambiente || "")}</p>
      <div class="planos">
        <div><h3>Plano sem índice</h3>${arvore(execucao.plano_sem_indice, experimento.indice)}</div>
        <div><h3>Plano com índice</h3>${arvore(execucao.plano_com_indice, experimento.indice)}</div>
      </div>
    </div>`;
}

function cartao(experimento) {
  return `
    <article class="cartao experimento" id="exp-${experimento.nome}">
      <div class="experimento-topo">
        <div>
          <h2>${textoSeguro(experimento.titulo)}</h2>
          <span class="selo q4">${textoSeguro(experimento.tabela)}</span>
          <span class="selo q3">${textoSeguro(experimento.indice)}</span>
        </div>
        <button class="primario" data-experimento="${experimento.nome}">Medir</button>
      </div>
      <details>
        <summary>Consulta e índice candidato</summary>
        <div class="sql-lado-a-lado">
          <pre>${textoSeguro(experimento.consulta)}</pre>
          <pre>${textoSeguro(experimento.ddl)}</pre>
        </div>
      </details>
      <div class="area-resultado">${resultado(experimento, experimento.ultima)}</div>
    </article>`;
}

let catalogo = [];

async function acompanhar(experimento, execucaoId, botao) {
  const area = document.querySelector(`#exp-${experimento.nome} .area-resultado`);
  for (;;) {
    const execucao = await buscar(`/api/laboratorio/medicoes/${execucaoId}`);
    area.innerHTML = resultado(experimento, execucao);
    if (execucao.estado === "concluida" || execucao.estado === "falhou") break;
    await new Promise((resolver) => setTimeout(resolver, 1000));
  }
  botao.disabled = false;
}

async function medir(botao) {
  const experimento = catalogo.find((e) => e.nome === botao.dataset.experimento);
  const token = document.getElementById("token").value;
  salvarToken(token);
  botao.disabled = true;
  try {
    const execucao = await buscar("/api/laboratorio/medicoes", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Lab-Token": token },
      body: JSON.stringify({ experimento: experimento.nome, repeticoes: Number(document.getElementById("repeticoes").value) }),
    });
    avisar("");
    await acompanhar(experimento, execucao.id, botao);
  } catch (erro) {
    avisar(erro.message);
    botao.disabled = false;
  }
}

async function carregar() {
  document.getElementById("token").value = lerTokenSalvo();
  try {
    catalogo = await buscar("/api/laboratorio/experimentos");
    document.getElementById("experimentos").innerHTML = catalogo.map(cartao).join("");
    document.querySelectorAll("button[data-experimento]").forEach((botao) =>
      botao.addEventListener("click", () => medir(botao)));
  } catch (erro) {
    avisar(`Não foi possível carregar o laboratório: ${erro.message}`);
  }
}

carregar();
