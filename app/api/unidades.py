"""Unidades e transportadoras. O cadastro de unidades e exclusivo do sindico."""
from flask import jsonify, request

from app.api import api_bp, erro, exige_login, exige_perfil
from app.extensions import db
from app.models import PERFIL_SINDICO, Transportadora, Unidade


@api_bp.get("/unidades")
@exige_login
def listar_unidades():
    unidades = db.session.scalars(
        db.select(Unidade).order_by(Unidade.bloco, Unidade.numero)
    ).all()
    return jsonify({"unidades": [u.to_dict() for u in unidades]})


@api_bp.post("/unidades")
@exige_perfil(PERFIL_SINDICO)
def cadastrar_unidade():
    dados = request.get_json(silent=True) or {}
    bloco = (dados.get("bloco") or "").strip().upper()
    numero = (dados.get("numero") or "").strip().upper()
    descricao = (dados.get("descricao") or "").strip()
    if not numero:
        return erro("Informe o numero da unidade.", 400)

    existente = db.session.scalar(db.select(Unidade).filter_by(bloco=bloco, numero=numero))
    if existente is not None:
        return erro(f"A unidade {existente.identificacao} ja esta cadastrada.", 409)

    unidade = Unidade(bloco=bloco, numero=numero, descricao=descricao)
    db.session.add(unidade)
    db.session.commit()
    return jsonify(unidade.to_dict()), 201


@api_bp.get("/transportadoras")
@exige_login
def listar_transportadoras():
    transportadoras = db.session.scalars(
        db.select(Transportadora).order_by(Transportadora.nome)
    ).all()
    return jsonify({"transportadoras": [t.to_dict() for t in transportadoras]})
