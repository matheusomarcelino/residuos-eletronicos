from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ItemDescartado, PontoColeta, SolicitacaoDescarte, TipoResiduo, Unidade, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "perfil", "unidade", "is_active")
    list_filter = ("perfil", "unidade", "is_active")
    search_fields = ("email", "first_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Dados", {"fields": ("first_name", "unidade", "perfil")}),
        ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Datas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "first_name", "unidade", "perfil", "password1", "password2")}),
    )


class ItemInline(admin.TabularInline):
    model = ItemDescartado
    extra = 0


@admin.register(SolicitacaoDescarte)
class SolicitacaoAdmin(admin.ModelAdmin):
    list_display = ("id", "data", "usuario", "unidade", "ponto", "status")
    list_filter = ("status", "unidade", "ponto")
    inlines = [ItemInline]


admin.site.register(Unidade)
admin.site.register(TipoResiduo)
admin.site.register(PontoColeta)
