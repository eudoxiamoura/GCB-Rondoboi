from datetime import date, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        # pbkdf2:sha256 explícito porque o hashlib do Python do sistema (macOS)
        # muitas vezes não tem suporte a scrypt, o padrão do Werkzeug.
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Lote(db.Model):
    __tablename__ = "lotes"

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False)
    descricao = db.Column(db.String(120), nullable=False, default="")
    data_criacao = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), nullable=False, default="aberto")  # aberto | encerrado
    percentual_parceria = db.Column(db.Float, nullable=False, default=50.0)
    despesas_extras = db.Column(db.Float, nullable=False, default=0.0)

    # marca lotes criados via "duplicar como rascunho"
    is_rascunho = db.Column(db.Boolean, nullable=False, default=False)
    lote_original_id = db.Column(db.Integer, db.ForeignKey("lotes.id"), nullable=True)

    compras = db.relationship(
        "Compra", backref="lote", cascade="all, delete-orphan", lazy=True
    )
    vendas = db.relationship(
        "Venda", backref="lote", cascade="all, delete-orphan", lazy=True
    )
    sobras_recebidas = db.relationship(
        "SobraTransferida",
        foreign_keys="SobraTransferida.lote_destino_id",
        backref="lote_destino",
        cascade="all, delete-orphan",
        lazy=True,
    )

    @property
    def nome_completo(self):
        if self.descricao:
            return f"{self.numero} - {self.descricao}"
        return self.numero


class Compra(db.Model):
    __tablename__ = "compras"

    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, db.ForeignKey("lotes.id"), nullable=False)
    data = db.Column(db.Date, nullable=False, default=date.today)
    fornecedor = db.Column(db.String(120), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False, default=0.0)
    frete = db.Column(db.Float, nullable=False, default=0.0)
    comissao = db.Column(db.Float, nullable=False, default=0.0)
    outras_despesas = db.Column(db.Float, nullable=False, default=0.0)

    @property
    def valor_total(self):
        return self.quantidade * self.valor_unitario

    @property
    def custo_total(self):
        return self.valor_total + self.frete + self.comissao + self.outras_despesas


class Venda(db.Model):
    __tablename__ = "vendas"

    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, db.ForeignKey("lotes.id"), nullable=False)
    data = db.Column(db.Date, nullable=False, default=date.today)
    comprador = db.Column(db.String(120), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False, default=0.0)
    frete = db.Column(db.Float, nullable=False, default=0.0)
    comissao = db.Column(db.Float, nullable=False, default=0.0)
    gta = db.Column(db.Float, nullable=False, default=0.0)

    # True quando este registro representa a sobra transferida para outro
    # lote, lançada aqui como se fosse uma venda para fechar o lucro deste lote.
    eh_transferencia_sobra = db.Column(db.Boolean, nullable=False, default=False)

    @property
    def valor_total(self):
        return self.quantidade * self.valor_unitario

    @property
    def total_liquido(self):
        return self.valor_total - self.frete - self.comissao - self.gta


class SobraTransferida(db.Model):
    __tablename__ = "sobras_transferidas"

    id = db.Column(db.Integer, primary_key=True)
    lote_origem_id = db.Column(db.Integer, db.ForeignKey("lotes.id"), nullable=False)
    lote_destino_id = db.Column(db.Integer, db.ForeignKey("lotes.id"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    custo_medio_herdado = db.Column(db.Float, nullable=False, default=0.0)

    lote_origem = db.relationship("Lote", foreign_keys=[lote_origem_id])


class Romaneio(db.Model):
    __tablename__ = "romaneios"

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False)
    data_criacao = db.Column(db.Date, nullable=False, default=date.today)
    tipo_calculo = db.Column(db.String(10), nullable=False)  # "peso" | "arroba"
    valor_unitario = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), nullable=False, default="em_andamento")  # em_andamento | finalizado

    pesagens = db.relationship(
        "PesagemIndividual",
        backref="romaneio",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="PesagemIndividual.id",
    )

    @property
    def nome_completo(self):
        return f"Romaneio {self.numero}"


class PesagemIndividual(db.Model):
    __tablename__ = "pesagens_individuais"

    id = db.Column(db.Integer, primary_key=True)
    romaneio_id = db.Column(db.Integer, db.ForeignKey("romaneios.id"), nullable=False)
    peso = db.Column(db.Float, nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
