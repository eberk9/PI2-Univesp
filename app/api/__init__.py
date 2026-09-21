"""Interface de programacao de aplicacoes (API) no estilo REST, sob /api/v1."""
from flask import Blueprint, jsonify
from flask_login import current_user
from functools import wraps

api_bp = Blueprint("api", __name__)


def erro(mensagem, status):
    return jsonify({"erro": mensagem}), status


def exige_login(f):
    """Como a API e consumida pelo proprio front, reaproveita a sessao.

    Diferente do Flask-Login padrao, responde 401 em JSON em vez de
    redirecionar para a tela de login.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return erro("Autenticacao necessaria.", 401)
        return f(*args, **kwargs)

    return wrapper


def exige_perfil(*perfis):
    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return erro("Autenticacao necessaria.", 401)
            if current_user.perfil not in perfis:
                return erro("Seu perfil nao permite esta operacao.", 403)
            return f(*args, **kwargs)

        return wrapper

    return decorador


from app.api import encomendas, sessoes, unidades  # noqa: E402,F401
