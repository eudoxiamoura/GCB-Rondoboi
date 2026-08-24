"""Regras de cálculo do lote (ver README, seção 'Regras de cálculo').

Todas as funções recebem valores já somados (não objetos do banco) para
poderem ser testadas isoladamente e reaproveitadas no rascunho de simulação.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ResumoLote:
    total_cabecas_compradas: int
    custo_total_lote: float
    custo_medio_cabeca: Optional[float]
    total_cabecas_vendidas: int
    receita_total: float
    sobra: int
    custo_sobra: Optional[float]
    lucro_bruto: float
    lucro_por_cabeca: Optional[float]
    lucro_liquido: float
    divisao_parceria: float


def calcular_resumo(
    total_cabecas_compradas: int,
    custo_total_lote: float,
    total_cabecas_vendidas: int,
    receita_total: float,
    despesas_extras: float,
    percentual_parceria: float,
) -> ResumoLote:
    custo_medio_cabeca = (
        custo_total_lote / total_cabecas_compradas
        if total_cabecas_compradas > 0
        else None
    )

    sobra = total_cabecas_compradas - total_cabecas_vendidas

    custo_sobra = (
        sobra * custo_medio_cabeca
        if sobra > 0 and custo_medio_cabeca is not None
        else None
    )

    lucro_bruto = receita_total - custo_total_lote

    lucro_por_cabeca = (
        lucro_bruto / total_cabecas_vendidas if total_cabecas_vendidas > 0 else None
    )

    lucro_liquido = lucro_bruto - despesas_extras

    divisao_parceria = lucro_liquido * (percentual_parceria / 100.0)

    return ResumoLote(
        total_cabecas_compradas=total_cabecas_compradas,
        custo_total_lote=round(custo_total_lote, 2),
        custo_medio_cabeca=round(custo_medio_cabeca, 2) if custo_medio_cabeca is not None else None,
        total_cabecas_vendidas=total_cabecas_vendidas,
        receita_total=round(receita_total, 2),
        sobra=sobra,
        custo_sobra=round(custo_sobra, 2) if custo_sobra is not None else None,
        lucro_bruto=round(lucro_bruto, 2),
        lucro_por_cabeca=round(lucro_por_cabeca, 2) if lucro_por_cabeca is not None else None,
        lucro_liquido=round(lucro_liquido, 2),
        divisao_parceria=round(divisao_parceria, 2),
    )


def resumo_do_lote(lote) -> ResumoLote:
    """Monta o ResumoLote a partir de um objeto Lote já carregado do banco."""
    total_comprado = sum(c.quantidade for c in lote.compras)
    total_comprado += sum(s.quantidade for s in lote.sobras_recebidas)

    custo_total = sum(c.custo_total for c in lote.compras)
    custo_total += sum(s.quantidade * s.custo_medio_herdado for s in lote.sobras_recebidas)

    total_vendido = sum(v.quantidade for v in lote.vendas)
    receita_total = sum(v.total_liquido for v in lote.vendas)

    return calcular_resumo(
        total_cabecas_compradas=total_comprado,
        custo_total_lote=custo_total,
        total_cabecas_vendidas=total_vendido,
        receita_total=receita_total,
        despesas_extras=lote.despesas_extras or 0.0,
        percentual_parceria=lote.percentual_parceria or 0.0,
    )


LIMITE_DIFERENCA_MEDIA = 0.4  # 40%


def formatar_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def alerta_preco_venda(valor_unitario: float, custo_medio_cabeca: Optional[float]) -> Optional[str]:
    """Retorna uma mensagem de alerta se o valor de venda por cabeça estiver
    abaixo do custo médio do lote, ou muito diferente dele (> 40%). Não
    bloqueia o lançamento — é só um aviso para o usuário conferir o valor.
    """
    if not custo_medio_cabeca:
        return None

    if valor_unitario < custo_medio_cabeca:
        return (
            f"Atenção: o valor de venda ({formatar_brl(valor_unitario)}) está abaixo do "
            f"custo médio por cabeça deste lote ({formatar_brl(custo_medio_cabeca)})."
        )

    diferenca = abs(valor_unitario - custo_medio_cabeca) / custo_medio_cabeca
    if diferenca > LIMITE_DIFERENCA_MEDIA:
        return (
            f"Atenção: o valor de venda ({formatar_brl(valor_unitario)}) está "
            f"{diferenca * 100:.0f}% diferente do custo médio por cabeça deste lote "
            f"({formatar_brl(custo_medio_cabeca)}). Confira se o valor está correto."
        )

    return None


def simular_venda(lote, quantidade: int, valor_unitario: float, frete: float, comissao: float, gta: float) -> ResumoLote:
    """Calcula o resumo do lote COMO SE a venda informada já tivesse sido lançada,
    sem gravar nada no banco. Usado na tela de simulação/rascunho.
    """
    total_comprado = sum(c.quantidade for c in lote.compras)
    total_comprado += sum(s.quantidade for s in lote.sobras_recebidas)

    custo_total = sum(c.custo_total for c in lote.compras)
    custo_total += sum(s.quantidade * s.custo_medio_herdado for s in lote.sobras_recebidas)

    valor_total_simulado = quantidade * valor_unitario
    total_liquido_simulado = valor_total_simulado - frete - comissao - gta

    total_vendido = sum(v.quantidade for v in lote.vendas) + quantidade
    receita_total = sum(v.total_liquido for v in lote.vendas) + total_liquido_simulado

    return calcular_resumo(
        total_cabecas_compradas=total_comprado,
        custo_total_lote=custo_total,
        total_cabecas_vendidas=total_vendido,
        receita_total=receita_total,
        despesas_extras=lote.despesas_extras or 0.0,
        percentual_parceria=lote.percentual_parceria or 0.0,
    )
