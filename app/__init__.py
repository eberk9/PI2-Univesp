"""Fabrica da aplicacao Flask."""
from flask import Flask

from app.extensions import db, login_manager, migrate


def create_app(config_object="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app import models  # noqa: F401  (registra os modelos no metadata)
    from app.api import api_bp
    from app.auth import auth_bp
    from app.main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api/v1")

    @app.shell_context_processor
    def contexto_shell():
        return {"db": db, **{n: getattr(models, n) for n in
                             ("Usuario", "Unidade", "Encomenda",
                              "Movimentacao", "Transportadora")}}

    return app
