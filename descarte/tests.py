"""Testes automatizados das regras principais (execute: python manage.py test)."""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import ItemDescartado, PontoColeta, SolicitacaoDescarte, TipoResiduo, Unidade, Usuario


class BaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.unidade = Unidade.objects.create(nome="Loja Teste")
        cls.pilhas = TipoResiduo.objects.create(nome="Pilhas")
        cls.celulares = TipoResiduo.objects.create(nome="Celulares")
        cls.ponto = PontoColeta.objects.create(nome="Ponto A", endereco="Rua A, 1")
        cls.ponto.tipos.set([cls.pilhas, cls.celulares])
        cls.ponto_pilhas = PontoColeta.objects.create(nome="Ponto Pilhas", endereco="Rua B, 2")
        cls.ponto_pilhas.tipos.set([cls.pilhas])
        cls.colab = Usuario.objects.create_user("colab@teste.com", "senha-forte-123", first_name="Colab", unidade=cls.unidade)
        cls.admin = Usuario.objects.create_user(
            "admin@teste.com", "senha-forte-123", first_name="Admin", perfil=Usuario.Perfil.ADMINISTRADOR
        )

    def dados_descarte(self, ponto=None, tipo=None, **extra):
        dados = {
            "unidade": self.unidade.pk,
            "ponto": (ponto or self.ponto).pk,
            "data": timezone.localdate().isoformat(),
            "itens-TOTAL_FORMS": "1",
            "itens-INITIAL_FORMS": "0",
            "itens-MIN_NUM_FORMS": "1",
            "itens-MAX_NUM_FORMS": "1000",
            "itens-0-tipo": (tipo or self.pilhas).pk,
            "itens-0-quantidade": "3",
            "itens-0-observacao": "",
        }
        dados.update(extra)
        return dados


class ModeloTests(BaseTestCase):
    def test_senha_armazenada_com_hash(self):
        self.assertNotEqual(self.colab.password, "senha-forte-123")
        self.assertTrue(self.colab.check_password("senha-forte-123"))

    def test_fluxo_de_status(self):
        s = SolicitacaoDescarte.objects.create(usuario=self.colab, unidade=self.unidade, ponto=self.ponto)
        self.assertEqual(s.status, "solicitado")
        self.assertTrue(s.avancar_status(por=self.admin))
        self.assertEqual(s.status, "coletado")
        self.assertTrue(s.avancar_status(por=self.admin))
        self.assertEqual(s.status, "encaminhado")
        self.assertFalse(s.avancar_status(por=self.admin))  # não passa do último status

    def test_perfis(self):
        self.assertFalse(self.colab.eh_administrador)
        self.assertTrue(self.admin.eh_administrador)


class PaginasPublicasTests(BaseTestCase):
    def test_paginas_publicas_abrem(self):
        for nome in ("home", "orientacoes", "pontos", "login", "cadastro"):
            self.assertEqual(self.client.get(reverse(nome)).status_code, 200, nome)

    def test_filtro_de_pontos_por_tipo(self):
        resp = self.client.get(reverse("pontos"), {"tipo": self.celulares.pk})
        self.assertContains(resp, "Ponto A")
        self.assertNotContains(resp, "Ponto Pilhas")

    def test_api_pontos_json(self):
        resp = self.client.get(reverse("api_pontos"), {"tipo": self.celulares.pk})
        nomes = [p["nome"] for p in resp.json()["pontos"]]
        self.assertEqual(nomes, ["Ponto A"])

    def test_html_basico_acessivel(self):
        html = self.client.get(reverse("home")).content.decode()
        self.assertIn('lang="pt-BR"', html)
        self.assertIn('name="viewport"', html)
        self.assertIn('class="pular"', html)
        self.assertIn("<main", html)


