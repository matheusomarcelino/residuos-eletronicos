import json
from playwright.sync_api import sync_playwright

B = 'http://127.0.0.1:8765'
VIEWS = {'celular 390': (390, 844), 'tablet 768': (768, 1024), 'desktop 1280': (1280, 800)}
PUBLIC = ['/', '/pontos/', '/orientacoes/', '/entrar/', '/cadastro/']
COLAB = ['/registrar/', '/meus-registros/']
ADMIN = ['/gestao/solicitacoes/', '/gestao/pontos/', '/gestao/pontos/novo/', '/gestao/tipos/', '/gestao/tipos/novo/', '/gestao/relatorio/']
res = []   # (teste, resultado, detalhe)

def ok(nome, cond, det=''):
    res.append((nome, 'APROVADO' if cond else 'FALHOU', det))

JS_AUDIT = '''() => {
  const out = {};
  out.lang = document.documentElement.lang;
  out.h1 = document.querySelectorAll('h1').length;
  out.landmarks = ['header','nav','main','footer'].filter(t => !document.querySelector(t));
  out.viewport = !!document.querySelector('meta[name=viewport]');
  out.title = document.title.length > 0;
  const hs = [...document.querySelectorAll('h1,h2,h3,h4')].map(h => +h.tagName[1]);
  out.saltoTitulo = hs.some((n,i) => i>0 && n - hs[i-1] > 1);
  const campos = [...document.querySelectorAll('input:not([type=hidden]),select,textarea')]
      .filter(e => !e.closest('template'));
  out.camposSemRotulo = campos.filter(e => {
      const id = e.id; const viaFor = id && document.querySelector('label[for="'+id+'"]');
      return !(viaFor || e.getAttribute('aria-label') || e.getAttribute('aria-labelledby') || e.closest('label'));
  }).map(e => e.name || e.id);
  out.botoesSemTexto = [...document.querySelectorAll('button,a')].filter(e => !e.closest('template') && !(e.textContent||'').trim() && !e.getAttribute('aria-label')).length;
  out.imgSemAlt = [...document.querySelectorAll('img')].filter(i => !i.hasAttribute('alt')).length;
  out.imgs = document.querySelectorAll('img').length;
  out.idsDuplicados = (() => { const s = {}; const d = []; document.querySelectorAll('[id]').forEach(e => { if (e.closest('template')) return; if (s[e.id]) d.push(e.id); s[e.id] = 1; }); return d; })();
  out.transbordo = document.documentElement.scrollWidth > document.documentElement.clientWidth;
  const vw = document.documentElement.clientWidth;
  out.foraDaTela = [...document.querySelectorAll('main *, header *, footer *')].filter(e => {
      const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return r.width > 0 && r.right > vw + 1 && cs.position !== 'absolute' && !e.closest('.tabela-rolavel') && !e.closest('template');
  }).slice(0,5).map(e => e.tagName + '.' + e.className);
  return out;
}'''

def login(page, email):
    page.goto(B + '/entrar/')
    page.fill('#id_username', email); page.fill('#id_password', 'demo12345')
    page.click('main button[type=submit]'); page.wait_for_load_state()

