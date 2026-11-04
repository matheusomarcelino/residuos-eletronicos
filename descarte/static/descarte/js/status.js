/* Gestão de solicitações: atualiza o status sem recarregar a página (fetch + JSON).
   Se o JavaScript falhar, o formulário comum (POST) continua funcionando. */
(function () {
  "use strict";
  var aviso = document.getElementById("aviso-status");

  document.querySelectorAll(".form-status").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var botao = form.querySelector("button");
      var linha = form.closest("tr");
      botao.disabled = true;

      fetch(form.action, {
        method: "POST",
        headers: { "Accept": "application/json", "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value },
        credentials: "same-origin"
      })
        .then(function (resp) { return resp.json().then(function (dados) { return { ok: resp.ok, dados: dados }; }); })
        .then(function (r) {
          if (!r.ok) { throw new Error("falha"); }
          var etiqueta = linha.querySelector(".status");
          etiqueta.textContent = r.dados.status_label;
          etiqueta.className = "status status--" + r.dados.status;
          if (r.dados.proximo_label) {
            botao.textContent = "Marcar como " + r.dados.proximo_label;
            botao.disabled = false;
          } else {
            form.outerHTML = '<span class="nota">Concluída</span>';
          }
          var numero = linha.querySelector("th").textContent.trim();
          if (aviso) { aviso.textContent = "Solicitação " + numero + " atualizada para " + r.dados.status_label + "."; }
        })
        .catch(function () {
          // Cai para o envio tradicional do formulário
          form.submit();
        });
    });
  });
})();
