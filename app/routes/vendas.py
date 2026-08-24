from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.calculos import alerta_preco_venda, resumo_do_lote, simular_venda
from app.models import Lote, Venda

vendas_bp = Blueprint("vendas", __name__, url_prefix="/lotes/<int:lote_id>/vendas")
vendas_bp.before_request(login_required(lambda: None))


def _parse_data(valor):
    if not valor:
        return date.today()
    return datetime.strptime(valor, "%Y-%m-%d").date()


@vendas_bp.route("/nova", methods=["POST"])
def nova(lote_id):
    lote = Lote.query.get_or_404(lote_id)

    venda = Venda(
        lote_id=lote.id,
        data=_parse_data(request.form.get("data")),
        comprador=request.form.get("comprador", "").strip(),
        quantidade=int(request.form.get("quantidade") or 0),
        valor_unitario=float(request.form.get("valor_unitario") or 0.0),
        frete=float(request.form.get("frete") or 0.0),
        comissao=float(request.form.get("comissao") or 0.0),
        gta=float(request.form.get("gta") or 0.0),
    )

    if not venda.comprador or venda.quantidade <= 0:
        flash("Informe o comprador e uma quantidade válida.", "erro")
        return redirect(url_for("lotes.detalhe", lote_id=lote.id))

    resumo_atual = resumo_do_lote(lote)
    if venda.quantidade > resumo_atual.sobra:
        flash(
            f"Quantidade maior que a sobra disponível ({resumo_atual.sobra} cabeça(s)).",
            "erro",
        )
        return redirect(url_for("lotes.detalhe", lote_id=lote.id))

    aviso = alerta_preco_venda(venda.valor_unitario, resumo_atual.custo_medio_cabeca)
    if aviso:
        flash(aviso, "aviso")

    db.session.add(venda)
    db.session.commit()
    flash("Venda lançada.", "sucesso")
    return redirect(url_for("lotes.detalhe", lote_id=lote.id))


@vendas_bp.route("/<int:venda_id>/editar", methods=["GET", "POST"])
def editar(lote_id, venda_id):
    venda = Venda.query.filter_by(id=venda_id, lote_id=lote_id).first_or_404()
    lote = Lote.query.get_or_404(lote_id)

    if request.method == "POST":
        comprador = request.form.get("comprador", "").strip()
        quantidade = int(request.form.get("quantidade") or 0)
        valor_unitario = float(request.form.get("valor_unitario") or 0.0)

        if not comprador or quantidade <= 0:
            flash("Informe o comprador e uma quantidade válida.", "erro")
            return render_template("editar_venda.html", venda=venda)

        # sobra disponível desconsiderando a própria venda que está sendo editada
        resumo_sem_esta_venda = resumo_do_lote(lote)
        sobra_disponivel = resumo_sem_esta_venda.sobra + venda.quantidade
        if quantidade > sobra_disponivel:
            flash(f"Quantidade maior que a sobra disponível ({sobra_disponivel} cabeça(s)).", "erro")
            return render_template("editar_venda.html", venda=venda)

        venda.data = _parse_data(request.form.get("data"))
        venda.comprador = comprador
        venda.quantidade = quantidade
        venda.valor_unitario = valor_unitario
        venda.frete = float(request.form.get("frete") or 0.0)
        venda.comissao = float(request.form.get("comissao") or 0.0)
        venda.gta = float(request.form.get("gta") or 0.0)

        aviso = alerta_preco_venda(valor_unitario, resumo_sem_esta_venda.custo_medio_cabeca)
        if aviso:
            flash(aviso, "aviso")

        db.session.commit()
        flash("Venda atualizada.", "sucesso")
        return redirect(url_for("lotes.detalhe", lote_id=lote_id))

    return render_template("editar_venda.html", venda=venda)


@vendas_bp.route("/<int:venda_id>/excluir", methods=["POST"])
def excluir(lote_id, venda_id):
    venda = Venda.query.filter_by(id=venda_id, lote_id=lote_id).first_or_404()
    db.session.delete(venda)
    db.session.commit()
    flash("Venda removida.", "sucesso")
    return redirect(url_for("lotes.detalhe", lote_id=lote_id))


@vendas_bp.route("/simular", methods=["GET", "POST"])
def simular(lote_id):
    """Simula uma venda e mostra o resultado sem gravar nada no banco."""
    lote = Lote.query.get_or_404(lote_id)
    resultado = None
    dados_form = {}

    if request.method == "POST":
        dados_form = request.form
        quantidade = int(request.form.get("quantidade") or 0)
        valor_unitario = float(request.form.get("valor_unitario") or 0.0)
        frete = float(request.form.get("frete") or 0.0)
        comissao = float(request.form.get("comissao") or 0.0)
        gta = float(request.form.get("gta") or 0.0)

        resultado = simular_venda(
            lote,
            quantidade=quantidade,
            valor_unitario=valor_unitario,
            frete=frete,
            comissao=comissao,
            gta=gta,
        )

        aviso = alerta_preco_venda(valor_unitario, resultado.custo_medio_cabeca)
        if aviso:
            flash(aviso, "aviso")

    return render_template(
        "simular_venda.html", lote=lote, resultado=resultado, dados_form=dados_form
    )
