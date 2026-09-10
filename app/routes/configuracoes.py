from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models import PAPEIS_USUARIO, User
from app.permissions import admin_required

config_bp = Blueprint("config", __name__, url_prefix="/configuracoes")
config_bp.before_request(login_required(lambda: None))
config_bp.before_request(admin_required(lambda: None))


@config_bp.route("/")
def index():
    usuarios = User.query.order_by(User.username).all()
    return render_template("configuracoes.html", usuarios=usuarios, papeis=PAPEIS_USUARIO)


@config_bp.route("/usuarios/novo", methods=["GET", "POST"])
def novo_usuario():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirmar_senha = request.form.get("confirmar_senha", "")
        role = request.form.get("role")

        if not username or not password:
            flash("Preencha usuário e senha.", "erro")
            return render_template("usuario_form.html", usuario=None, papeis=PAPEIS_USUARIO, username=username, role=role)

        if password != confirmar_senha:
            flash("As senhas não coincidem.", "erro")
            return render_template("usuario_form.html", usuario=None, papeis=PAPEIS_USUARIO, username=username, role=role)

        if role not in PAPEIS_USUARIO:
            flash("Selecione um papel válido.", "erro")
            return render_template("usuario_form.html", usuario=None, papeis=PAPEIS_USUARIO, username=username, role=role)

        if User.query.filter_by(username=username).first() is not None:
            flash("Esse usuário já existe.", "erro")
            return render_template("usuario_form.html", usuario=None, papeis=PAPEIS_USUARIO, username=username, role=role)

        usuario = User(username=username, role=role)
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()

        flash(f"Usuário '{username}' criado com sucesso.", "sucesso")
        return redirect(url_for("config.index"))

    return render_template("usuario_form.html", usuario=None, papeis=PAPEIS_USUARIO)


@config_bp.route("/usuarios/<int:user_id>/editar", methods=["GET", "POST"])
def editar_usuario(user_id):
    usuario = User.query.get_or_404(user_id)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        role = request.form.get("role")
        password = request.form.get("password", "")
        confirmar_senha = request.form.get("confirmar_senha", "")

        if not username:
            flash("Informe o usuário.", "erro")
            return render_template("usuario_form.html", usuario=usuario, papeis=PAPEIS_USUARIO)

        if role not in PAPEIS_USUARIO:
            flash("Selecione um papel válido.", "erro")
            return render_template("usuario_form.html", usuario=usuario, papeis=PAPEIS_USUARIO)

        if usuario.id == current_user.id and role != "admin":
            flash("Você não pode remover seu próprio acesso de administrador.", "erro")
            return render_template("usuario_form.html", usuario=usuario, papeis=PAPEIS_USUARIO)

        outro = User.query.filter_by(username=username).first()
        if outro is not None and outro.id != usuario.id:
            flash("Esse usuário já existe.", "erro")
            return render_template("usuario_form.html", usuario=usuario, papeis=PAPEIS_USUARIO)

        if password or confirmar_senha:
            if password != confirmar_senha:
                flash("As senhas não coincidem.", "erro")
                return render_template("usuario_form.html", usuario=usuario, papeis=PAPEIS_USUARIO)
            usuario.set_password(password)

        usuario.username = username
        usuario.role = role
        db.session.commit()

        flash(f"Usuário '{usuario.username}' atualizado.", "sucesso")
        return redirect(url_for("config.index"))

    return render_template("usuario_form.html", usuario=usuario, papeis=PAPEIS_USUARIO)


@config_bp.route("/usuarios/<int:user_id>/excluir", methods=["POST"])
def excluir_usuario(user_id):
    usuario = User.query.get_or_404(user_id)

    if usuario.id == current_user.id:
        flash("Você não pode excluir seu próprio usuário.", "erro")
        return redirect(url_for("config.index"))

    if usuario.is_admin and User.query.filter_by(role="admin").count() <= 1:
        flash("Não é possível excluir o único administrador do sistema.", "erro")
        return redirect(url_for("config.index"))

    nome = usuario.username
    db.session.delete(usuario)
    db.session.commit()
    flash(f"Usuário '{nome}' excluído.", "sucesso")
    return redirect(url_for("config.index"))
