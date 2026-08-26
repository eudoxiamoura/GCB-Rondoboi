import re
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import PesagemIndividual, Romaneio
from app.romaneio_calculos import resumo_do_romaneio

romaneio_bp = Blueprint("romaneio", __name__, url_prefix="/romaneio")
romaneio_bp.before_request(login_required(lambda: None))


def _proximo_numero_romaneio():
    maior = 0
    for romaneio in Romaneio.query.all():
        m = re.match(r"(\d+)", romaneio.numero)
        if m:
            maior = max(maior, int(m.group(1)))
    return f"{maior + 1:03d}"


@romaneio_bp.route("/")
def index():
    romaneios = Romaneio.query.order_by(Romaneio.id.desc()).all()
    resumos = {romaneio.id: resumo_do_romaneio(romaneio) for romaneio in romaneios}
    return render_template("romaneio_lista.html", romaneios=romaneios, resumos=resumos)


@romaneio_bp.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        tipo_calculo = request.form.get("tipo_calculo")
        valor_unitario = float(request.form.get("valor_unitario") or 0.0)

        if tipo_calculo not in ("peso", "arroba"):
            flash("Selecione se o cálculo é por peso ou por arroba.", "erro")
            return render_template("romaneio_novo.html")

        if valor_unitario <= 0:
            flash("Informe um valor válido.", "erro")
            return render_template("romaneio_novo.html")

        romaneio = Romaneio(
            numero=_proximo_numero_romaneio(),
            data_criacao=date.today(),
            tipo_calculo=tipo_calculo,
            valor_unitario=valor_unitario,
        )
        db.session.add(romaneio)
        db.session.commit()
        return redirect(url_for("romaneio.pesar", romaneio_id=romaneio.id))

    return render_template("romaneio_novo.html")


@romaneio_bp.route("/<int:romaneio_id>/pesar")
def pesar(romaneio_id):
    romaneio = Romaneio.query.get_or_404(romaneio_id)
    if romaneio.status == "finalizado":
        return redirect(url_for("romaneio.detalhe", romaneio_id=romaneio.id))

    quantidade = len(romaneio.pesagens)
    ultimo_peso = romaneio.pesagens[-1].peso if romaneio.pesagens else None
    return render_template(
        "romaneio_pesar.html", romaneio=romaneio, quantidade=quantidade, ultimo_peso=ultimo_peso
    )


@romaneio_bp.route("/<int:romaneio_id>/pesar/adicionar", methods=["POST"])
def adicionar_peso(romaneio_id):
    romaneio = Romaneio.query.get_or_404(romaneio_id)
    peso = float(request.form.get("peso") or 0.0)

    if peso <= 0:
        flash("Informe um peso válido.", "erro")
        return redirect(url_for("romaneio.pesar", romaneio_id=romaneio.id))

    db.session.add(PesagemIndividual(romaneio_id=romaneio.id, peso=peso))
    db.session.commit()
    return redirect(url_for("romaneio.pesar", romaneio_id=romaneio.id))


@romaneio_bp.route("/<int:romaneio_id>/pesagens/<int:pesagem_id>/excluir", methods=["POST"])
def excluir_pesagem(romaneio_id, pesagem_id):
    pesagem = PesagemIndividual.query.filter_by(id=pesagem_id, romaneio_id=romaneio_id).first_or_404()
    db.session.delete(pesagem)
    db.session.commit()
    flash("Peso removido.", "sucesso")
    return redirect(url_for("romaneio.detalhe", romaneio_id=romaneio_id))


@romaneio_bp.route("/<int:romaneio_id>/finalizar", methods=["POST"])
def finalizar(romaneio_id):
    romaneio = Romaneio.query.get_or_404(romaneio_id)

    if not romaneio.pesagens:
        flash("Registre pelo menos um peso antes de finalizar.", "erro")
        return redirect(url_for("romaneio.pesar", romaneio_id=romaneio.id))

    romaneio.status = "finalizado"
    db.session.commit()
    return redirect(url_for("romaneio.detalhe", romaneio_id=romaneio.id))


@romaneio_bp.route("/<int:romaneio_id>/reabrir", methods=["POST"])
def reabrir(romaneio_id):
    romaneio = Romaneio.query.get_or_404(romaneio_id)
    romaneio.status = "em_andamento"
    db.session.commit()
    return redirect(url_for("romaneio.pesar", romaneio_id=romaneio.id))


@romaneio_bp.route("/<int:romaneio_id>")
def detalhe(romaneio_id):
    romaneio = Romaneio.query.get_or_404(romaneio_id)
    resumo = resumo_do_romaneio(romaneio)
    return render_template("romaneio_detalhe.html", romaneio=romaneio, resumo=resumo)