with sync_playwright() as p:
    br = p.chromium.launch()
    for vnome, (w, h) in VIEWS.items():
        for papel, paginas, email in (('anônimo', PUBLIC, None), ('colaborador', COLAB, 'colaborador@exemplo.com'), ('administrador', ADMIN, 'admin@exemplo.com')):
            ctx = br.new_context(viewport={'width': w, 'height': h}, locale='pt-BR')
            page = ctx.new_page()
            erros = []
            page.on('console', lambda m: erros.append(m.text) if m.type == 'error' else None)
            page.on('pageerror', lambda e: erros.append(str(e)))
            page.on('response', lambda r: erros.append(f'{r.status} {r.url}') if r.status >= 400 else None)
            if email: login(page, email)
            for url in paginas:
                page.goto(B + url); page.wait_for_load_state()
                a = page.evaluate(JS_AUDIT)
                rot = f'{vnome} | {url}'
                ok(rot + ' | sem rolagem horizontal', not a['transbordo'])
                ok(rot + ' | nada fora da tela', not a['foraDaTela'], str(a['foraDaTela']))
                if vnome == 'desktop 1280':   # checagens estruturais independem da largura
                    ok(url + ' | lang pt-BR e viewport e título', a['lang'] == 'pt-BR' and a['viewport'] and a['title'])
                    ok(url + ' | um único h1', a['h1'] == 1, f"h1={a['h1']}")
                    ok(url + ' | marcos header/nav/main/footer', not a['landmarks'], str(a['landmarks']))
                    ok(url + ' | hierarquia de títulos sem saltos', not a['saltoTitulo'])
                    ok(url + ' | todos os campos têm rótulo', not a['camposSemRotulo'], str(a['camposSemRotulo']))
                    ok(url + ' | links e botões com texto', a['botoesSemTexto'] == 0)
                    ok(url + ' | ids únicos', not a['idsDuplicados'], str(a['idsDuplicados']))
                    ok(url + ' | imagens com alt', a['imgSemAlt'] == 0, f"{a['imgs']} imagens na página")
            ok(f'{vnome} | {papel} | sem erros de console/rede', not erros, str(erros[:3]))
            ctx.close()

    # ---------- teclado
    ctx = br.new_context(viewport={'width': 1280, 'height': 800}, locale='pt-BR'); page = ctx.new_page()
    page.goto(B + '/'); page.keyboard.press('Tab')
    foco = page.evaluate('document.activeElement.className + "|" + document.activeElement.textContent.trim()')
    ok('teclado | primeiro Tab foca o link "Pular para o conteúdo"', foco.startswith('pular'), foco)
    page.keyboard.press('Enter')
    ok('teclado | Enter no link de pular leva o foco ao conteúdo', page.evaluate('document.activeElement.id') == 'conteudo')
    ctx.close()
    ctx = br.new_context(viewport={'width': 390, 'height': 844}, locale='pt-BR'); page = ctx.new_page()
    page.goto(B + '/'); page.focus('.menu-botao'); page.keyboard.press('Enter')
    ok('teclado | Enter no botão Menu abre a navegação', page.get_attribute('.menu-botao', 'aria-expanded') == 'true')
    page.keyboard.press('Escape')
    ok('teclado | Esc fecha o menu e devolve o foco ao botão', page.get_attribute('.menu-botao', 'aria-expanded') == 'false' and page.evaluate('document.activeElement.className') == 'menu-botao')
    ctx.close()
    ctx = br.new_context(viewport={'width': 1280, 'height': 800}, locale='pt-BR'); page = ctx.new_page()
    login(page, 'colaborador@exemplo.com'); page.goto(B + '/registrar/')
    page.focus('#adicionar-item'); page.keyboard.press('Enter')
    ok('teclado | Enter em "Adicionar outro item" cria a linha 2', page.locator('.item-linha').count() == 2)
    ctx.close()

    # ---------- fluxos dinâmicos (JS ligado)
    ctx = br.new_context(viewport={'width': 1280, 'height': 800}, locale='pt-BR'); page = ctx.new_page()
    page.goto(B + '/pontos/')
    n_todos = page.locator('#lista-pontos > li').count()
    url0 = page.url
    page.select_option('#tipo', label='Pilhas'); page.wait_for_timeout(500)
    ok('dinâmico | filtro de pontos atualiza a lista sem navegar', page.locator('#lista-pontos > li').count() >= 1 and page.evaluate('performance.getEntriesByType("navigation").length') == 1, f'{n_todos} → {page.locator("#lista-pontos > li").count()}')
    ok('dinâmico | resultado anunciado em região aria-live', 'encontrado' in page.inner_text('#resultado-pontos'))
    ok('dinâmico | Recic.LE aparece com horário real', 'Recic.LE' in page.inner_text('#lista-pontos') and 'sáb, 8h às 12h' in page.inner_text('#lista-pontos'))
    ctx.close()

    ctx = br.new_context(viewport={'width': 1280, 'height': 800}, locale='pt-BR'); page = ctx.new_page()
    login(page, 'colaborador@exemplo.com'); page.goto(B + '/registrar/')
    # validação do servidor: envia sem ponto
    page.select_option('#id_itens-0-tipo', label='Pilhas'); page.fill('#id_itens-0-quantidade', '0')
    page.wait_for_timeout(800); page.click("#form-descarte button[type=submit]", timeout=5000); page.wait_for_load_state()
    ok('validação | quantidade 0 e ponto vazio são rejeitados com mensagens', page.url.endswith('/registrar/') and page.locator('.erro').count() >= 1, f"{page.locator('.erro').count()} mensagens")
    page.select_option('#id_ponto', index=1); page.fill('#id_itens-0-quantidade', '4')
    page.click('#adicionar-item'); page.select_option('#id_itens-1-tipo', label='Baterias'); page.fill('#id_itens-1-quantidade', '1')
    ok('dinâmico | TOTAL_FORMS acompanha as linhas', page.input_value('#id_itens-TOTAL_FORMS') == '2')
    page.click('.item-linha >> nth=0 >> .remover-item')
    ok('dinâmico | remover renumera os campos', page.locator('.item-linha').count() == 1 and page.get_attribute('.item-linha select', 'name') == 'itens-0-tipo' and page.input_value('#id_itens-TOTAL_FORMS') == '1')
    page.fill('#id_itens-0-quantidade', '1'); page.select_option('#id_itens-0-tipo', label='Baterias')
    page.wait_for_timeout(800); page.click("#form-descarte button[type=submit]", timeout=5000); page.wait_for_load_state()
    ok('fluxo | registro válido redireciona para "Meus registros" com aviso', page.url.endswith('/meus-registros/') and 'registrado' in page.inner_text('.mensagens'))
    ctx.close()

    ctx = br.new_context(viewport={'width': 1280, 'height': 800}, locale='pt-BR'); page = ctx.new_page()
    login(page, 'admin@exemplo.com'); page.goto(B + '/gestao/solicitacoes/')
    primeiro = page.locator('#tabela-solicitacoes tbody tr').filter(has=page.locator('.form-status')).first
    antes = primeiro.locator('.status').inner_text()
    primeiro.locator('.form-status button').click(); page.wait_for_timeout(600)
    depois = primeiro.locator('.status').inner_text()
    ok('dinâmico | status muda sem recarregar', antes != depois and page.url.endswith('/gestao/solicitacoes/'), f'{antes} → {depois}')
    ok('dinâmico | mudança de status anunciada (aria-live)', 'atualizada' in page.inner_text('#aviso-status'))
    ctx.close()

    # ---------- sem JavaScript (melhoria progressiva)
    ctx = br.new_context(viewport={'width': 390, 'height': 844}, java_script_enabled=False, locale='pt-BR'); page = ctx.new_page()
    page.goto(B + '/')
    ok('sem JS | menu visível no celular (sem botão Menu)', page.locator('.menu').is_visible() and not page.locator('.menu-botao').is_visible())
    page.goto(B + '/pontos/'); page.select_option('#tipo', label='Pilhas'); page.click('#filtro-pontos button[type=submit]'); page.wait_for_load_state()
    ok('sem JS | filtro de pontos funciona pelo botão Filtrar', 'tipo=' in page.url and page.locator('#lista-pontos > li').count() >= 1, page.url)
    login(page, 'colaborador@exemplo.com'); page.goto(B + '/registrar/')
    ok('sem JS | botão "Adicionar" oculto e formulário com 1 item', page.locator('#adicionar-item').is_hidden() and page.locator('.item-linha').count() == 1)
    page.select_option('#id_ponto', index=1); page.select_option('#id_itens-0-tipo', label='Celulares'); page.fill('#id_itens-0-quantidade', '2')
    page.wait_for_timeout(800); page.click("#form-descarte button[type=submit]", timeout=5000); page.wait_for_load_state()
    ok('sem JS | registro de descarte funciona', page.url.endswith('/meus-registros/'))
    ctx.close()
    ctx = br.new_context(java_script_enabled=False, locale='pt-BR'); page = ctx.new_page()
    login(page, 'admin@exemplo.com'); page.goto(B + '/gestao/solicitacoes/')
    n_antes = page.locator('.form-status').count()
    page.locator('.form-status button').first.click(); page.wait_for_load_state()
    ok('sem JS | mudança de status funciona por envio comum', 'atualizada' in page.inner_text('.mensagens'))
    ctx.close()

    # ---------- permissões no navegador
    ctx = br.new_context(locale='pt-BR'); page = ctx.new_page()
    login(page, 'colaborador@exemplo.com')
    r = page.goto(B + '/gestao/relatorio/')
    ok('permissão | colaborador recebe 403 na gestão', r.status == 403)
    ctx.close()
    br.close()

falhas = [r for r in res if r[1] != 'APROVADO']
print(f'{len(res)} verificações, {len(res)-len(falhas)} aprovadas, {len(falhas)} falharam')
for r in falhas: print('FALHOU:', r)
json.dump(res, open('/tmp/claude-0/-home-claude/09c2d98e-119f-5e4a-8299-1de163a462b8/scratchpad/audit_result.json', 'w'), ensure_ascii=False, indent=1)
