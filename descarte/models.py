"""Modelos do domínio. Correspondem às entidades do DER (docs/diagramas/der.png)."""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Unidade(models.Model):
    """Loja franqueada ou setor da sede."""

    class Tipo(models.TextChoices):
        LOJA = "loja", "Loja"
        SETOR = "setor", "Setor da sede"

    nome = models.CharField("nome", max_length=120, unique=True)
    tipo = models.CharField("tipo", max_length=10, choices=Tipo.choices, default=Tipo.LOJA)
    cidade = models.CharField("cidade", max_length=80, blank=True)

    class Meta:
        verbose_name = "unidade"
        verbose_name_plural = "unidades"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class UsuarioManager(BaseUserManager):
    """Gerenciador de usuários que usa o e-mail como identificador de login."""

    use_in_migrations = True

    def _criar(self, email, password, **extra):
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        email = self.normalize_email(email).lower()
        usuario = self.model(email=email, **extra)
        usuario.set_password(password)  # a senha é armazenada com hash (RNF03)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._criar(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("perfil", Usuario.Perfil.ADMINISTRADOR)
        return self._criar(email, password, **extra)


class Usuario(AbstractUser):
    """Usuário do sistema (RF01), com perfil de colaborador ou administrador.

    Guarda só os dados pessoais necessários: nome, e-mail e unidade (RNF04).
    """

    class Perfil(models.TextChoices):
        COLABORADOR = "colaborador", "Colaborador"
        ADMINISTRADOR = "administrador", "Administrador"

    username = None
    last_name = None
    first_name = models.CharField("nome completo", max_length=150)
    email = models.EmailField("e-mail", unique=True)
    unidade = models.ForeignKey(
        Unidade, verbose_name="unidade", on_delete=models.SET_NULL, null=True, blank=True, related_name="usuarios"
    )
    perfil = models.CharField("perfil", max_length=15, choices=Perfil.choices, default=Perfil.COLABORADOR)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]
    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"

    def __str__(self):
        return f"{self.first_name} <{self.email}>"

    @property
    def nome(self):
        return self.first_name

    @property
    def eh_administrador(self):
        return self.perfil == self.Perfil.ADMINISTRADOR or self.is_superuser


class TipoResiduo(models.Model):
    nome = models.CharField("nome", max_length=80, unique=True)
    orientacoes = models.TextField("orientações de descarte", blank=True)

    class Meta:
        verbose_name = "tipo de resíduo"
        verbose_name_plural = "tipos de resíduo"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class PontoColeta(models.Model):
    nome = models.CharField("nome", max_length=120)
    endereco = models.CharField("endereço", max_length=200)
    horario = models.CharField("horário de recebimento", max_length=120, blank=True)
    ativo = models.BooleanField("ativo", default=True)
    # Relação N:N "aceita" do DER (tabela associativa PONTO_TIPO).
    tipos = models.ManyToManyField(TipoResiduo, verbose_name="tipos aceitos", related_name="pontos", blank=True)

    class Meta:
        verbose_name = "ponto de coleta"
        verbose_name_plural = "pontos de coleta"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class SolicitacaoDescarte(models.Model):
    """Registro de descarte feito por um usuário (RF02), com acompanhamento de status (RF04)."""

    class Status(models.TextChoices):
        SOLICITADO = "solicitado", "Solicitado"
        COLETADO = "coletado", "Coletado"
        ENCAMINHADO = "encaminhado", "Encaminhado"

    # Fluxo permitido: solicitado -> coletado -> encaminhado
    PROXIMO = {
        Status.SOLICITADO: Status.COLETADO,
        Status.COLETADO: Status.ENCAMINHADO,
    }

    usuario = models.ForeignKey(Usuario, verbose_name="usuário", on_delete=models.PROTECT, related_name="solicitacoes")
    unidade = models.ForeignKey(Unidade, verbose_name="unidade", on_delete=models.PROTECT, related_name="solicitacoes")
    ponto = models.ForeignKey(
        PontoColeta, verbose_name="ponto de coleta", on_delete=models.PROTECT, related_name="solicitacoes"
    )
    data = models.DateField("data", default=timezone.localdate)
    status = models.CharField("status", max_length=12, choices=Status.choices, default=Status.SOLICITADO)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)
    atualizado_por = models.ForeignKey(
        Usuario, verbose_name="atualizado por", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        verbose_name = "solicitação de descarte"
        verbose_name_plural = "solicitações de descarte"
        ordering = ["-data", "-id"]

    def __str__(self):
        return f"Solicitação #{self.pk} ({self.get_status_display()})"

    @property
    def proximo_status(self):
        return self.PROXIMO.get(self.status)

    @property
    def total_itens(self):
        return sum(i.quantidade for i in self.itens.all())

    def avancar_status(self, por=None):
        """Avança para o próximo status do fluxo; devolve False se já estiver no último."""
        proximo = self.proximo_status
        if proximo is None:
            return False
        self.status = proximo
        self.atualizado_por = por
        self.save(update_fields=["status", "atualizado_por", "atualizado_em"])
        return True


class ItemDescartado(models.Model):
    solicitacao = models.ForeignKey(SolicitacaoDescarte, on_delete=models.CASCADE, related_name="itens")
    tipo = models.ForeignKey(TipoResiduo, verbose_name="tipo de resíduo", on_delete=models.PROTECT, related_name="itens")
    quantidade = models.PositiveIntegerField("quantidade", validators=[MinValueValidator(1)], default=1)
    observacao = models.CharField("observação", max_length=200, blank=True)

    class Meta:
        verbose_name = "item descartado"
        verbose_name_plural = "itens descartados"

    def __str__(self):
        return f"{self.quantidade} x {self.tipo}"
