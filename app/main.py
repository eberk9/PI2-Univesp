"""Rotas das paginas HTML. Os dados vem da API, consumida pelo JavaScript."""
from flask import Blueprint, abort, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Encomenda, Transportadora, Unidade

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def inicio():
    if current_user.e_morador():
        return redirect(url_for("main.minhas_encomendas"))
    return redirect(url_for("main.pendentes"))


@main_bp.route("/encomendas/nova")
@login_required
def nova_encomenda():
    if current_user.e_morador():
        abort(403)
    unidades = db.session.scalars(
        db.select(Unidade).order_by(Unidade.bloco, Unidade.numero)
    ).all()
    transportadoras = db.session.scalars(
        db.select(Transportadora).order_by(Transportadora.nome)
    ).all()
    return render_template(
        "nova_encomenda.html", unidades=unidades, transportadoras=transportadoras
    )


@main_bp.route("/encomendas/pendentes")
@login_required
def pendentes():
    if current_user.e_morador():
        abort(403)
    return render_template("pendentes.html")


@main_bp.route("/encomendas/<int:encomenda_id>")
@login_required
def detalhe(encomenda_id):
    encomenda = db.session.get(Encomenda, encomenda_id)
    if encomenda is None:
        abort(404)
    if current_user.e_morador() and encomenda.unidade_id != current_user.unidade_id:
        abort(403)
    return render_template("detalhe.html", encomenda=encomenda)


@main_bp.route("/minhas-encomendas")
@login_required
def minhas_encomendas():
    return render_template("minhas_encomendas.html")
