"""Autenticacao por sessao: login e logout."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.models import Usuario

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.inicio"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        senha = request.form.get("senha") or ""
        usuario = db.session.scalar(
            db.select(Usuario).filter_by(email=email)
        )
        if usuario is None or not usuario.conferir_senha(senha):
            flash("E-mail ou senha incorretos.", "erro")
            return render_template("login.html", email=email), 401
        if not usuario.ativo:
            flash("Este usuario esta inativo. Procure o sindico.", "erro")
            return render_template("login.html", email=email), 403

        login_user(usuario)
        destino = request.args.get("next")
        if destino and destino.startswith("/"):
            return redirect(destino)
        return redirect(url_for("main.inicio"))

    return render_template("login.html", email="")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sessao encerrada.", "ok")
    return redirect(url_for("auth.login"))