class CadastroTests(BaseTestCase):
    def dados(self, **extra):
        d = {"first_name": "Novo Usuário", "email": "Novo@Teste.com", "unidade": self.unidade.pk,
             "password1": "Senha-bem-forte-77", "password2": "Senha-bem-forte-77", "aceite": "on"}
        d.update(extra)
        return d

    def test_cadastro_cria_colaborador_e_faz_login(self):
        resp = self.client.post(reverse("cadastro"), self.dados())
        self.assertRedirects(resp, reverse("registrar"))
        u = Usuario.objects.get(email="novo@teste.com")
        self.assertEqual(u.perfil, "colaborador")
        self.assertEqual(int(self.client.session["_auth_user_id"]), u.pk)

    def test_cadastro_nao_permite_escolher_perfil(self):
        self.client.post(reverse("cadastro"), self.dados(perfil="administrador", is_staff="on"))
        u = Usuario.objects.get(email="novo@teste.com")
        self.assertEqual(u.perfil, "colaborador")
        self.assertFalse(u.is_staff)

    def test_cadastro_exige_aceite_e_senha_forte(self):
        self.assertEqual(Usuario.objects.filter(email="novo@teste.com").count(), 0)
        r1 = self.client.post(reverse("cadastro"), self.dados(aceite=""))
        r2 = self.client.post(reverse("cadastro"), self.dados(password1="12345678", password2="12345678"))
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(Usuario.objects.filter(email="novo@teste.com").count(), 0)

    def test_email_duplicado(self):
        resp = self.client.post(reverse("cadastro"), self.dados(email="colab@teste.com"))
        self.assertContains(resp, "Já existe uma conta com este e-mail.")

    def test_login_por_email(self):
        resp = self.client.post(reverse("login"), {"username": "colab@teste.com", "password": "senha-forte-123"})
        self.assertRedirects(resp, reverse("minhas_solicitacoes"))


class DescarteTests(BaseTestCase):
    def test_registrar_exige_login(self):
        resp = self.client.get(reverse("registrar"))
        self.assertRedirects(resp, f"{reverse('login')}?next={reverse('registrar')}")

    def test_registrar_descarte_cria_solicitacao_e_itens(self):
        self.client.force_login(self.colab)
        resp = self.client.post(reverse("registrar"), self.dados_descarte())
        self.assertRedirects(resp, reverse("minhas_solicitacoes"))
        s = SolicitacaoDescarte.objects.get()
        self.assertEqual(s.usuario, self.colab)
        self.assertEqual(s.status, "solicitado")
        self.assertEqual(s.itens.get().quantidade, 3)

    def test_ponto_deve_aceitar_o_tipo(self):
        self.client.force_login(self.colab)
        resp = self.client.post(reverse("registrar"), self.dados_descarte(ponto=self.ponto_pilhas, tipo=self.celulares))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "não recebe")
        self.assertEqual(SolicitacaoDescarte.objects.count(), 0)

    def test_data_futura_e_quantidade_invalida(self):
        self.client.force_login(self.colab)
        futura = (timezone.localdate() + timedelta(days=2)).isoformat()
        r1 = self.client.post(reverse("registrar"), self.dados_descarte(data=futura))
        r2 = self.client.post(reverse("registrar"), self.dados_descarte(**{"itens-0-quantidade": "0"}))
        self.assertEqual((r1.status_code, r2.status_code), (200, 200))
        self.assertEqual(SolicitacaoDescarte.objects.count(), 0)

    def test_historico_mostra_so_os_proprios_registros_e_filtra_por_tipo(self):
        outro = Usuario.objects.create_user("outro@teste.com", "senha-forte-123", first_name="Outro")
        mine = SolicitacaoDescarte.objects.create(usuario=self.colab, unidade=self.unidade, ponto=self.ponto)
        ItemDescartado.objects.create(solicitacao=mine, tipo=self.pilhas, quantidade=2)
        alheia = SolicitacaoDescarte.objects.create(usuario=outro, unidade=self.unidade, ponto=self.ponto)
        ItemDescartado.objects.create(solicitacao=alheia, tipo=self.pilhas, quantidade=9)
        self.client.force_login(self.colab)
        resp = self.client.get(reverse("minhas_solicitacoes"))
        self.assertContains(resp, f"Solicitação #{mine.pk}")
        self.assertNotContains(resp, f"Solicitação #{alheia.pk}")
        resp = self.client.get(reverse("minhas_solicitacoes"), {"tipo": self.celulares.pk})
        self.assertNotContains(resp, f"Solicitação #{mine.pk}")


