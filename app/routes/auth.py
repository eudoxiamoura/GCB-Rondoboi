from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from app import db
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash("Usuário ou senha inválidos.", "erro")
            return render_template("login.html", username=username)

        login_user(user)
        destino = request.args.get("next") or url_for("lotes.index")
        return redirect(destino)

    return render_template("login.html")


@auth_bp.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirmar_senha = request.form.get("confirmar_senha", "")

        if not username or not password:
            flash("Preencha usuário e senha.", "erro")
            return render_template("registrar.html", username=username)

        if password != confirmar_senha:
            flash("As senhas não coincidem.", "erro")
            return render_template("registrar.html", username=username)

        if User.query.filter_by(username=username).first() is not None:
            flash("Esse usuário já existe.", "erro")
            return render_template("registrar.html", username=username)

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Conta criada com sucesso.", "sucesso")
        return redirect(url_for("lotes.index"))

    return render_template("registrar.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Você saiu do sistema.", "sucesso")
    return redirect(url_for("auth.login"))
