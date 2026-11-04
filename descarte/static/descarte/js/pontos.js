/* Pontos de coleta: filtra por tipo de resíduo sem recarregar a página.
   Sem JavaScript, o botão "Filtrar" envia o formulário (GET) normalmente. */
(function () {
  "use strict";
  var form = document.getElementById("filtro-pontos");
  var lista = document.getElementById("lista-pontos");
  var aviso = document.getElementById("resultado-pontos");
  if (!form || !lista) { return; }

  function criar(tag, classe, texto) {
    var el = document.createElement(tag);
    if (classe) { el.className = classe; }
    if (texto !== undefined) { el.textContent = texto; }   // textContent evita injeção de HTML
    return el;
  }

  function linha(rotulo, valor) {
    var p = criar("p", "cartao__linha");
    p.appendChild(criar("span", "rotulo", rotulo + " "));
    p.appendChild(document.createTextNode(valor));
    return p;
  }

  function desenhar(pontos) {
    lista.textContent = "";
    if (!pontos.length) {
      lista.appendChild(criar("li", "vazio", "Nenhum ponto de coleta encontrado para este filtro."));
      return;
    }
    pontos.forEach(function (p) {
      var li = criar("li", "cartao");
      li.appendChild(criar("h2", "cartao__titulo", p.nome));
      li.appendChild(linha("Endereço:", p.endereco));
      if (p.horario) { li.appendChild(linha("Horário:", p.horario)); }
      var aceita = criar("p", "cartao__linha");
      aceita.appendChild(criar("span", "rotulo", "Aceita:"));
      li.appendChild(aceita);
      var etiquetas = criar("ul", "etiquetas");
      (p.tipos.length ? p.tipos : ["Todos os tipos"]).forEach(function (t) { etiquetas.appendChild(criar("li", "", t)); });
      li.appendChild(etiquetas);
      lista.appendChild(li);
    });
  }

  function filtrar() {
    var tipo = form.elements.tipo.value;
    var url = lista.dataset.url + (tipo ? "?tipo=" + encodeURIComponent(tipo) : "");
    fetch(url, { headers: { "Accept": "application/json" } })
      .then(function (r) { if (!r.ok) { throw new Error("falha"); } return r.json(); })
      .then(function (dados) {
        desenhar(dados.pontos);
        aviso.textContent = dados.pontos.length + (dados.pontos.length === 1 ? " ponto encontrado." : " pontos encontrados.");
        history.replaceState(null, "", tipo ? "?tipo=" + encodeURIComponent(tipo) : location.pathname);
      })
      .catch(function () { form.submit(); });
  }

  form.addEventListener("submit", function (e) { e.preventDefault(); filtrar(); });
  form.elements.tipo.addEventListener("change", filtrar);
})();
