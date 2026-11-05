"""Cadastro de usuarios pelo sindico. Os perfis sao fixos (PERFIS)."""
from flask import jsonify, request
from flask_login import current_user

from app.api import api_bp, erro, exige_perfil
from app.extensions import db
from app.models import PERFIL_MORADOR, PERFIL_SINDICO, PERFIS, Unidade, Usuario

SENHA_MINIMA = 8


@api_bp.get("/usuarios")
@exige_perfil(PERFIL_SINDICO)
def listar_usuarios():
    usuarios = db.session.scalars(db.select(Usuario).order_by(Usuario.nome)).all()
    return jsonify({"usuarios": [u.to_dict() for u in usuarios]})


@api_bp.post("/usuarios")
@exige_perfil(PERFIL_SINDICO)
def cadastrar_usuario():
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    email = (dados.get("email") or "").strip().lower()
    senha = dados.get("senha") or ""
    perfil = (dados.get("perfil") or "").strip().upper()

    if not nome or not email:
        return erro("Informe o nome e o e-mail.", 400)
    if perfil not in PERFIS:
        return erro("Perfil invalido.", 400)
    if len(senha) < SENHA_MINIMA:
        return erro(f"A senha precisa ter pelo menos {SENHA_MINIMA} caracteres.", 400)

    # So o morador fica vinculado a uma unidade; os demais perfis atendem a todas.
    unidade = None
    if perfil == PERFIL_MORADOR:
        unidade = db.session.get(Unidade, dados.get("unidade_id") or 0)
        if unidade is None:
            return erro("Informe a unidade do morador.", 400)

    if db.session.scalar(db.select(Usuario).filter_by(email=email)) is not None:
        return erro("Ja existe um usuario com este e-mail.", 409)

    usuario = Usuario(nome=nome, email=email, perfil=perfil, unidade=unidade)
    usuario.definir_senha(senha)
    db.session.add(usuario)
    db.session.commit()
    return jsonify(usuario.to_dict()), 201


@api_bp.patch("/usuarios/<int:usuario_id>")
@exige_perfil(PERFIL_SINDICO)
def alterar_usuario(usuario_id):
    """Ativa ou desativa o usuario e redefine a senha. Nao ha exclusao:
    o historico das encomendas continua apontando para quem as registrou."""
    usuario = db.session.get(Usuario, usuario_id)
    if usuario is None:
        return erro("Usuario nao encontrado.", 404)

    dados = request.get_json(silent=True) or {}
    if "ativo" in dados:
        if usuario.id == current_user.id and not dados["ativo"]:
            return erro("Voce nao pode desativar o proprio usuario.", 400)
        usuario.ativo = bool(dados["ativo"])
    if "senha" in dados:
        if len(dados["senha"] or "") < SENHA_MINIMA:
            return erro(f"A senha precisa ter pelo menos {SENHA_MINIMA} caracteres.", 400)
        usuario.definir_senha(dados["senha"])

    db.session.commit()
    return jsonify(usuario.to_dict())
