import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ...extensions import db
from ...models import Usuario

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _destino_seguro(destino):
    if destino and destino.startswith("/") and not destino.startswith("//"):
        return destino
    return url_for("main.index")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        recordar = request.form.get("remember") == "on"

        usuario = Usuario.query.filter_by(username=username).first()

        if usuario and usuario.check_password(password):
            login_user(usuario, remember=recordar)
            flash(f"Bienvenido, {usuario.nombre}.", "success")
            return redirect(_destino_seguro(request.args.get("next")))

        flash("Usuario o contraseña incorrectos.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    datos = {
        "nombre": "",
        "username": "",
        "email": "",
    }

    if request.method == "POST":
        datos = {
            "nombre": request.form.get("nombre", "").strip(),
            "username": request.form.get("username", "").strip().lower(),
            "email": request.form.get("email", "").strip().lower(),
        }
        password = request.form.get("password", "")
        confirmar = request.form.get("confirmar", "")

        errores = []
        if not datos["nombre"]:
            errores.append("El nombre completo es obligatorio.")
        if not re.fullmatch(r"[a-zA-Z0-9_.-]{3,50}", datos["username"]):
            errores.append(
                "El nombre de usuario debe tener entre 3 y 50 caracteres y solo puede contener letras, números, puntos, guiones y guiones bajos."
            )
        if "@" not in datos["email"]:
            errores.append("Ingrese un correo electrónico válido.")
        if len(password) < 6:
            errores.append("La contraseña debe tener al menos 6 caracteres.")
        if password != confirmar:
            errores.append("Las contraseñas no coinciden.")
        if Usuario.query.filter(db.func.lower(Usuario.username) == datos["username"]).first():
            errores.append("El nombre de usuario ya está registrado.")
        if Usuario.query.filter(db.func.lower(Usuario.email) == datos["email"]).first():
            errores.append("El correo electrónico ya está registrado.")

        if errores:
            for error in errores:
                flash(error, "danger")
        else:
            usuario = Usuario(
                nombre=datos["nombre"],
                username=datos["username"],
                email=datos["email"],
                rol="usuario",
            )
            usuario.set_password(password)
            db.session.add(usuario)
            db.session.commit()
            login_user(usuario)
            flash("Tu cuenta fue creada correctamente.", "success")
            return redirect(url_for("main.index"))

    return render_template("auth/registro.html", datos=datos)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión finalizada correctamente.", "info")
    return redirect(url_for("auth.login"))
