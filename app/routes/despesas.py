from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import DespesaLote, Lote
from app.permissions import bloquear_escrita_visualizacao

despesas_bp = Blueprint("despesas", __name__, url_prefix="/lotes/<int:lote_id>/despesas")
despesas_bp.before_request(login_required(lambda: None))
despesas_bp.before_request(bloquear_escrita_visualizacao)


def _parse_data(valor):
    if not valor:
        return date.today()
    return datetime.strptime(valor, "%Y-%m-%d").date()


@despesas_bp.route("/nova", methods=["POST"])
def nova(lote_id):
    lote = Lote.query.get_or_404(lote_id)

    despesa = DespesaLote(
        lote_id=lote.id,
        data=_parse_data(request.form.get("data")),
        descricao=request.form.get("descricao", "").strip(),
        valor=float(request.form.get("valor") or 0.0),
    )

    if not despesa.descricao or despesa.valor <= 0:
        flash("Informe a descrição e um valor válido.", "erro")
        return redirect(url_for("lotes.detalhe", lote_id=lote.id))

    db.session.add(despesa)
    db.session.commit()
    flash("Despesa lançada.", "sucesso")
    return redirect(url_for("lotes.detalhe", lote_id=lote.id))


@despesas_bp.route("/<int:despesa_id>/editar", methods=["GET", "POST"])
def editar(lote_id, despesa_id):
    despesa = DespesaLote.query.filter_by(id=despesa_id, lote_id=lote_id).first_or_404()

    if request.method == "POST":
        descricao = request.form.get("descricao", "").strip()
        valor = float(request.form.get("valor") or 0.0)

        if not descricao or valor <= 0:
            flash("Informe a descrição e um valor válido.", "erro")
            return render_template("editar_despesa.html", despesa=despesa)

        despesa.data = _parse_data(request.form.get("data"))
        despesa.descricao = descricao
        despesa.valor = valor
        db.session.commit()
        flash("Despesa atualizada.", "sucesso")
        return redirect(url_for("lotes.detalhe", lote_id=lote_id))

    return render_template("editar_despesa.html", despesa=despesa)


@despesas_bp.route("/<int:despesa_id>/excluir", methods=["POST"])
def excluir(lote_id, despesa_id):
    despesa = DespesaLote.query.filter_by(id=despesa_id, lote_id=lote_id).first_or_404()
    db.session.delete(despesa)
    db.session.commit()
    flash("Despesa removida.", "sucesso")
    return redirect(url_for("lotes.detalhe", lote_id=lote_id))
