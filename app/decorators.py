from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def admin_required(vista):
    @wraps(vista)
    @login_required
    def envoltura(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return vista(*args, **kwargs)

    return envoltura


def propietario_o_admin(anuncio):
    return current_user.is_admin or anuncio.usuario_id == current_user.id
