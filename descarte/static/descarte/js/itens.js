/* Formulário de descarte: adicionar e remover itens sem recarregar a página.
   Melhoria progressiva: sem JavaScript, o formulário continua com 1 item. */
(function () {
  "use strict";
  var prefixo = "itens";
  var conteiner = document.getElementById("itens");
  var modelo = document.getElementById("modelo-item");
  var botaoAdicionar = document.getElementById("adicionar-item");
  var total = document.getElementById("id_" + prefixo + "-TOTAL_FORMS");
  if (!conteiner || !modelo || !botaoAdicionar || !total) { return; }

  botaoAdicionar.hidden = false;

  function linhas() { return conteiner.querySelectorAll(".item-linha"); }

  function atualizarBotoesRemover() {
    var muitas = linhas().length > 1;
    linhas().forEach(function (linha) {
      linha.querySelector(".remover-item").hidden = !muitas;
    });
  }

  // Renumera name/id/for de cada linha (itens-0-tipo, itens-1-tipo, ...)
  function renumerar() {
    linhas().forEach(function (linha, i) {
      linha.querySelectorAll("[name], [id], label[for]").forEach(function (el) {
        ["name", "id", "for"].forEach(function (attr) {
          var valor = el.getAttribute(attr);
          if (valor) { el.setAttribute(attr, valor.replace(/itens-(\d+|__prefix__)-/, "itens-" + i + "-")); }
        });
      });
    });
    total.value = linhas().length;
    atualizarBotoesRemover();
  }

  botaoAdicionar.addEventListener("click", function () {
    var html = modelo.innerHTML.replace(/__prefix__/g, String(linhas().length));
    conteiner.insertAdjacentHTML("beforeend", html);
    renumerar();
    var nova = linhas()[linhas().length - 1];
    var primeiro = nova.querySelector("select, input:not([type=hidden])");
    if (primeiro) { primeiro.focus(); }
  });

  conteiner.addEventListener("click", function (evento) {
    var botao = evento.target.closest(".remover-item");
    if (!botao || linhas().length <= 1) { return; }
    botao.closest(".item-linha").remove();
    renumerar();
    botaoAdicionar.focus();
  });

  atualizarBotoesRemover();
})();
