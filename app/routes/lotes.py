import re
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.calculos import formatar_brl, resumo_do_lote
from app.models import Compra, Lote, SobraTransferida, Venda

lotes_bp = Blueprint("lotes", __name__, url_prefix="/lotes")
lotes_bp.before_request(login_required(lambda: None))

MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def _proximo_numero_lote():
    """Gera o próximo número sequencial de lote (ex: 001, 002, 003...),
    olhando o maior número já usado entre os lotes reais (não-rascunho)."""
    maior = 0
    for lote in Lote.query.filter_by(is_rascunho=False).all():
        m = re.match(r"(\d+)", lote.numero)
        if m:
            maior = max(maior, int(m.group(1)))
    return f"{maior + 1:03d}"


def _parse_data_compra(valor):
    if not valor:
        return date.today()
    return date.fromisoformat(valor)


@lotes_bp.route("/")
def index():
    status_filtro = request.args.get("status")
    query = Lote.query.filter_by(is_rascunho=False)
    if status_filtro in ("aberto", "encerrado"):
        query = query.filter_by(status=status_filtro)
    lotes = query.order_by(Lote.data_criacao.desc()).all()
    resumos = {lote.id: resumo_do_lote(lote) for lote in lotes}
    return render_template("lotes_lista.html", lotes=lotes, resumos=resumos, status_filtro=status_filtro)


@lotes_bp.route("/comprar", methods=["GET", "POST"])
def comprar():
    """Lança uma compra sem precisar escolher o lote: cai automaticamente
    no lote em aberto do sexo escolhido (ou cria um novo, se não houver)."""
    if request.method == "POST":
        sexo = request.form.get("sexo")
        if sexo not in ("macho", "femea"):
            flash("Selecione se a compra é de machos ou fêmeas.", "erro")
            return render_template("nova_compra.html")

        fornecedor = request.form.get("fornecedor", "").strip()
        quantidade = int(request.form.get("quantidade") or 0)

        if not fornecedor or quantidade <= 0:
            flash("Informe o fornecedor e uma quantidade válida.", "erro")
            return render_template("nova_compra.html")

        lote = (
            Lote.query.filter_by(status="aberto", sexo=sexo, is_rascunho=False)
            .order_by(Lote.data_criacao.desc())
            .first()
        )
        if lote is None:
            hoje = date.today()
            lote = Lote(
                numero=_proximo_numero_lote(),
                descricao=f"{'Machos' if sexo == 'macho' else 'Fêmeas'} - {MESES_PT[hoje.month - 1]}",
                sexo=sexo,
                data_criacao=hoje,
            )
            db.session.add(lote)
            db.session.flush()

        db.session.add(Compra(
            lote_id=lote.id,
            data=_parse_data_compra(request.form.get("data")),
            fornecedor=fornecedor,
            quantidade=quantidade,
            valor_unitario=float(request.form.get("valor_unitario") or 0.0),
            frete=float(request.form.get("frete") or 0.0),
            comissao=float(request.form.get("comissao") or 0.0),
            outras_despesas=float(request.form.get("outras_despesas") or 0.0),
        ))
        db.session.commit()
        flash(f"Compra lançada no lote {lote.nome_completo}.", "sucesso")
        return redirect(url_for("lotes.detalhe", lote_id=lote.id))

    return render_template("nova_compra.html")


@lotes_bp.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        descricao = request.form.get("descricao", "").strip()
        sexo = request.form.get("sexo") if request.form.get("sexo") in ("macho", "femea") else "macho"

        lote = Lote(
            numero=_proximo_numero_lote(),
            descricao=descricao,
            sexo=sexo,
            data_criacao=date.today(),
        )
        db.session.add(lote)
        db.session.commit()
        flash(f"Lote {lote.nome_completo} criado.", "sucesso")
        return redirect(url_for("lotes.detalhe", lote_id=lote.id))

    return render_template("novo_lote.html", proximo_numero=_proximo_numero_lote())


@lotes_bp.route("/<int:lote_id>")
def detalhe(lote_id):
    lote = Lote.query.get_or_404(lote_id)
    resumo = resumo_do_lote(lote)
    return render_template("lote_detalhe.html", lote=lote, resumo=resumo)


@lotes_bp.route("/<int:lote_id>/excluir", methods=["POST"])
def excluir(lote_id):
    lote = Lote.query.get_or_404(lote_id)

    sobra_transferida_para = SobraTransferida.query.filter_by(lote_origem_id=lote.id).first()
    if sobra_transferida_para is not None:
        flash(
            f"Não é possível excluir: a sobra deste lote já foi transferida para o lote "
            f"{sobra_transferida_para.lote_destino.nome_completo}.",
            "erro",
        )
        return redirect(url_for("lotes.detalhe", lote_id=lote.id))

    nome = lote.nome_completo
    db.session.delete(lote)
    db.session.commit()
    flash(f"Lote {nome} excluído.", "sucesso")
    return redirect(url_for("lotes.index"))