class AdministradorTests(BaseTestCase):
    def setUp(self):
        self.s = SolicitacaoDescarte.objects.create(usuario=self.colab, unidade=self.unidade, ponto=self.ponto)
        ItemDescartado.objects.create(solicitacao=self.s, tipo=self.pilhas, quantidade=10)
        ItemDescartado.objects.create(solicitacao=self.s, tipo=self.celulares, quantidade=2)

    def test_areas_de_gestao_negam_colaborador_e_anonimo(self):
        nomes = ["gestao_solicitacoes", "pontos_admin", "ponto_novo", "tipos_admin", "tipo_novo", "relatorio"]
        for nome in nomes:
            self.assertEqual(self.client.get(reverse(nome)).status_code, 302, nome)  # anônimo → login
        self.client.force_login(self.colab)
        for nome in nomes:
            self.assertEqual(self.client.get(reverse(nome)).status_code, 403, nome)

    def test_colaborador_nao_altera_status(self):
        self.client.force_login(self.colab)
        resp = self.client.post(reverse("avancar_status", args=[self.s.pk]))
        self.assertEqual(resp.status_code, 403)
        self.s.refresh_from_db()
        self.assertEqual(self.s.status, "solicitado")

    def test_admin_avanca_status_via_json(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse("avancar_status", args=[self.s.pk]), HTTP_ACCEPT="application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "coletado")
        self.assertEqual(resp.json()["proximo_label"], "Encaminhado")
        self.s.refresh_from_db()
        self.assertEqual(self.s.atualizado_por, self.admin)

    def test_status_nao_avanca_alem_do_ultimo(self):
        self.s.status = "encaminhado"
        self.s.save()
        self.client.force_login(self.admin)
        resp = self.client.post(reverse("avancar_status", args=[self.s.pk]), HTTP_ACCEPT="application/json")
        self.assertEqual(resp.status_code, 409)

    def test_status_so_aceita_post(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("avancar_status", args=[self.s.pk])).status_code, 405)

    def test_admin_cadastra_ponto_e_tipo(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse("ponto_novo"), {"nome": "Ponto Novo", "endereco": "Rua C, 3", "horario": "", "tipos": [self.pilhas.pk], "ativo": "on"})
        self.assertRedirects(r, reverse("pontos_admin"))
        self.assertTrue(PontoColeta.objects.filter(nome="Ponto Novo", tipos=self.pilhas).exists())
        r = self.client.post(reverse("tipo_novo"), {"nome": "Tablets", "orientacoes": "Apague os dados."})
        self.assertRedirects(r, reverse("tipos_admin"))

    def test_relatorio_totais_e_csv(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("relatorio"))
        self.assertEqual(resp.context["total"], 12)
        self.assertEqual(resp.context["por_tipo"][0]["tipo__nome"], "Pilhas")
        resp = self.client.get(reverse("relatorio"), {"tipo": self.celulares.pk})
        self.assertEqual(resp.context["total"], 2)
        csv_resp = self.client.get(reverse("relatorio"), {"formato": "csv"})
        self.assertEqual(csv_resp["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("Pilhas;10", csv_resp.content.decode("utf-8-sig"))


class SeedTests(TestCase):
    def test_seed_demo_e_idempotente_e_inclui_recicle(self):
        from django.core.management import call_command
        from io import StringIO

        call_command("seed_demo", stdout=StringIO())
        call_command("seed_demo", stdout=StringIO())  # rodar de novo não duplica
        self.assertEqual(PontoColeta.objects.filter(nome__startswith="Recic.LE").count(), 1)
        recic = PontoColeta.objects.get(nome__startswith="Recic.LE")
        self.assertIn("sáb, 8h às 12h", recic.horario)
        self.assertEqual(recic.tipos.count(), TipoResiduo.objects.count())
        self.assertEqual(Usuario.objects.filter(perfil="administrador").count(), 1)
