"""Formulários. A validação fica no servidor; o HTML5 apenas ajuda o usuário."""
from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone

from .models import ItemDescartado, PontoColeta, SolicitacaoDescarte, TipoResiduo, Unidade, Usuario


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="E-mail", widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"})
    )
    password = forms.CharField(
        label="Senha", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password"})
    )


class CadastroForm(forms.ModelForm):
    """Cadastro de colaborador (RF01). O perfil NUNCA vem do formulário."""

    password1 = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Mínimo de 8 caracteres, sem ser só números nem uma senha muito comum.",
    )
    password2 = forms.CharField(
        label="Confirme a senha", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"})
    )
    aceite = forms.BooleanField(
        label="Li e concordo com o uso dos meus dados (nome, e-mail e unidade) apenas para registrar e acompanhar descartes.",
        error_messages={"required": "É necessário aceitar o uso dos dados para criar a conta."},
    )

    class Meta:
        model = Usuario
        fields = ["first_name", "email", "unidade"]
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email

    def clean(self):
        dados = super().clean()
        s1, s2 = dados.get("password1"), dados.get("password2")
        if s1 and s2 and s1 != s2:
            self.add_error("password2", "As senhas não coincidem.")
        if s1:
            usuario = Usuario(first_name=dados.get("first_name", ""), email=dados.get("email", ""))
            try:
                password_validation.validate_password(s1, usuario)
            except forms.ValidationError as erro:
                self.add_error("password1", erro)
        return dados

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password1"])
        usuario.perfil = Usuario.Perfil.COLABORADOR
        if commit:
            usuario.save()
        return usuario


class SolicitacaoForm(forms.ModelForm):
    class Meta:
        model = SolicitacaoDescarte
        fields = ["unidade", "ponto", "data"]
        widgets = {"data": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ponto"].queryset = PontoColeta.objects.filter(ativo=True)
        self.fields["ponto"].empty_label = "Selecione o ponto de coleta"
        self.fields["unidade"].empty_label = "Selecione a unidade"

    def clean_data(self):
        data = self.cleaned_data["data"]
        if data > timezone.localdate():
            raise forms.ValidationError("A data não pode ser futura.")
        return data


class ItemForm(forms.ModelForm):
    class Meta:
        model = ItemDescartado
        fields = ["tipo", "quantidade", "observacao"]
        widgets = {"quantidade": forms.NumberInput(attrs={"min": 1})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo"].empty_label = "Selecione o tipo"


ItemFormSet = forms.inlineformset_factory(
    SolicitacaoDescarte, ItemDescartado, form=ItemForm, extra=0, min_num=1, validate_min=True, can_delete=False
)


class PontoForm(forms.ModelForm):
    class Meta:
        model = PontoColeta
        fields = ["nome", "endereco", "horario", "tipos", "ativo"]
        widgets = {"tipos": forms.CheckboxSelectMultiple}


class TipoForm(forms.ModelForm):
    class Meta:
        model = TipoResiduo
        fields = ["nome", "orientacoes"]
        widgets = {"orientacoes": forms.Textarea(attrs={"rows": 4})}


class FiltroPeriodoForm(forms.Form):
    """Filtros do histórico (RF06) e do relatório (RF07)."""

    de = forms.DateField(label="De", required=False, widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    ate = forms.DateField(label="Até", required=False, widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    tipo = forms.ModelChoiceField(
        label="Tipo de resíduo", queryset=TipoResiduo.objects.all(), required=False, empty_label="Todos os tipos"
    )
    unidade = forms.ModelChoiceField(
        label="Unidade", queryset=Unidade.objects.all(), required=False, empty_label="Todas as unidades"
    )

    def clean(self):
        dados = super().clean()
        if dados.get("de") and dados.get("ate") and dados["de"] > dados["ate"]:
            self.add_error("ate", "A data final deve ser igual ou posterior à data inicial.")
        return dados
