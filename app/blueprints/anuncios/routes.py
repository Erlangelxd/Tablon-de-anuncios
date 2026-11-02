from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import or_

from ...decorators import propietario_o_admin
from ...extensions import db
from ...models import Anuncio, Categoria

anuncios_bp = Blueprint("anuncios", __name__, url_prefix="/anuncios")

ESTADOS = ("activos", "inactivos", "todos")


def _datos_formulario():
    return {
        "titulo": request.form.get("titulo", "").strip(),
        "contenido": request.form.get("contenido", "").strip(),
        "categoria_id": request.form.get("categoria_id", type=int),
        "activo": "activo" in request.form,
    }


def _validar(datos):
    errores = []
    categoria = None

    if not datos["titulo"]:
        errores.append("El título del anuncio es obligatorio.")
    elif len(datos["titulo"]) > 150:
        errores.append("El título no puede superar los 150 caracteres.")

    if not datos["contenido"]:
        errores.append("El contenido del anuncio es obligatorio.")

    if datos["categoria_id"]:
        categoria = db.session.get(Categoria, datos["categoria_id"])
    if categoria is None:
        errores.append("Seleccione una categoría válida.")

    return errores, categoria


@anuncios_bp.route("/")
def lista():
    busqueda = request.args.get("q", "").strip()
    categoria_id = request.args.get("categoria", type=int)
    estado = request.args.get("estado", "activos")
    pagina = request.args.get("page", 1, type=int)

    if not current_user.is_authenticated:
        estado = "activos"
    elif estado not in ESTADOS:
        estado = "activos"

    consulta = Anuncio.query

    if estado == "activos":
        consulta = consulta.filter_by(activo=True)
    elif estado == "inactivos":
        consulta = consulta.filter_by(activo=False)

    if categoria_id:
        consulta = consulta.filter_by(categoria_id=categoria_id)

    if busqueda:
        patron = f"%{busqueda}%"
        consulta = consulta.filter(
            or_(
                Anuncio.titulo.ilike(patron),
                Anuncio.contenido.ilike(patron),
            )
        )

    paginacion = consulta.order_by(
        Anuncio.fecha_publicacion.desc()
    ).paginate(
        page=pagina,
        per_page=current_app.config["ITEMS_POR_PAGINA"],
        error_out=False,
    )

    categorias = Categoria.query.order_by(Categoria.nombre).all()

    filtros = {}
    if busqueda:
        filtros["q"] = busqueda
    if categoria_id:
        filtros["categoria"] = categoria_id
    if estado != "activos":
        filtros["estado"] = estado

    return render_template(
        "anuncios/lista.html",
        paginacion=paginacion,
        anuncios=paginacion.items,
        categorias=categorias,
        busqueda=busqueda,
        categoria_id=categoria_id,
        estado=estado,
        filtros=filtros,
        estados=ESTADOS,
    )


@anuncios_bp.route("/<int:anuncio_id>")
def detalle(anuncio_id):
    anuncio = db.get_or_404(Anuncio, anuncio_id)
    autorizado = current_user.is_authenticated and propietario_o_admin(anuncio)

    if not anuncio.activo and not autorizado:
        abort(404)

    return render_template("anuncios/detalle.html", anuncio=anuncio)


@anuncios_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def crear():
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    datos = {
        "titulo": "",
        "contenido": "",
        "categoria_id": None,
        "activo": True,
    }

    if request.method == "POST":
        datos = _datos_formulario()
        errores, categoria = _validar(datos)

        if errores:
            for error in errores:
                flash(error, "danger")
        else:
            anuncio = Anuncio(
                titulo=datos["titulo"],
                contenido=datos["contenido"],
                activo=datos["activo"],
                usuario_id=current_user.id,
                categoria_id=categoria.id,
            )
            db.session.add(anuncio)
            db.session.commit()
            flash("Anuncio publicado correctamente.", "success")
            return redirect(url_for("anuncios.detalle", anuncio_id=anuncio.id))

    return render_template(
        "anuncios/formulario.html",
        anuncio=None,
        datos=datos,
        categorias=categorias,
        accion="Publicar anuncio",
    )


@anuncios_bp.route("/<int:anuncio_id>/editar", methods=["GET", "POST"])
@login_required
def editar(anuncio_id):
    anuncio = db.get_or_404(Anuncio, anuncio_id)

    if not propietario_o_admin(anuncio):
        abort(403)

    categorias = Categoria.query.order_by(Categoria.nombre).all()
    datos = {
        "titulo": anuncio.titulo,
        "contenido": anuncio.contenido,
        "categoria_id": anuncio.categoria_id,
        "activo": anuncio.activo,
    }

    if request.method == "POST":
        datos = _datos_formulario()
        errores, categoria = _validar(datos)

        if errores:
            for error in errores:
                flash(error, "danger")
        else:
            anuncio.titulo = datos["titulo"]
            anuncio.contenido = datos["contenido"]
            anuncio.categoria_id = categoria.id
            anuncio.activo = datos["activo"]
            db.session.commit()
            flash("Anuncio actualizado correctamente.", "success")
            return redirect(url_for("anuncios.detalle", anuncio_id=anuncio.id))

    return render_template(
        "anuncios/formulario.html",
        anuncio=anuncio,
        datos=datos,
        categorias=categorias,
        accion="Actualizar anuncio",
    )


@anuncios_bp.route("/<int:anuncio_id>/estado", methods=["POST"])
@login_required
def cambiar_estado(anuncio_id):
    anuncio = db.get_or_404(Anuncio, anuncio_id)

    if not propietario_o_admin(anuncio):
        abort(403)

    anuncio.activo = not anuncio.activo
    db.session.commit()

    estado = "activo" if anuncio.activo else "inactivo"
    flash(f"El anuncio ahora está {estado}.", "success")
    return redirect(url_for("anuncios.detalle", anuncio_id=anuncio.id))


@anuncios_bp.route("/<int:anuncio_id>/eliminar", methods=["POST"])
@login_required
def eliminar(anuncio_id):
    anuncio = db.get_or_404(Anuncio, anuncio_id)

    if not propietario_o_admin(anuncio):
        abort(403)

    db.session.delete(anuncio)
    db.session.commit()
    flash("Anuncio eliminado correctamente.", "success")
    return redirect(url_for("anuncios.lista"))
