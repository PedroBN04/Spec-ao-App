"""Diagnóstico visual da base (etapa 2 da APP_SPEC).

Funções puras sobre DataFrames: não dependem do Streamlit e podem ser testadas.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

LIMITE_PARECE_NUMERO = 0.90
LIMITE_PARECE_DATA = 0.90
LIMITE_MUITOS_NULOS = 0.50

# Datas como "2016-04-29", "2016-04-29T18:38:08Z", "2015-07-01 10:00" ou "29/04/2016".
_PADRAO_DATA = r"^\s*(\d{4}-\d{1,2}-\d{1,2}([ T]\d{1,2}:\d{2}(:\d{2})?.*)?|\d{1,2}/\d{1,2}/\d{2,4})\s*$"


@dataclass(frozen=True)
class Alerta:
    tipo: str  # identificador curto, ex.: "texto_numero"
    icone: str
    coluna: str | None  # None para alertas da base inteira
    mensagem: str  # frase em linguagem simples


# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------


def eh_texto(serie: pd.Series) -> bool:
    return pd.api.types.is_object_dtype(serie) or pd.api.types.is_string_dtype(serie)


def eh_numerica(serie: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(serie) and not pd.api.types.is_bool_dtype(serie)


def tipo_amigavel(dtype) -> str:
    """Nome do tipo do pandas em português simples."""
    nome = str(dtype)
    if nome in ("object", "string", "str"):
        return "texto"
    if nome.startswith(("int", "Int", "uint")):
        return "número inteiro"
    if nome.startswith(("float", "Float")):
        return "número decimal"
    if nome.startswith("datetime"):
        return "data/hora"
    if nome == "bool":
        return "verdadeiro/falso"
    if nome == "category":
        return "categoria"
    return nome


def parece_numero(serie: pd.Series) -> bool:
    """Coluna de texto cujos valores (não vazios) são ≥ 90% convertíveis em número após strip()."""
    if not eh_texto(serie):
        return False
    valores = serie.dropna()
    if valores.empty:
        return False
    convertidos = pd.to_numeric(valores.astype(str).str.strip(), errors="coerce")
    return convertidos.notna().mean() >= LIMITE_PARECE_NUMERO


def parece_data(serie: pd.Series) -> bool:
    """Coluna de texto cujos valores (não vazios) têm formato de data em ≥ 90% dos casos."""
    if not eh_texto(serie) or parece_numero(serie):
        return False
    valores = serie.dropna()
    if valores.empty:
        return False
    return valores.astype(str).str.match(_PADRAO_DATA).mean() >= LIMITE_PARECE_DATA


# ---------------------------------------------------------------------------
# Métricas e alertas
# ---------------------------------------------------------------------------


def metricas(df: pd.DataFrame) -> dict:
    total_celulas = df.size or 1
    n_numericas = sum(eh_numerica(df[c]) for c in df.columns)
    return {
        "linhas": len(df),
        "colunas": df.shape[1],
        "pct_nulos": float(df.isna().sum().sum() / total_celulas * 100),
        "duplicadas": int(df.duplicated().sum()),
        "numericas": int(n_numericas),
        "texto": int(sum(eh_texto(df[c]) for c in df.columns)),
    }


def alertas_coluna(serie: pd.Series, colunas_vazamento: tuple[str, ...] = ()) -> list[Alerta]:
    col = str(serie.name)
    alertas: list[Alerta] = []
    if col in colunas_vazamento:
        alertas.append(
            Alerta(
                "vazamento",
                "⚠️",
                col,
                "Esta coluna revela o resultado. Ela pode existir no CSV, mas não pode ser usada para prever o alvo.",
            )
        )
    if parece_numero(serie):
        alertas.append(
            Alerta("texto_numero", "🔢", col, "Está guardada como texto, mas os valores parecem números.")
        )
    if parece_data(serie):
        alertas.append(Alerta("texto_data", "📅", col, "Está guardada como texto, mas os valores parecem datas."))
    pct_nulos = serie.isna().mean() if len(serie) else 0.0
    if pct_nulos > LIMITE_MUITOS_NULOS:
        alertas.append(
            Alerta("muitos_nulos", "🕳️", col, f"Mais da metade está vazia ({pct_nulos:.0%} de nulos).")
        )
    if eh_numerica(serie) and (serie < 0).any():
        n = int((serie < 0).sum())
        alertas.append(Alerta("negativos", "➖", col, f"Tem {n} valor(es) negativo(s)."))
    if len(serie) and serie.nunique(dropna=True) <= 1:
        alertas.append(Alerta("valor_unico", "1️⃣", col, "Tem um valor só: não ajuda a diferenciar as linhas."))
    return alertas


def alertas_base(df: pd.DataFrame, colunas_vazamento: tuple[str, ...] = ()) -> list[Alerta]:
    alertas: list[Alerta] = []
    duplicadas = int(df.duplicated().sum())
    if duplicadas:
        alertas.append(
            Alerta(
                "duplicadas",
                "👯",
                None,
                f"Há {duplicadas} linha(s) totalmente duplicada(s) (iguais a outra linha em todas as colunas).",
            )
        )
    for col in df.columns:
        alertas.extend(alertas_coluna(df[col], colunas_vazamento))
    return alertas


def _exemplo(serie: pd.Series) -> str:
    valores = serie.dropna()
    if valores.empty:
        return ""
    texto = repr(valores.iloc[0]) if eh_texto(serie) else str(valores.iloc[0])
    return texto if len(texto) <= 40 else texto[:37] + "..."


def raio_x(df: pd.DataFrame, dicionario: dict[str, str], colunas_vazamento: tuple[str, ...] = ()) -> pd.DataFrame:
    """Tabela "Raio-X das colunas": uma linha por coluna."""
    linhas = []
    for col in df.columns:
        serie = df[col]
        alertas = alertas_coluna(serie, colunas_vazamento)
        linhas.append(
            {
                "Coluna": col,
                "Significado": dicionario.get(col, ""),
                "Tipo": str(serie.dtype),
                "% nulos": round(float(serie.isna().mean() * 100), 1) if len(serie) else 0.0,
                "Valores distintos": int(serie.nunique(dropna=True)),
                "Exemplo": _exemplo(serie),
                "Alerta": " · ".join(f"{a.icone} {a.mensagem}" for a in alertas),
            }
        )
    return pd.DataFrame(linhas)


def distribuicao(serie: pd.Series, top: int | None = None) -> pd.DataFrame:
    """Contagem e % de cada valor (vazios contam como "(vazio)")."""
    contagem = serie.astype(object).where(serie.notna(), "(vazio)").value_counts()
    if top is not None:
        contagem = contagem.head(top)
    total = len(serie) or 1
    out = contagem.rename_axis("valor").reset_index(name="quantidade")
    out["valor"] = out["valor"].astype(str)
    out["%"] = (out["quantidade"] / total * 100).round(1)
    return out


# ---------------------------------------------------------------------------
# v2: exploração (fatos, sem apontar problemas)
# ---------------------------------------------------------------------------

ROTEIRO = (
    "Cada linha da base representa o quê? (um cliente? uma reserva? uma consulta?)",
    "Qual coluna guarda o resultado que a área quer entender? Como ele está escrito?",
    "O tipo de cada coluna combina com o que ela significa? (um número guardado como texto não soma)",
    "Onde há células vazias? O vazio é um erro ou tem significado?",
    "Há valores estranhos (negativos, zeros, muito altos)? São erros ou casos reais?",
    "Há linhas repetidas? São o mesmo registro ou registros diferentes que parecem iguais?",
    "Alguma coluna só seria conhecida depois que o resultado acontece?",
    "Há informação espalhada em várias colunas, com nomes confusos ou escrita de jeitos diferentes?",
)


def _fmt_valor(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, float):
        return f"{v:.2f}".rstrip("0").rstrip(".")
    return str(v)


def raio_x_v2(df: pd.DataFrame, dicionario: dict[str, str]) -> pd.DataFrame:
    """Raio-X só com fatos: tipo, vazios, distintos, exemplo e faixa (sem coluna de alerta)."""
    linhas = []
    for col in df.columns:
        s = df[col]
        num = eh_numerica(s)
        linhas.append({
            "Coluna": col,
            "Significado": dicionario.get(col, ""),
            "Tipo": tipo_amigavel(s.dtype),
            "% vazios": round(float(s.isna().mean() * 100), 1) if len(s) else 0.0,
            "Distintos": int(s.nunique(dropna=True)),
            "Exemplo": _exemplo(s),
            "Mínimo": _fmt_valor(s.min()) if num and s.notna().any() else "",
            "Máximo": _fmt_valor(s.max()) if num and s.notna().any() else "",
        })
    return pd.DataFrame(linhas)


def estatisticas(serie: pd.Series) -> dict[str, str]:
    s = serie
    nao_vazios = s.dropna()
    info = {
        "Tipo": tipo_amigavel(s.dtype),
        "Vazios": f"{int(s.isna().sum())} ({s.isna().mean():.1%})".replace(".", ","),
        "Valores distintos": str(int(s.nunique(dropna=True))),
    }
    if eh_numerica(s) and not nao_vazios.empty:
        info.update({
            "Mínimo": _fmt_valor(nao_vazios.min()),
            "Média": _fmt_valor(float(nao_vazios.mean())),
            "Mediana": _fmt_valor(float(nao_vazios.median())),
            "Máximo": _fmt_valor(nao_vazios.max()),
            "Zeros": str(int((nao_vazios == 0).sum())),
            "Negativos": str(int((nao_vazios < 0).sum())),
        })
    elif not nao_vazios.empty:
        textos = nao_vazios.astype(str)
        info["Valor mais comum"] = repr(textos.mode().iloc[0])
        info["Valores só com espaços"] = str(int(textos.str.strip().eq("").sum()))
    return info


def indicador_alvo(serie: pd.Series) -> tuple[pd.Series, str] | None:
    """(série 0/1, rótulo) para o alvo; None se o formato não for reconhecido."""
    valores = set(serie.dropna().unique())
    if pd.api.types.is_numeric_dtype(serie) and valores <= {0, 1}:
        return (serie == 1).astype(float).where(serie.notna()), f"% com `{serie.name}` = 1"
    if {str(v) for v in valores} <= {"Yes", "No"}:
        return (serie == "Yes").astype(float).where(serie.notna()), f"% com `{serie.name}` = Yes"
    return None


def relacao_com_alvo(df: pd.DataFrame, coluna: str, alvo: str, top: int = 15) -> tuple[pd.DataFrame, str] | None:
    """Taxa do alvo por valor (ou faixa) da coluna. Fato, não interpretação."""
    if alvo not in df.columns or coluna == alvo:
        return None
    ind = indicador_alvo(df[alvo])
    if ind is None:
        return None
    indicador, rotulo = ind
    s = df[coluna]
    if eh_numerica(s) and s.nunique() > 12:
        grupos = pd.qcut(s, q=5, duplicates="drop").astype(str).where(s.notna(), "(vazio)")
    else:
        grupos = s.astype(object).where(s.notna(), "(vazio)").astype(str)
    tabela = (
        pd.DataFrame({"grupo": grupos, "alvo": indicador})
        .groupby("grupo", observed=True)["alvo"]
        .agg(["mean", "size"])
        .reset_index()
        .rename(columns={"grupo": coluna, "mean": "taxa", "size": "linhas"})
        .sort_values("linhas", ascending=False)
        .head(top)
    )
    return tabela, rotulo
