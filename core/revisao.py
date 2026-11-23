"""Revisão (etapa 4, v2): só fatos sobre o resultado, sem dizer se está certo ou errado.

A pessoa compara a base original com a tratada e decide se quer voltar ao fluxo para melhorar.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core import diagnostics as dg


@dataclass(frozen=True)
class Indicador:
    titulo: str
    antes: str
    depois: str
    detalhe: str = ""  # fato complementar (ex.: quais colunas)


def _fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _pct(x: float) -> str:
    return f"{x * 100:.1f}%".replace(".", ",")


def indicadores(tema, original: pd.DataFrame, df: pd.DataFrame) -> list[Indicador]:
    def com_vazios(d):
        s = d.isna().sum()
        return [str(c) for c in s[s > 0].index]

    def texto_numero(d):
        return [str(c) for c in d.columns if dg.parece_numero(d[c])]

    def lista(cols, limite=6):
        if not cols:
            return "nenhuma"
        extra = f" e mais {len(cols) - limite}" if len(cols) > limite else ""
        return ", ".join(f"`{c}`" for c in cols[:limite]) + extra

    alvo_antes = tema.alvo in original.columns
    vazios_depois, num_txt_depois = com_vazios(df), texto_numero(df)
    return [
        Indicador("Linhas", _fmt(len(original)), _fmt(len(df)),
                  f"{_pct(len(df) / len(original))} das linhas originais continuam na base." if len(original) else ""),
        Indicador("Colunas", _fmt(original.shape[1]), _fmt(df.shape[1])),
        Indicador("Células vazias", _fmt(int(original.isna().sum().sum())), _fmt(int(df.isna().sum().sum())),
                  "Colunas com vazios agora: " + lista(vazios_depois)),
        Indicador("Linhas repetidas", _fmt(int(original.duplicated().sum())), _fmt(int(df.duplicated().sum()))),
        Indicador("Colunas de texto com valores que parecem números", _fmt(len(texto_numero(original))),
                  _fmt(len(num_txt_depois)), "Agora: " + lista(num_txt_depois)),
        Indicador("Coluna de resultado original", f"`{tema.alvo}`" if alvo_antes else "—",
                  "continua na base" if tema.alvo in df.columns else "não está mais na base"),
    ]


def comparativo_colunas(original: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por coluna (originais e novas): situação, tipo e vazios antes × depois."""
    linhas = []
    for c in list(original.columns) + [c for c in df.columns if c not in original.columns]:
        antes, depois = c in original.columns, c in df.columns
        situacao = "mantida" if antes and depois else ("removida ou renomeada" if antes else "nova")
        linhas.append({
            "Coluna": str(c),
            "Situação": situacao,
            "Tipo antes": dg.tipo_amigavel(original[c].dtype) if antes else "",
            "Tipo depois": dg.tipo_amigavel(df[c].dtype) if depois else "",
            "Vazios antes": int(original[c].isna().sum()) if antes else None,
            "Vazios depois": int(df[c].isna().sum()) if depois else None,
        })
    return pd.DataFrame(linhas)
