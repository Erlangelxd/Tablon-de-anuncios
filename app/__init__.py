import os
from datetime import datetime, timezone

import click
from flask import Flask, render_template

from config import Config
from .extensions import db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Debes iniciar sesión para acceder a esta sección."
    login_manager.login_message_category = "warning"

    from .blueprints.anuncios import anuncios_bp
    from .blueprints.auth import auth_bp
    from .blueprints.categorias import categorias_bp
    from .blueprints.main import main_bp
    from .blueprints.usuarios import usuarios_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(categorias_bp)
    app.register_blueprint(anuncios_bp)

    from .models import Anuncio, Categoria, Usuario

    @login_manager.user_loader
    def cargar_usuario(usuario_id):
        return db.session.get(Usuario, int(usuario_id))

    @app.context_processor
    def variables_globales():
        return {
            "anio_actual": datetime.now().year,
            "nombre_sitio": "Tablón de Anuncios",
        }

    @app.errorhandler(403)
    def error_403(error):
        return render_template("errores/403.html"), 403

    @app.errorhandler(404)
    def error_404(error):
        return render_template("errores/404.html"), 404

    @app.cli.command("init-db")
    def init_db():
        db.create_all()

        if not Usuario.query.filter_by(username="admin").first():
            admin = Usuario(
                nombre="Administrador del Sistema",
                username="admin",
                email="admin@tablon.com",
                rol="admin",
            )
            admin.set_password("admin123")
            db.session.add(admin)

        if Categoria.query.count() == 0:
            db.session.add_all(
                [
                    Categoria(nombre="Académico", descripcion="Avisos de clases, exámenes y trámites."),
                    Categoria(nombre="Eventos", descripcion="Actividades, ferias y encuentros."),
                    Categoria(nombre="Deportes", descripcion="Torneos y actividades deportivas."),
                    Categoria(nombre="Tecnología", descripcion="Cursos, talleres y novedades tecnológicas."),
                    Categoria(nombre="General", descripcion="Anuncios de interés general."),
                ]
            )
            db.session.commit()

        if Anuncio.query.count() == 0:
            admin = Usuario.query.filter_by(username="admin").first()
            categorias = {categoria.nombre: categoria for categoria in Categoria.query.all()}
            db.session.add_all(
                [
                    Anuncio(
                        titulo="Inscripciones para el segundo examen parcial",
                        contenido=(
                            "Se comunica a todos los estudiantes que el registro para el segundo "
                            "examen parcial estará habilitado durante toda la semana. Ingrese al "
                            "portal académico y confirme su inscripción antes del viernes."
                        ),
                        usuario_id=admin.id,
                        categoria_id=categorias["Académico"].id,
                    ),
                    Anuncio(
                        titulo="Feria de proyectos de ingeniería",
                        contenido=(
                            "La feria de proyectos se realizará en el patio central. Los equipos "
                            "interesados deben registrar su proyecto con su docente guía y presentar "
                            "un resumen de máximo dos páginas."
                        ),
                        usuario_id=admin.id,
                        categoria_id=categorias["Eventos"].id,
                    ),
                    Anuncio(
                        titulo="Taller de desarrollo web con Flask",
                        contenido=(
                            "Se abre la convocatoria al taller de desarrollo web. Se abordarán temas "
                            "de Application Factory, blueprints, bases de datos SQLite y Bootstrap. "
                            "Cupos limitados."
                        ),
                        usuario_id=admin.id,
                        categoria_id=categorias["Tecnología"].id,
                    ),
                ]
            )

        db.session.commit()
        click.echo("Base de datos bd_anuncios inicializada correctamente.")
        click.echo("Usuario administrador: admin / admin123")

    return app
