"""Exportação dos dois arquivos finais (seção 10 da APP_SPEC)."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

from core.spec_builder import EstadoSpec, montar_spec


def _datas_em_iso(df: pd.DataFrame) -> pd.DataFrame:
    """Colunas de data viram texto ISO: AAAA-MM-DD (só datas) ou AAAA-MM-DD HH:MM:SS."""
    colunas = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    if not colunas:
        return df
    df = df.copy()
    for c in colunas:
        serie = df[c]
        if getattr(serie.dt, "tz", None) is not None:
            serie = serie.dt.tz_convert("UTC").dt.tz_localize(None)
        so_data = serie.dropna().eq(serie.dropna().dt.normalize()).all()
        formato = "%Y-%m-%d" if so_data else "%Y-%m-%d %H:%M:%S"
        df[c] = serie.dt.strftime(formato)
    return df


def gerar_csv(df: pd.DataFrame) -> bytes:
    return _datas_em_iso(df).to_csv(index=False).encode("utf-8-sig")


def gerar_spec(estado: EstadoSpec) -> str:
    return montar_spec(estado)


def slug_equipe(equipe: str) -> str:
    """Minúsculas, sem acentos, espaços viram `_`; outros símbolos são removidos."""
    texto = unicodedata.normalize("NFKD", equipe).encode("ascii", "ignore").decode("ascii").lower().strip()
    texto = re.sub(r"\s+", "_", texto)
    texto = re.sub(r"[^a-z0-9_-]", "", texto)
    texto = re.sub(r"_+", "_", texto).strip("_-")
    return texto or "equipe"


def nome_arquivo(equipe: str, sufixo: str) -> str:
    return f"{slug_equipe(equipe)}_{sufixo}"
