from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

urlpatterns = [
    path("", views.home, name="home"),
    path("orientacoes/", views.orientacoes, name="orientacoes"),
    path("pontos/", views.pontos, name="pontos"),
    path("api/pontos/", views.api_pontos, name="api_pontos"),
    # conta
    path("entrar/", auth_views.LoginView.as_view(authentication_form=LoginForm), name="login"),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
    path("cadastro/", views.cadastro, name="cadastro"),
    # colaborador
    path("registrar/", views.registrar, name="registrar"),
    path("meus-registros/", views.minhas_solicitacoes, name="minhas_solicitacoes"),
    # administrador
    path("gestao/solicitacoes/", views.gestao_solicitacoes, name="gestao_solicitacoes"),
    path("gestao/solicitacoes/<int:pk>/avancar/", views.avancar_status, name="avancar_status"),
    path("gestao/pontos/", views.pontos_admin, name="pontos_admin"),
    path("gestao/pontos/novo/", views.ponto_form, name="ponto_novo"),
    path("gestao/pontos/<int:pk>/", views.ponto_form, name="ponto_editar"),
    path("gestao/tipos/", views.tipos_admin, name="tipos_admin"),
    path("gestao/tipos/novo/", views.tipo_form, name="tipo_novo"),
    path("gestao/tipos/<int:pk>/", views.tipo_form, name="tipo_editar"),
    path("gestao/relatorio/", views.relatorio, name="relatorio"),
]
