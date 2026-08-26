"""Regras de cálculo do romaneio (pesagem individual de animais)."""

from dataclasses import dataclass
from typing import List, Optional

ARROBA_KG = 15.0


@dataclass
class ResumoRomaneio:
    quantidade_animais: int
    peso_total: float
    arrobas: float
    media_peso: Optional[float]
    menor_peso: Optional[float]
    maior_peso: Optional[float]
    valor_total: float


def calcular_resumo_romaneio(
    pesos: List[float], tipo_calculo: str, valor_unitario: float
) -> ResumoRomaneio:
    quantidade = len(pesos)
    peso_total = sum(pesos)
    arrobas = peso_total / ARROBA_KG

    if tipo_calculo == "arroba":
        valor_total = arrobas * valor_unitario
    else:
        valor_total = peso_total * valor_unitario

    return ResumoRomaneio(
        quantidade_animais=quantidade,
        peso_total=round(peso_total, 2),
        arrobas=round(arrobas, 2),
        media_peso=round(peso_total / quantidade, 2) if quantidade > 0 else None,
        menor_peso=min(pesos) if pesos else None,
        maior_peso=max(pesos) if pesos else None,
        valor_total=round(valor_total, 2),
    )


def resumo_do_romaneio(romaneio) -> ResumoRomaneio:
    pesos = [p.peso for p in romaneio.pesagens]
    return calcular_resumo_romaneio(pesos, romaneio.tipo_calculo, romaneio.valor_unitario)
