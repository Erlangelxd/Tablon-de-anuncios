from flask import Blueprint, render_template, request
from sqlalchemy import or_

from ...models import Anuncio, Categoria, Usuario

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    busqueda = request.args.get("q", "").strip()
    categoria_id = request.args.get("categoria", type=int)

    consulta = Anuncio.query.filter_by(activo=True)

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

    total_resultados = consulta.count()
    anuncios = (
        consulta.order_by(Anuncio.fecha_publicacion.desc()).limit(6).all()
    )
    categorias = Categoria.query.order_by(Categoria.nombre).all()

    estadisticas = {
        "anuncios": Anuncio.query.filter_by(activo=True).count(),
        "categorias": Categoria.query.count(),
        "usuarios": Usuario.query.count(),
    }

    return render_template(
        "main/index.html",
        anuncios=anuncios,
        categorias=categorias,
        busqueda=busqueda,
        categoria_id=categoria_id,
        total_resultados=total_resultados,
        estadisticas=estadisticas,
    )