@lotes_bp.route("/<int:lote_id>/editar", methods=["GET", "POST"])
def editar(lote_id):
    lote = Lote.query.get_or_404(lote_id)
    if request.method == "POST":
        lote.descricao = request.form.get("descricao", "").strip()
        if request.form.get("sexo") in ("macho", "femea"):
            lote.sexo = request.form.get("sexo")
        lote.percentual_parceria = float(request.form.get("percentual_parceria") or 50.0)
        lote.despesas_extras = float(request.form.get("despesas_extras") or 0.0)
        lote.status = request.form.get("status", lote.status)
        db.session.commit()
        flash("Lote atualizado.", "sucesso")
        return redirect(url_for("lotes.detalhe", lote_id=lote.id))
    return render_template("editar_lote.html", lote=lote)


@lotes_bp.route("/<int:lote_id>/duplicar", methods=["POST"])
def duplicar(lote_id):
    """Cria uma cópia editável do lote (rascunho) para testar cenários
    sem alterar os dados originais."""
    original = Lote.query.get_or_404(lote_id)

    copia = Lote(
        numero=f"{original.numero}-RASCUNHO",
        descricao=original.descricao,
        data_criacao=date.today(),
        status="aberto",
        sexo=original.sexo,
        percentual_parceria=original.percentual_parceria,
        despesas_extras=original.despesas_extras,
        is_rascunho=True,
        lote_original_id=original.id,
    )
    db.session.add(copia)
    db.session.flush()

    for compra in original.compras:
        db.session.add(
            type(compra)(
                lote_id=copia.id,
                data=compra.data,
                fornecedor=compra.fornecedor,
                quantidade=compra.quantidade,
                valor_unitario=compra.valor_unitario,
                frete=compra.frete,
                comissao=compra.comissao,
                outras_despesas=compra.outras_despesas,
            )
        )

    for venda in original.vendas:
        db.session.add(
            type(venda)(
                lote_id=copia.id,
                data=venda.data,
                comprador=venda.comprador,
                quantidade=venda.quantidade,
                valor_unitario=venda.valor_unitario,
                frete=venda.frete,
                comissao=venda.comissao,
                gta=venda.gta,
            )
        )

    for sobra in original.sobras_recebidas:
        db.session.add(
            SobraTransferida(
                lote_origem_id=sobra.lote_origem_id,
                lote_destino_id=copia.id,
                quantidade=sobra.quantidade,
                custo_medio_herdado=sobra.custo_medio_herdado,
            )
        )

    db.session.commit()
    flash(f"Rascunho {copia.nome_completo} criado a partir do lote {original.nome_completo}.", "sucesso")
    return redirect(url_for("lotes.detalhe", lote_id=copia.id))


@lotes_bp.route("/<int:lote_id>/transferir-sobra", methods=["GET", "POST"])
def transferir_sobra(lote_id):
    """Cria um lote novo levando a sobra (cabeças não vendidas) do lote
    de origem como ponto de partida, com o custo médio já conhecido."""
    origem = Lote.query.get_or_404(lote_id)
    resumo = resumo_do_lote(origem)

    if resumo.sobra <= 0:
        flash("Este lote não tem sobra para transferir.", "erro")
        return redirect(url_for("lotes.detalhe", lote_id=origem.id))

    if request.method == "POST":
        descricao = request.form.get("descricao", "").strip()
        quantidade = int(request.form.get("quantidade") or resumo.sobra)
        valor_unitario = float(request.form.get("valor_unitario") or 0.0)

        if quantidade <= 0 or quantidade > resumo.sobra:
            flash(f"Quantidade inválida. A sobra disponível é {resumo.sobra}.", "erro")
            return redirect(url_for("lotes.transferir_sobra", lote_id=origem.id))

        if resumo.custo_medio_cabeca is not None and valor_unitario < resumo.custo_medio_cabeca:
            flash(
                f"O valor por cabeça ({formatar_brl(valor_unitario)}) não pode ser inferior "
                f"ao que está custando ({formatar_brl(resumo.custo_medio_cabeca)}).",
                "erro",
            )
            return redirect(url_for("lotes.transferir_sobra", lote_id=origem.id))

        novo_lote = Lote(
            numero=_proximo_numero_lote(),
            descricao=descricao,
            sexo=origem.sexo,
            data_criacao=date.today(),
        )
        db.session.add(novo_lote)
        db.session.flush()

        db.session.add(
            SobraTransferida(
                lote_origem_id=origem.id,
                lote_destino_id=novo_lote.id,
                quantidade=quantidade,
                custo_medio_herdado=valor_unitario,
            )
        )

        # Lança a sobra transferida como se fosse uma venda no lote de origem,
        # para que o lucro deste lote seja calculado considerando esse valor.
        db.session.add(
            Venda(
                lote_id=origem.id,
                data=date.today(),
                comprador=f"Sobra transferida → lote {novo_lote.nome_completo}",
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                eh_transferencia_sobra=True,
            )
        )

        db.session.commit()
        flash(f"Sobra de {quantidade} cabeça(s) transferida para o lote {novo_lote.nome_completo}.", "sucesso")
        return redirect(url_for("lotes.detalhe", lote_id=novo_lote.id))

    return render_template(
        "transferir_sobra.html", lote=origem, resumo=resumo, proximo_numero=_proximo_numero_lote()
    )
