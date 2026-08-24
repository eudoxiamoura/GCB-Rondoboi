from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import Compra, Lote

compras_bp = Blueprint("compras", __name__, url_prefix="/lotes/<int:lote_id>/compras")
compras_bp.before_request(login_required(lambda: None))


def _parse_data(valor):
    if not valor:
        return date.today()
    return datetime.strptime(valor, "%Y-%m-%d").date()


@compras_bp.route("/nova", methods=["POST"])
def nova(lote_id):
    lote = Lote.query.get_or_404(lote_id)

    compra = Compra(
        lote_id=lote.id,
        data=_parse_data(request.form.get("data")),
        fornecedor=request.form.get("fornecedor", "").strip(),
        quantidade=int(request.form.get("quantidade") or 0),
        valor_unitario=float(request.form.get("valor_unitario") or 0.0),
        frete=float(request.form.get("frete") or 0.0),
        comissao=float(request.form.get("comissao") or 0.0),
        outras_despesas=float(request.form.get("outras_despesas") or 0.0),
    )

    if not compra.fornecedor or compra.quantidade <= 0:
        flash("Informe o fornecedor e uma quantidade válida.", "erro")
        return redirect(url_for("lotes.detalhe", lote_id=lote.id))

    db.session.add(compra)
    db.session.commit()
    flash("Compra lançada.", "sucesso")
    return redirect(url_for("lotes.detalhe", lote_id=lote.id))


@compras_bp.route("/<int:compra_id>/editar", methods=["GET", "POST"])
def editar(lote_id, compra_id):
    compra = Compra.query.filter_by(id=compra_id, lote_id=lote_id).first_or_404()

    if request.method == "POST":
        fornecedor = request.form.get("fornecedor", "").strip()
        quantidade = int(request.form.get("quantidade") or 0)

        if not fornecedor or quantidade <= 0:
            flash("Informe o fornecedor e uma quantidade válida.", "erro")
            return render_template("editar_compra.html", compra=compra)

        compra.data = _parse_data(request.form.get("data"))
        compra.fornecedor = fornecedor
        compra.quantidade = quantidade
        compra.valor_unitario = float(request.form.get("valor_unitario") or 0.0)
        compra.frete = float(request.form.get("frete") or 0.0)
        compra.comissao = float(request.form.get("comissao") or 0.0)
        compra.outras_despesas = float(request.form.get("outras_despesas") or 0.0)
        db.session.commit()
        flash("Compra atualizada.", "sucesso")
        return redirect(url_for("lotes.detalhe", lote_id=lote_id))

    return render_template("editar_compra.html", compra=compra)


@compras_bp.route("/<int:compra_id>/excluir", methods=["POST"])
def excluir(lote_id, compra_id):
    compra = Compra.query.filter_by(id=compra_id, lote_id=lote_id).first_or_404()
    db.session.delete(compra)
    db.session.commit()
    flash("Compra removida.", "sucesso")
    return redirect(url_for("lotes.detalhe", lote_id=lote_id))
