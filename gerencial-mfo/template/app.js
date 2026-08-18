/* Gerencial MFO — comportamento do dashboard.
   Quatro coisas, e nada mais: navegar entre as abas, filtrar, ordenar e abrir
   o detalhe de uma linha. Os números já vêm calculados do build; nada aqui
   recalcula valor de negócio.

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

  function alternarDetalhe(linha) {
    var alvo = linha.getAttribute("data-abre");
    var aberto = linha.getAttribute("aria-expanded") === "true";
    linha.setAttribute("aria-expanded", aberto ? "false" : "true");
    Array.prototype.forEach.call(
      doc.querySelectorAll('[data-detalhe="' + alvo + '"]'),
      function (filha) {
        filha.hidden = aberto;
      }
    );
  }

  doc.addEventListener("click", function (evento) {
    var linha = evento.target.closest ? evento.target.closest("tr[data-abre]") : null;
    if (linha) alternarDetalhe(linha);
  });

  doc.addEventListener("keydown", function (evento) {
    if (evento.key !== "Enter" && evento.key !== " ") return;
    var linha = evento.target.closest ? evento.target.closest("tr[data-abre]") : null;
    if (!linha) return;
    evento.preventDefault();
    alternarDetalhe(linha);
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
