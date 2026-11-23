"""Helpers compartilhados pelos testes."""

import re
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core.models import Theme
from core.themes import REGISTRY

RAIZ = Path(__file__).resolve().parent.parent
PREFIXOS = {"T": "telco", "H": "hotel", "N": "noshow"}


def executar(codigo: str, df: pd.DataFrame) -> pd.DataFrame:
    """Executa um bloco exatamente como a seção 5.1 da APP_SPEC manda."""
    ns = {"df": df.copy()}
    exec(codigo, {"pd": pd, "np": np}, ns)
    return ns["df"]


def aplicar_com_requisitos(tema: Theme, block_id: str, df: pd.DataFrame) -> pd.DataFrame:
    """Aplica os blocos pré-requisito (recursivamente), cria colunas que faltam usando o primeiro
    bloco de boa prática que as cria, e depois aplica o bloco pedido."""
    from core.executor import blocos_que_criam

    bloco = tema.bloco(block_id)
    for req in bloco.requer_blocos:
        df = aplicar_com_requisitos(tema, req, df)
    for coluna in bloco.requer_colunas:
        if coluna not in df.columns:
            criadores = [b for b in blocos_que_criam(tema, coluna) if tema.bloco(b).categoria == "boa_pratica"]
            df = aplicar_com_requisitos(tema, criadores[0], df)
    return executar(bloco.codigo, df)


@cache
def _base(tema_id: str) -> pd.DataFrame:
    return pd.read_csv(RAIZ / REGISTRY[tema_id].arquivo)


def base(tema_id: str) -> pd.DataFrame:
    return _base(tema_id).copy()


@cache
def blocos_da_spec() -> dict[str, dict]:
    """Lê as tabelas de blocos da seção 8 do APP_SPEC.md."""
    blocos = {}
    for linha in (RAIZ / "APP_SPEC.md").read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\| [THN]\d{2} \|", linha):
            continue
        partes = [p.strip() for p in linha.split("|")[1:-1]]
        assert len(partes) == 7, linha
        bid, grupo, titulo, categoria, requer, codigo, feedback = partes
        segmentos = [re.fullmatch(r"`(.*)`", s.strip()).group(1) for s in codigo.split("<br>")]
        colunas, blocos_req = [], []
        if requer != "—":
            cols_txt, _, blocos_txt = requer.partition(";")
            if cols_txt.strip().startswith("bloco"):
                cols_txt, blocos_txt = "", cols_txt
            colunas = [c.strip() for c in cols_txt.split(",") if c.strip()]
            blocos_req = re.findall(r"[THN]\d{2}", blocos_txt)
        blocos[bid] = {
            "tema": PREFIXOS[bid[0]],
            "grupo": grupo,
            "titulo": titulo,
            "categoria": categoria,
            "requer_colunas": tuple(colunas),
            "requer_blocos": tuple(blocos_req),
            "codigo": "\n".join(segmentos),
            "feedback": feedback,
        }
    return blocos


@pytest.fixture
def telco():
    return REGISTRY["telco"]
