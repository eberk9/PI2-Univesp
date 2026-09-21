"""Recursos de apoio ao formulario: unidades e transportadoras."""
from flask import jsonify

from app.api import api_bp, exige_login
from app.extensions import db
from app.models import Transportadora, Unidade


@api_bp.get("/unidades")
@exige_login
def listar_unidades():
    unidades = db.session.scalars(
        db.select(Unidade).order_by(Unidade.bloco, Unidade.numero)
    ).all()
    return jsonify({"unidades": [u.to_dict() for u in unidades]})


@api_bp.get("/transportadoras")
@exige_login
def listar_transportadoras():
    transportadoras = db.session.scalars(
        db.select(Transportadora).order_by(Transportadora.nome)
    ).all()
    return jsonify({"transportadoras": [t.to_dict() for t in transportadoras]})
