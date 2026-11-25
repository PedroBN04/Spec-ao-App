"""Exportação dos dois arquivos finais (seção 10 da APP_SPEC)."""

from __future__ import annotations

import io
import re
import unicodedata
import zipfile

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


# ---------------------------------------------------------------------------
# Excel e kit .zip (proposta P0.4)
# ---------------------------------------------------------------------------

LIMITE_CELULAS_XLSX = 3_000_000  # acima disso a planilha ficaria lenta demais (ex.: depois do T11)


def xlsx_viavel(df: pd.DataFrame) -> bool:
    return df.size <= LIMITE_CELULAS_XLSX and df.shape[1] <= 16_000


def gerar_xlsx(df: pd.DataFrame) -> bytes:
    """Planilha .xlsx real: abre em linhas e colunas no Excel em português, com números como números."""
    dados = df.copy()
    for c in dados.columns:
        if pd.api.types.is_datetime64_any_dtype(dados[c]) and getattr(dados[c].dt, "tz", None) is not None:
            dados[c] = dados[c].dt.tz_convert("UTC").dt.tz_localize(None)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter", datetime_format="yyyy-mm-dd hh:mm:ss",
                        date_format="yyyy-mm-dd") as writer:
        dados.to_excel(writer, index=False, sheet_name="dados_tratados")
        planilha = writer.sheets["dados_tratados"]
        planilha.freeze_panes(1, 0)
        cabecalho = writer.book.add_format({"bold": True, "bg_color": "#EEF0FB", "border": 1})
        for i, col in enumerate(dados.columns):
            planilha.write(0, i, str(col), cabecalho)
            amostra = dados[col].head(200).astype(str).str.len().max() if len(dados) else 0
            planilha.set_column(i, i, min(max(len(str(col)), int(amostra or 0)) + 2, 45))
    return buffer.getvalue()


def gerar_zip(df: pd.DataFrame, spec: str) -> bytes:
    """Kit da equipe: dados_tratados.csv (para o agente), dados_tratados_excel.xlsx e SPEC.md."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as kit:
        kit.writestr("dados_tratados.csv", gerar_csv(df))
        if xlsx_viavel(df):
            kit.writestr("dados_tratados_excel.xlsx", gerar_xlsx(df))
        kit.writestr("SPEC.md", spec.encode("utf-8"))
    return buffer.getvalue()
