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
    observacao: str = ""  # explicação de efeito colateral (ex.: linhas repetidas que surgiram)


def _observacao(resultado) -> str:
    if resultado is None or resultado.repetidas_antes is None:
        return ""
    if resultado.repetidas_depois > resultado.repetidas_antes and resultado.colunas_removidas:
        return (f"Depois deste passo surgiram {resultado.repetidas_depois - resultado.repetidas_antes} linhas "
                "repetidas. Isso acontece quando sai uma coluna que diferenciava as linhas (como um código de "
                "identificação): registros diferentes, com perfil parecido, passam a parecer iguais na tabela. "
                "Não são duplicatas de verdade.")
    return ""


def passos_comentados(tema: Theme, passos: list, blocos: dict, resultados: dict | None = None) -> list[ItemPasso]:
    itens = []
    for n, passo in enumerate(passos, start=1):
        obs = _observacao((resultados or {}).get(ex.uid(passo)))
        bloco = blocos.get(ex.uid(passo)) or ex.bloco_do_passo(tema, passo)
        if bloco.categoria == "livre":
            itens.append(ItemPasso(n, bloco.titulo, "livre",
                                   "Bloco personalizado: não há gabarito fixo. Discuta com o facilitador se ele "
                                   "atende à missão e o que ele muda nos números.", "", "", obs))
        else:
            sug = ""
            if bloco.sugestao:
                sug = f"Alternativa: {bloco.sugestao} — {tema.bloco(bloco.sugestao).titulo}"
            itens.append(ItemPasso(n, bloco.titulo, bloco.categoria, bloco.feedback, bloco.pergunta_reflexao, sug, obs))
    return itens


def boas_praticas_nao_usadas(tema: Theme, passos: list) -> list:
    usados = {ex.id_catalogo(p) for p in passos}
    return [b for b in tema.blocos if b.categoria == "boa_pratica" and b.id not in usados]


def _limite_de_colunas(titulo: str) -> bool:
    return titulo.startswith("No máximo") and "colunas" in titulo


def regras(tema: Theme, original: pd.DataFrame, df: pd.DataFrame, passos: list) -> list[ck.ResultadoCheck]:
    """Regras genéricas + do tema. Se o tema tem o próprio limite de colunas, o genérico (G06) não aparece."""
    ids = [ex.id_catalogo(p) or ex.uid(p) for p in passos]
    resultados = ck.avaliar(tema, original, df, ids)
    if any(_limite_de_colunas(r.titulo) for r in tema.regras_checklist):
        resultados = [r for r in resultados if r.check.id != "G06"]
    return resultados
