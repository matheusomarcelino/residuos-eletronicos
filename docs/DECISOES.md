# Decisões de desenvolvimento

Registro das principais decisões do módulo 2 do PI II (framework, HTML e CSS), com o motivo de cada uma.

## 1. Framework: Django

- **Escolha.** Django 5.2 (versão LTS), um dos frameworks de back-end citados na disciplina (junto com Node.js e
  Ruby on Rails).
- **Por quê.** Traz pronto o que o projeto exige: autenticação com senhas com *hash*, proteção contra CSRF, ORM
  ligado a banco relacional, sistema de *templates* e testes automatizados. Isso reduz código e risco, e a
  organização em modelos, visões e *templates* deixa o código fácil de manter.
- **Alternativa avaliada.** Vue.js, foco da aula, resolve só a interface. O projeto também precisa de usuários,
  perfis, banco de dados e regras de negócio, então um framework completo foi mais adequado. Vue.js continua uma
  opção para evoluir a interface (ver seção 9).
- **Alinhamento com os artefatos.** Os modelos do Django seguem o DER do PI II (`Unidade`, `Usuario`,
  `TipoResiduo`, `PontoColeta`, `SolicitacaoDescarte`, `ItemDescartado`), e as páginas atendem aos requisitos
  RF01 a RF08.

## 2. Plataforma: web responsiva

A aplicação roda no navegador, em computador e celular, sem instalar nada. Isso favorece equipes em várias lojas
(RNF02) e dispensa publicar em lojas de aplicativos.

## 3. Banco de dados: SQLite agora, PostgreSQL ou MySQL depois

SQLite não exige instalação e basta para o desenvolvimento. Como todo acesso passa pelo ORM, trocar para
PostgreSQL ou MySQL exige só alterar o bloco `DATABASES` em `config/settings.py`.

## 4. Usuários, perfis e segurança (RF01, RNF03, RNF04)

- Modelo de usuário próprio, com **e-mail como login** e campo `perfil` (colaborador ou administrador).
- Senhas armazenadas com *hash* e validadas (mínimo de 8 caracteres, não comuns, não só números).
- O **perfil nunca vem do formulário de cadastro**: quem se cadastra é sempre colaborador (há teste para isso).
- Páginas de gestão exigem perfil de administrador (`administrador_required`) e respondem 403 aos demais.
- Alterações (POST) são protegidas por CSRF. A mudança de status só aceita POST.
- Em produção (`DJANGO_DEBUG=0`), cookies seguros, HTTPS e HSTS são ativados.
- **Privacidade (LGPD).** Coletamos só nome, e-mail e unidade, e o cadastro exige o aceite do uso dos dados.

## 5. Regras de negócio

- **Fluxo de status.** `solicitado → coletado → encaminhado`, sem pular nem voltar, só alterado por administrador,
  com registro de quem atualizou.
- **Ponto e tipo de resíduo.** Se o ponto de coleta tem tipos cadastrados, só recebe esses tipos. O formulário avisa
  quando o item não é aceito.
- **Consulta pública aos pontos.** RF03 não exige login, para que clientes e colaboradores vejam onde descartar.
- **Data.** Não pode ser futura. Quantidade mínima de 1 item.

## 6. HTML: semântica e acessibilidade

- `lang="pt-BR"`, `viewport`, título único por página e hierarquia de títulos (`h1`, `h2`).
- Marcos semânticos: `header`, `nav` (com `aria-label`), `main`, `section`, `footer`.
- *Link* "Pular para o conteúdo" e foco visível em todos os elementos.
- Todo campo tem `label` associado; erros usam `role="alert"`; mensagens usam `role="status"`.
- Menu com `aria-expanded` e página atual com `aria-current="page"`.
- Tabelas com `caption`, `scope` e cabeçalhos; barras do relatório com `<meter>`.
- Atualizações dinâmicas (status e filtro de pontos) são anunciadas em regiões `aria-live`.
- Alvos de toque com pelo menos 44 px e contraste de cores acima de 4,5:1 (RNF07).

## 7. CSS: responsivo e organizado

- Um arquivo externo (`css/estilo.css`), sem estilos *inline* e sem *framework* de CSS. Assim, os conceitos de
  Box Model, Flexbox, Grid e *media queries* da aula ficam explícitos, e o carregamento é leve (RNF05).
