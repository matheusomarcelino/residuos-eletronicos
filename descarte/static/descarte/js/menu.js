/* Menu responsivo: botão que abre e fecha a navegação em telas pequenas.
   Sem JavaScript, o CSS mantém o menu visível (classe "sem-js"). */
(function () {
  "use strict";
  document.documentElement.classList.remove("sem-js");
  var botao = document.querySelector(".menu-botao");
  var menu = document.getElementById("menu-principal");
  if (!botao || !menu) { return; }

  function definir(aberto) {
    menu.classList.toggle("aberto", aberto);
    botao.setAttribute("aria-expanded", String(aberto));
  }

  botao.addEventListener("click", function () {
    definir(botao.getAttribute("aria-expanded") !== "true");
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && botao.getAttribute("aria-expanded") === "true") {
      definir(false);
      botao.focus();
    }
  });
})();
