from flask import Blueprint, flash, redirect, render_template, request, url_for

from ...decorators import admin_required
from ...extensions import db
from ...models import Categoria

categorias_bp = Blueprint("categorias", __name__, url_prefix="/categorias")


def _validar(datos, categoria=None):
    errores = []

    if not datos["nombre"]:
        errores.append("El nombre de la categoría es obligatorio.")
    elif len(datos["nombre"]) > 80:
        errores.append("El nombre no puede superar los 80 caracteres.")

    consulta = Categoria.query.filter(
        db.func.lower(Categoria.nombre) == datos["nombre"].lower()
    )
    if categoria is not None:
        consulta = consulta.filter(Categoria.id != categoria.id)

    if consulta.first():
        errores.append("Ya existe una categoría con ese nombre.")

    return errores


def _datos_formulario():
    return {
        "nombre": request.form.get("nombre", "").strip(),
        "descripcion": request.form.get("descripcion", "").strip(),
    }


@categorias_bp.route("/")
@admin_required
def lista():
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    return render_template("categorias/lista.html", categorias=categorias)


@categorias_bp.route("/nueva", methods=["GET", "POST"])
@admin_required
def crear():
    datos = {"nombre": "", "descripcion": ""}

    if request.method == "POST":
        datos = _datos_formulario()
        errores = _validar(datos)

        if errores:
            for error in errores:
                flash(error, "danger")
        else:
            categoria = Categoria(
                nombre=datos["nombre"], descripcion=datos["descripcion"]
            )
            db.session.add(categoria)
            db.session.commit()
            flash("Categoría registrada correctamente.", "success")
            return redirect(url_for("categorias.lista"))

    return render_template(
        "categorias/formulario.html",
        categoria=None,
        datos=datos,
        accion="Registrar categoría",
    )


@categorias_bp.route("/<int:categoria_id>/editar", methods=["GET", "POST"])
@admin_required
def editar(categoria_id):
    categoria = db.get_or_404(Categoria, categoria_id)
    datos = {
        "nombre": categoria.nombre,
        "descripcion": categoria.descripcion or "",
    }

    if request.method == "POST":
        datos = _datos_formulario()
        errores = _validar(datos, categoria)

        if errores:
            for error in errores:
                flash(error, "danger")
        else:
            categoria.nombre = datos["nombre"]
            categoria.descripcion = datos["descripcion"]
            db.session.commit()
            flash("Categoría actualizada correctamente.", "success")
            return redirect(url_for("categorias.lista"))

    return render_template(
        "categorias/formulario.html",
        categoria=categoria,
        datos=datos,
        accion="Actualizar categoría",
    )


@categorias_bp.route("/<int:categoria_id>/eliminar", methods=["POST"])
@admin_required
def eliminar(categoria_id):
    categoria = db.get_or_404(Categoria, categoria_id)

    if categoria.anuncios:
        flash(
            "No se puede eliminar la categoría porque tiene anuncios asociados.",
            "warning",
        )
    else:
        db.session.delete(categoria)
        db.session.commit()
        flash("Categoría eliminada correctamente.", "success")

    return redirect(url_for("categorias.lista"))
