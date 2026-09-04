import os

from flask import Flask, render_template
from flask_login import LoginManager, login_required
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Faça login para acessar o sistema."
login_manager.login_message_category = "erro"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(os.path.join(app.root_path, "..", "instance"), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.lotes import lotes_bp
    from app.routes.compras import compras_bp
    from app.routes.vendas import vendas_bp
    from app.routes.romaneio import romaneio_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(lotes_bp)
    app.register_blueprint(compras_bp)
    app.register_blueprint(vendas_bp)
    app.register_blueprint(romaneio_bp)

    from app import models  # noqa: F401 - garante que os modelos sejam registrados

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    from app.calculos import formatar_brl, resumo_do_lote

    @app.route("/")
    @login_required
    def index():
        lotes = models.Lote.query.filter_by(is_rascunho=False).all()
        resumos = {lote.id: resumo_do_lote(lote) for lote in lotes}
        total_estoque = sum(resumo.sobra for resumo in resumos.values())

        lotes_abertos = [lote for lote in lotes if lote.status == "aberto"]
        lotes_abertos.sort(key=lambda lote: lote.data_criacao, reverse=True)
        lotes_machos = [lote for lote in lotes_abertos if lote.sexo == "macho"]
        lotes_femeas = [lote for lote in lotes_abertos if lote.sexo == "femea"]
        total_em_aberto = sum(resumos[lote.id].custo_total_lote for lote in lotes_abertos)

        return render_template(
            "inicio.html",
            total_em_aberto=total_em_aberto,
            total_estoque=total_estoque,
            resumos=resumos,
            lotes_machos=lotes_machos,
            lotes_femeas=lotes_femeas,
        )

    @app.template_filter("brl")
    def brl(value):
        if value is None:
            return "—"
        return formatar_brl(value)

    @app.cli.command("create-user")
    def create_user_command():
        """Cria (ou redefine a senha de) um usuário para acessar o sistema."""
        import getpass

        username = input("Usuário: ").strip()
        password = getpass.getpass("Senha: ")

        if not username or not password:
            print("Usuário e senha não podem ser vazios.")
            return

        user = models.User.query.filter_by(username=username).first()
        if user is None:
            user = models.User(username=username)
            db.session.add(user)
            acao = "criado"
        else:
            acao = "senha redefinida"

        user.set_password(password)
        db.session.commit()
        print(f"Usuário '{username}' {acao} com sucesso.")

    return app