- **Mobile-first**: os estilos base são para telas pequenas, e *media queries* (`min-width`) ampliam o layout em
  40 rem, 48 rem e 64 rem.
- Variáveis CSS (`:root`) para cores, espaçamentos e raios, e unidades relativas (`rem`, `%`, `fr`).
- Em telas pequenas, as tabelas viram cartões empilhados (o rótulo da coluna vem de `data-rotulo`).
- Respeita `prefers-reduced-motion` e tem estilos de impressão.

## 8. JavaScript: melhoria progressiva

A interface dinâmica usa JavaScript puro, em arquivos pequenos e separados:

| Arquivo | O que faz |
|---|---|
| `menu.js` | Abre e fecha o menu em telas pequenas |
| `itens.js` | Adiciona e remove itens do descarte sem recarregar |
| `status.js` | Atualiza o status da solicitação via `fetch` (JSON) |
| `pontos.js` | Filtra pontos de coleta por tipo sem recarregar |

**Melhoria progressiva:** sem JavaScript, o menu fica visível, o formulário tem 1 item, o filtro usa o botão
"Filtrar" e o status muda por um envio comum de formulário. O JavaScript monta o conteúdo com `textContent`
(evita injeção de HTML).

## 9. Limites e próximos passos

- **Não feitos nesta versão:** notificações (RF10), mapa interativo (RF11), integração com sistemas internos (RF12)
  e exportação em PDF (RF09; o CSV está pronto).
- **Pontos de coleta.** O Recic.LE (endereço e horários) foi informado pelo autor e deve ser reconfirmado com a associação; os outros dois pontos de `seed_demo` são fictícios. Os dados reais, com tipos aceitos e horários
  confirmados, devem ser cadastrados pelo administrador.
- **Banco e hospedagem.** Trocar para PostgreSQL ou MySQL e publicar em hospedagem gratuita ou de baixo custo
  (RNF08), com HTTPS.
- **Testes e CI.** Ampliar os testes automatizados e executá-los com GitHub Actions (módulos seguintes).
- **Interface.** Se a interação crescer, pode-se adotar Vue.js nos componentes que mais mudam (por exemplo, a
  lista de itens), mantendo o Django como API.

## 10. Testes realizados e resultados

Só constam testes efetivamente executados (ambiente: Python 3.13, Django 5.2, Chromium via Playwright).

| Teste | Resultado |
|---|---|
| 25 testes automatizados Django (`manage.py test`, também com `-W error::DeprecationWarning`) | 25 aprovados |
| `manage.py check --deploy` | só avisos sobre HSTS_INCLUDE_SUBDOMAINS e HSTS_PRELOAD (decisão consciente) |
| Auditoria no navegador (`docs/testes/auditoria_navegador.py`): 211 verificações em 390, 768 e 1280 px, em todas as páginas de anônimo, colaborador e administrador | 211 aprovadas depois da correção abaixo |
| Itens da auditoria | sem rolagem horizontal; sem erros de console, de página ou HTTP 4xx/5xx; lang, viewport e título; um h1; marcos header/nav/main/footer; títulos sem saltos; todo campo com rótulo; ids únicos |
| Teclado | link "Pular para o conteúdo", Enter/Esc no menu, Enter em "Adicionar outro item" |
| Fluxos dinâmicos | filtro de pontos, adicionar/remover/renumerar itens, validação do servidor, status sem recarregar |
| Sem JavaScript | menu visível, filtro por botão, registro com 1 item, status por formulário |
| Permissão | colaborador recebe 403 na gestão |

**Problema encontrado e corrigido:** sem JavaScript, os botões "Adicionar outro item" e "Remover este item" apareciam
sem função, porque a regra `display` de `.botao` anulava o atributo `hidden`. Corrigido com `[hidden] { display: none !important; }`.

**Não realizado / limites:** não houve auditoria com leitor de tela nem teste em celulares e tablets reais (apenas
emulação do Chromium); só Chromium foi testado; no tablet de 768 px a tabela de gestão fica apertada e o selo de
status da última coluna encosta na borda (sem rolagem da página).
