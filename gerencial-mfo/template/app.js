/* Gerencial MFO — comportamento do dashboard.
   Seis coisas, e nada mais: navegar entre as abas, filtrar, ordenar, abrir
   o detalhe de uma linha (uma a uma ou todas), alternar entre versões de um
   mesmo gráfico e exibir o tooltip dos gráficos. Os números já vêm
   calculados do build; nada aqui recalcula valor de negócio.

   Restrições do projeto: precisa rodar dentro de um <iframe>, então nada de
   window.top, e nada de localStorage — o estado vive em memória. */
(function () {
  "use strict";

  var doc = document;

  /* ------------------------------------------------------------ navegação */

  var paginas = Array.prototype.slice.call(doc.querySelectorAll("[data-pagina]"));
  var itens = Array.prototype.slice.call(doc.querySelectorAll("[data-vai-para]"));
  var titulo = doc.querySelector("[data-titulo-pagina]");

  function mostrar(identificador) {
    paginas.forEach(function (pagina) {
      pagina.hidden = pagina.getAttribute("data-pagina") !== identificador;
    });
    itens.forEach(function (item) {
      var ativo = item.getAttribute("data-vai-para") === identificador;
      if (ativo) {
        item.setAttribute("aria-current", "page");
        if (titulo) titulo.textContent = item.getAttribute("data-titulo") || item.textContent;
      } else {
        item.removeAttribute("aria-current");
      }
    });
    var principal = doc.querySelector(".g5-main");
    if (principal) principal.scrollTop = 0;
    window.scrollTo(0, 0);
  }

  itens.forEach(function (item) {
    item.addEventListener("click", function () {
      mostrar(item.getAttribute("data-vai-para"));
    });
  });

  /* -------------------------------------------------------------- filtro */

  doc.addEventListener("input", function (evento) {
    var campo = evento.target;
    if (!campo.hasAttribute || !campo.hasAttribute("data-filtra")) return;

    var alvo = doc.getElementById(campo.getAttribute("data-filtra"));
    if (!alvo) return;

    var termo = campo.value.trim().toLowerCase();
    var visiveis = 0;
    var linhas = alvo.tBodies[0] ? alvo.tBodies[0].rows : [];

    Array.prototype.forEach.call(linhas, function (linha) {
      if (linha.hasAttribute("data-detalhe")) return;
      var casa = !termo || linha.textContent.toLowerCase().indexOf(termo) !== -1;
      linha.hidden = !casa;
      if (casa) visiveis++;
    });

    var contador = doc.querySelector('[data-contador="' + campo.getAttribute("data-filtra") + '"]');
    if (contador) contador.textContent = termo ? visiveis + " linha(s)" : "";
  });

  /* ------------------------------------------------------------ ordenação */

  function valorDaCelula(linha, indice) {
    var celula = linha.cells[indice];
    if (!celula) return "";
    var cru = celula.getAttribute("data-valor");
    return cru !== null ? parseFloat(cru) : celula.textContent.trim();
  }

  doc.addEventListener("click", function (evento) {
    var cabecalho = evento.target.closest ? evento.target.closest("th[data-ordena]") : null;
    if (!cabecalho) return;

    var tabela = cabecalho.closest("table");
    var corpo = tabela.tBodies[0];
    if (!corpo) return;

    var indice = Array.prototype.indexOf.call(cabecalho.parentNode.cells, cabecalho);
    var numerica = cabecalho.getAttribute("data-ordena") === "numero";
    var descendente = cabecalho.getAttribute("aria-sort") !== "descending";

    Array.prototype.forEach.call(tabela.tHead.rows[0].cells, function (celula) {
      celula.removeAttribute("aria-sort");
    });
    cabecalho.setAttribute("aria-sort", descendente ? "descending" : "ascending");

    /* Linhas de total e de detalhe não entram na ordenação: total fica ao pé
       da tabela e detalhe acompanha o pai. */
    var linhas = Array.prototype.filter.call(corpo.rows, function (linha) {
      return !linha.classList.contains("total") && !linha.hasAttribute("data-detalhe");
    });
    var fixas = Array.prototype.filter.call(corpo.rows, function (linha) {
      return linha.classList.contains("total");
    });
    var detalhes = {};
    Array.prototype.forEach.call(corpo.rows, function (linha) {
      var alvo = linha.getAttribute("data-detalhe");
      if (!alvo) return;
      (detalhes[alvo] = detalhes[alvo] || []).push(linha);
    });

    linhas.sort(function (a, b) {
      var va = valorDaCelula(a, indice);
      var vb = valorDaCelula(b, indice);
      if (numerica) {
        va = isNaN(va) ? -Infinity : va;
        vb = isNaN(vb) ? -Infinity : vb;
        return descendente ? vb - va : va - vb;
      }
      return descendente
        ? String(vb).localeCompare(String(va), "pt-BR")
        : String(va).localeCompare(String(vb), "pt-BR");
    });

    linhas.forEach(function (linha) {
      corpo.appendChild(linha);
      var alvo = linha.getAttribute("data-abre");
      if (alvo && detalhes[alvo]) {
        detalhes[alvo].forEach(function (filha) {
          corpo.appendChild(filha);
        });
      }
    });
    fixas.forEach(function (linha) {
      corpo.appendChild(linha);
    });
  });

  /* ----------------------------------------------------------- drill-down */

  function definirDetalhe(linha, abrir) {
    var alvo = linha.getAttribute("data-abre");
    linha.setAttribute("aria-expanded", abrir ? "true" : "false");
    Array.prototype.forEach.call(
      doc.querySelectorAll('[data-detalhe="' + alvo + '"]'),
      function (filha) {
        filha.hidden = !abrir;
      }
    );
  }

  /* O botão "Expandir tudo" reflete o estado da tabela: com tudo aberto ele
     vira "Recolher tudo", não importa se o leitor abriu linha a linha. */
  function sincronizarBotao(tabela) {
    if (!tabela || !tabela.id) return;
    var botao = doc.querySelector('[data-expande-todos="' + tabela.id + '"]');
    if (!botao) return;
    var pais = tabela.querySelectorAll("tr[data-abre]");
    var todosAbertos = pais.length > 0 && Array.prototype.every.call(pais, function (linha) {
      return linha.getAttribute("aria-expanded") === "true";
    });
    botao.setAttribute("aria-expanded", todosAbertos ? "true" : "false");
    botao.textContent = todosAbertos ? "Recolher tudo" : "Expandir tudo";
  }

  function alternarDetalhe(linha) {
    definirDetalhe(linha, linha.getAttribute("aria-expanded") !== "true");
    sincronizarBotao(linha.closest("table"));
  }

  doc.addEventListener("click", function (evento) {
    var linha = evento.target.closest ? evento.target.closest("tr[data-abre]") : null;
    if (linha) alternarDetalhe(linha);
  });

  doc.addEventListener("click", function (evento) {
    var botao = evento.target.closest ? evento.target.closest("[data-expande-todos]") : null;
    if (!botao) return;
    var tabela = doc.getElementById(botao.getAttribute("data-expande-todos"));
    if (!tabela) return;
    var abrir = botao.getAttribute("aria-expanded") !== "true";
    Array.prototype.forEach.call(tabela.querySelectorAll("tr[data-abre]"), function (linha) {
      definirDetalhe(linha, abrir);
    });
    sincronizarBotao(tabela);
  });

  /* ----------------------------------------------------------- alternador */

  doc.addEventListener("click", function (evento) {
    var botao = evento.target.closest ? evento.target.closest("[data-alterna]") : null;
    if (!botao) return;
    var grupo = botao.closest("[data-alternador]");
    if (!grupo) return;
    var chave = botao.getAttribute("data-alterna");
    Array.prototype.forEach.call(grupo.querySelectorAll("[data-alterna]"), function (outro) {
      outro.setAttribute("aria-pressed", outro === botao ? "true" : "false");
    });
    Array.prototype.forEach.call(grupo.querySelectorAll("[data-painel]"), function (painel) {
      painel.hidden = painel.getAttribute("data-painel") !== chave;
    });
  });

  doc.addEventListener("keydown", function (evento) {
    if (evento.key !== "Enter" && evento.key !== " ") return;
    var linha = evento.target.closest ? evento.target.closest("tr[data-abre]") : null;
    if (!linha) return;
    evento.preventDefault();
    alternarDetalhe(linha);
  });

  /* -------------------------------------------------------------- tooltip */

  /* O gráfico chega pronto do build; aqui só se exibe o que ele já traz em
     `data-dica` ({titulo, linhas: [[rótulo, valor, cor, total?]]}); linha sem
     cor ou marcada como total sai separada por um fio. Um único balão
     para a página, posicionado junto ao ponteiro e mantido dentro da janela.
     Texto entra por textContent: rótulo vem da planilha. */
  var balao = null;

  function montarBalao(dica) {
    if (!balao) {
      balao = doc.createElement("div");
      balao.className = "g5-dica";
      balao.setAttribute("role", "tooltip");
      doc.body.appendChild(balao);
    }
    balao.textContent = "";
    var cabeca = doc.createElement("div");
    cabeca.className = "g5-dica__titulo";
    cabeca.textContent = dica.titulo || "";
    balao.appendChild(cabeca);
    (dica.linhas || []).forEach(function (item) {
      var linha = doc.createElement("div");
      var total = item[3] === true || !item[2];
      linha.className = "g5-dica__linha" + (total ? " g5-dica__linha--total" : "");
      var chave = doc.createElement("i");
      if (item[2]) chave.style.background = item[2];
      var valor = doc.createElement("strong");
      valor.textContent = item[1];
      var rotulo = doc.createElement("span");
      rotulo.textContent = item[0];
      linha.appendChild(chave);
      linha.appendChild(valor);
      linha.appendChild(rotulo);
      balao.appendChild(linha);
    });
    balao.hidden = false;
  }

  function posicionarBalao(evento) {
    var folga = 14;
    var x = evento.clientX + folga;
    var y = evento.clientY + folga;
    var caixa = balao.getBoundingClientRect();
    if (x + caixa.width > window.innerWidth - 4) x = evento.clientX - folga - caixa.width;
    if (y + caixa.height > window.innerHeight - 4) y = evento.clientY - folga - caixa.height;
    balao.style.left = Math.max(4, x) + "px";
    balao.style.top = Math.max(4, y) + "px";
  }

  var marcaAtual = null;

  doc.addEventListener("pointermove", function (evento) {
    var marca = evento.target.closest ? evento.target.closest("[data-dica]") : null;
    if (!marca) {
      if (balao) balao.hidden = true;
      marcaAtual = null;
      return;
    }
    if (marca !== marcaAtual) {
      var dica;
      try {
        dica = JSON.parse(marca.getAttribute("data-dica"));
      } catch (erro) {
        return;
      }
      montarBalao(dica);
      marcaAtual = marca;
    }
    posicionarBalao(evento);
  });

  doc.addEventListener("pointerleave", function () {
    if (balao) balao.hidden = true;
    marcaAtual = null;
  });

  /* ------------------------------------------------------------ impressão */

  var botao = doc.querySelector("[data-imprimir]");
  if (botao) {
    botao.addEventListener("click", function () {
      window.print();
    });
  }

  if (paginas.length) mostrar(paginas[0].getAttribute("data-pagina"));
})();
