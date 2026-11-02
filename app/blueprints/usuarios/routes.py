import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import or_

from ...decorators import admin_required
from ...extensions import db
from ...models import Usuario

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")

ROLES = ("admin", "usuario")


def _validar(datos, usuario=None):
    errores = []

    if not datos["nombre"]:
        errores.append("El nombre completo es obligatorio.")
    if not re.fullmatch(r"[a-zA-Z0-9_.-]{3,50}", datos["username"]):
        errores.append(
            "El nombre de usuario debe tener entre 3 y 50 caracteres y solo puede contener letras, números, puntos, guiones y guiones bajos."
        )
    if "@" not in datos["email"]:
        errores.append("Ingrese un correo electrónico válido.")
    if datos["rol"] not in ROLES:
        errores.append("Seleccione un rol válido.")
    if usuario is None and len(datos["password"]) < 6:
        errores.append("La contraseña debe tener al menos 6 caracteres.")
    if usuario is not None and datos["password"] and len(datos["password"]) < 6:
        errores.append("La nueva contraseña debe tener al menos 6 caracteres.")

    consulta_username = Usuario.query.filter(
        db.func.lower(Usuario.username) == datos["username"]
    )
    consulta_email = Usuario.query.filter(
        db.func.lower(Usuario.email) == datos["email"]
    )
    if usuario is not None:
        consulta_username = consulta_username.filter(Usuario.id != usuario.id)
        consulta_email = consulta_email.filter(Usuario.id != usuario.id)

    if consulta_username.first():
        errores.append("El nombre de usuario ya está registrado.")
    if consulta_email.first():
        errores.append("El correo electrónico ya está registrado.")

    if usuario is not None and usuario.id == current_user.id and datos["rol"] != "admin":
        errores.append("No puedes quitarte el rol de administrador a ti mismo.")

    return errores


def _datos_formulario():
    return {
        "nombre": request.form.get("nombre", "").strip(),
        "username": request.form.get("username", "").strip().lower(),
        "email": request.form.get("email", "").strip().lower(),
        "rol": request.form.get("rol", "usuario"),
        "password": request.form.get("password", ""),
    }


@usuarios_bp.route("/")
@admin_required
def lista():
    busqueda = request.args.get("q", "").strip()
    consulta = Usuario.query

    if busqueda:
        patron = f"%{busqueda}%"
        consulta = consulta.filter(
            or_(
                Usuario.nombre.ilike(patron),
                Usuario.username.ilike(patron),
                Usuario.email.ilike(patron),
            )
        )

    usuarios = consulta.order_by(Usuario.nombre).all()
    return render_template(
        "usuarios/lista.html", usuarios=usuarios, busqueda=busqueda
    )


@usuarios_bp.route("/nuevo", methods=["GET", "POST"])
@admin_required
def crear():
    datos = {
        "nombre": "",
        "username": "",
        "email": "",
        "rol": "usuario",
        "password": "",
    }

    if request.method == "POST":
        datos = _datos_formulario()
        errores = _validar(datos)

        if errores:
            for error in errores:
                flash(error, "danger")
        else:
            usuario = Usuario(
                nombre=datos["nombre"],
                username=datos["username"],
                email=datos["email"],
                rol=datos["rol"],
            )
            usuario.set_password(datos["password"])
            db.session.add(usuario)
            db.session.commit()
            flash("Usuario registrado correctamente.", "success")
            return redirect(url_for("usuarios.lista"))

    return render_template(
        "usuarios/formulario.html",
        usuario=None,
        datos=datos,
        roles=ROLES,
        accion="Registrar usuario",
    )


@usuarios_bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
@admin_required
def editar(usuario_id):
    usuario = db.get_or_404(Usuario, usuario_id)

    datos = {
        "nombre": usuario.nombre,
        "username": usuario.username,
        "email": usuario.email,
        "rol": usuario.rol,
        "password": "",
    }

    if request.method == "POST":
        datos = _datos_formulario()
        errores = _validar(datos, usuario)

        if errores:
            for error in errores:
                flash(error, "danger")
        else:
            usuario.nombre = datos["nombre"]
            usuario.username = datos["username"]
            usuario.email = datos["email"]
            usuario.rol = datos["rol"]
            if datos["password"]:
                usuario.set_password(datos["password"])
            db.session.commit()
            flash("Usuario actualizado correctamente.", "success")
            return redirect(url_for("usuarios.lista"))

    return render_template(
        "usuarios/formulario.html",
        usuario=usuario,
        datos=datos,
        roles=ROLES,
        accion="Actualizar usuario",
    )


@usuarios_bp.route("/<int:usuario_id>/eliminar", methods=["POST"])
@admin_required
def eliminar(usuario_id):
    usuario = db.get_or_404(Usuario, usuario_id)

    if usuario.id == current_user.id:
        flash("No puedes eliminar tu propia cuenta.", "warning")
    elif usuario.anuncios:
        flash(
            "No se puede eliminar el usuario porque tiene anuncios publicados.",
            "warning",
        )
    else:
        db.session.delete(usuario)
        db.session.commit()
        flash("Usuario eliminado correctamente.", "success")

    return redirect(url_for("usuarios.lista"))
