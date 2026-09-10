from functools import wraps

from flask import abort, request
from flask_login import current_user


def admin_required(f):
    """Bloqueia a rota para quem não é admin (usar após login_required)."""

    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return wrapped


def bloquear_escrita_visualizacao():
    """Handler de before_request: usuários de visualização só podem fazer GET."""
    if (
        request.method != "GET"
        and current_user.is_authenticated
        and not current_user.pode_editar
    ):
        abort(403)
