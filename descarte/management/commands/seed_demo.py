"""Cria dados de DEMONSTRAÇÃO para testar a aplicação localmente.

Não use em produção: as contas de exemplo têm senha pública. Dois dos pontos de coleta
são fictícios (marcados com "exemplo"). O Recic.LE usa dados informados pelo autor do
projeto (endereço e horários) e deve ser conferido antes de uso real; os demais pontos
reais são cadastrados pelo administrador (RF05).
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from descarte.models import ItemDescartado, PontoColeta, SolicitacaoDescarte, TipoResiduo, Unidade, Usuario

SENHA_DEMO = "demo12345"


class Command(BaseCommand):
    help = "Popula o banco com unidades, tipos, pontos e usuários de demonstração."

    def handle(self, *args, **opcoes):
        sede, _ = Unidade.objects.get_or_create(nome="Sede – Tecnologia da Informação", defaults={"tipo": "setor", "cidade": "Campo Grande"})
        loja1, _ = Unidade.objects.get_or_create(nome="Loja Exemplo Centro", defaults={"tipo": "loja", "cidade": "Campo Grande"})
        loja2, _ = Unidade.objects.get_or_create(nome="Loja Exemplo Bairro", defaults={"tipo": "loja", "cidade": "Campo Grande"})

        textos = {
            "Pilhas": "Não descarte no lixo comum. Entregue em ponto de coleta; mantenha as pilhas secas e separadas.",
            "Baterias": "Evite perfurar ou amassar. Se estiver estufada, isole e entregue com cuidado em ponto de coleta.",
            "Celulares": "Apague os dados e saia das contas antes de descartar. Retire o chip e o cartão de memória.",
            "Carregadores e cabos": "Entregue junto com os demais eletrônicos; podem ser reaproveitados ou reciclados.",
            "Computadores e periféricos": "Apague ou destrua o armazenamento (HD/SSD) com segurança antes de entregar.",
        }
        tipos = {n: TipoResiduo.objects.get_or_create(nome=n, defaults={"orientacoes": o})[0] for n, o in textos.items()}

        p1, criado = PontoColeta.objects.get_or_create(
            nome="Ponto de coleta da sede (exemplo)",
            defaults={"endereco": "Endereço de exemplo, 100 – Campo Grande/MS", "horario": "Seg a sex, 8h às 17h"},
        )
        if criado:
            p1.tipos.set(tipos.values())
        p2, criado = PontoColeta.objects.get_or_create(
            nome="Ponto de coleta de pilhas e baterias (exemplo)",
            defaults={"endereco": "Endereço de exemplo, 200 – Campo Grande/MS", "horario": "Seg a sáb, 9h às 18h"},
        )
        if criado:
            p2.tipos.set([tipos["Pilhas"], tipos["Baterias"]])

        recic, criado = PontoColeta.objects.get_or_create(
            nome="Recic.LE – Associação dos Recicladores de Resíduos Eletroeletrônicos",
            defaults={
                "endereco": "Rua Vera Cruz, 542 – Bairro Rita Vieira, Campo Grande/MS",
                "horario": "Seg a sex, 8h às 18h; sáb, 8h às 12h; dom fechado",
            },
        )
        if criado:
            recic.tipos.set(tipos.values())  # informado: sem restrição de materiais recebidos

        if not Usuario.objects.filter(email="admin@exemplo.com").exists():
            Usuario.objects.create_user("admin@exemplo.com", SENHA_DEMO, first_name="Administrador Exemplo",
                                        unidade=sede, perfil="administrador", is_staff=True)
        if not Usuario.objects.filter(email="colaborador@exemplo.com").exists():
            Usuario.objects.create_user("colaborador@exemplo.com", SENHA_DEMO, first_name="Colaborador Exemplo", unidade=loja1)

        colab = Usuario.objects.get(email="colaborador@exemplo.com")
        if not SolicitacaoDescarte.objects.exists():
            hoje = timezone.localdate()
            exemplos = [
                (loja1, p1, hoje - timedelta(days=9), "encaminhado", [("Celulares", 3), ("Carregadores e cabos", 5)]),
                (loja1, p2, hoje - timedelta(days=4), "coletado", [("Pilhas", 20), ("Baterias", 4)]),
                (loja2, p1, hoje - timedelta(days=1), "solicitado", [("Computadores e periféricos", 2)]),
            ]
            for unidade, ponto, data, status, itens in exemplos:
                s = SolicitacaoDescarte.objects.create(usuario=colab, unidade=unidade, ponto=ponto, data=data, status=status)
                for nome, qtd in itens:
                    ItemDescartado.objects.create(solicitacao=s, tipo=tipos[nome], quantidade=qtd)

        self.stdout.write(self.style.SUCCESS("Dados de demonstração criados."))
        self.stdout.write(f"  Administrador: admin@exemplo.com / {SENHA_DEMO}")
        self.stdout.write(f"  Colaborador:   colaborador@exemplo.com / {SENHA_DEMO}")
