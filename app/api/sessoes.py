"""Recurso de sessao: autenticacao via API."""
from flask import jsonify, request
from flask_login import current_user, login_user, logout_user

from app.api import api_bp, erro, exige_login
from app.extensions import db
from app.models import Usuario


@api_bp.post("/sessoes")
def criar_sessao():
    dados = request.get_json(silent=True) or request.form
    email = (dados.get("email") or "").strip().lower()
    senha = dados.get("senha") or ""

    usuario = db.session.scalar(db.select(Usuario).filter_by(email=email))
    if usuario is None or not usuario.conferir_senha(senha):
        return erro("E-mail ou senha incorretos.", 401)
    if not usuario.ativo:
        return erro("Usuario inativo.", 403)

    login_user(usuario)
    return jsonify({"usuario": usuario.to_dict()}), 201


@api_bp.delete("/sessoes")
@exige_login
def encerrar_sessao():
    logout_user()
    return "", 204


@api_bp.get("/sessoes/atual")
@exige_login
def sessao_atual():
    return jsonify({"usuario": current_user.to_dict()})
