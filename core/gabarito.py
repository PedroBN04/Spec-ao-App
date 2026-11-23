"""Gabarito para a revisão com o facilitador (v2).

Só aparece DEPOIS da exportação: categoria e feedback de cada bloco do catálogo usado, regras de
qualidade (genéricas + do tema), blocos não usados e uma SPEC de referência (os spec_defaults do tema).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core import checklist as ck
from core import executor as ex
from core.models import Theme


@dataclass(frozen=True)
class ItemPasso:
    n: int
    titulo: str
    categoria: str  # boa_pratica | armadilha | depende | livre
    feedback: str
    pergunta: str
    sugestao: str


def passos_comentados(tema: Theme, passos: list, blocos: dict) -> list[ItemPasso]:
    itens = []
    for n, passo in enumerate(passos, start=1):
        bloco = blocos.get(ex.uid(passo)) or ex.bloco_do_passo(tema, passo)
        if bloco.categoria == "livre":
            itens.append(ItemPasso(n, bloco.titulo, "livre",
                                   "Bloco personalizado: não há gabarito fixo. Discuta com o facilitador se ele "
                                   "atende à missão e o que ele muda nos números.", "", ""))
        else:
            sug = ""
            if bloco.sugestao:
                sug = f"Alternativa: {bloco.sugestao} — {tema.bloco(bloco.sugestao).titulo}"
            itens.append(ItemPasso(n, bloco.titulo, bloco.categoria, bloco.feedback, bloco.pergunta_reflexao, sug))
    return itens


def boas_praticas_nao_usadas(tema: Theme, passos: list) -> list:
    usados = {ex.id_catalogo(p) for p in passos}
    return [b for b in tema.blocos if b.categoria == "boa_pratica" and b.id not in usados]


def regras(tema: Theme, original: pd.DataFrame, df: pd.DataFrame, passos: list) -> list[ck.ResultadoCheck]:
    ids = [ex.id_catalogo(p) or ex.uid(p) for p in passos]
    return ck.avaliar(tema, original, df, ids)
