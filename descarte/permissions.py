from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def administrador_required(view):
    """Exige usuário autenticado com perfil de administrador (controle por perfil, RNF03)."""

    @wraps(view)
    @login_required
    def envelope(request, *args, **kwargs):
        if not request.user.eh_administrador:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return envelope
