"""Temas e bases do repositório (marco M1)."""

import pandas as pd
import pytest

from core.themes import REGISTRY
from tests.conftest import base

FORMATOS = {"telco": (7043, 21), "hotel": (30000, 32), "noshow": (30000, 14)}


def test_registry_tem_os_tres_temas():
    assert list(REGISTRY) == ["telco", "hotel", "noshow"]
    for tema_id, tema in REGISTRY.items():
        assert tema.id == tema_id


@pytest.mark.parametrize("tema_id", FORMATOS)
def test_base_tem_o_formato_esperado(tema_id):
    assert base(tema_id).shape == FORMATOS[tema_id]


@pytest.mark.parametrize("tema_id", FORMATOS)
def test_dicionario_cobre_exatamente_as_colunas(tema_id):
    tema = REGISTRY[tema_id]
    assert list(tema.dicionario) == list(base(tema_id).columns)
    assert all(v.strip() for v in tema.dicionario.values())


@pytest.mark.parametrize("tema_id", FORMATOS)
def test_alvo_e_vazamento_existem_na_base(tema_id):
    tema = REGISTRY[tema_id]
    df = base(tema_id)
    assert tema.alvo in df.columns
    assert set(tema.colunas_vazamento) <= set(df.columns)


@pytest.mark.parametrize("tema_id", FORMATOS)
def test_textos_do_cartao_preenchidos(tema_id):
    tema = REGISTRY[tema_id]
    for campo in ("nome", "dominio", "fonte", "licenca", "descricao_base", "problematica", "emoji"):
        assert getattr(tema, campo).strip()
    assert tema.proposta_inicial and tema.aprofundamentos


def test_taxas_do_alvo_batem_com_a_spec():
    assert base("telco")["Churn"].eq("Yes").mean() == pytest.approx(0.265, abs=0.01)
    assert base("hotel")["is_canceled"].mean() == pytest.approx(0.37, abs=0.02)
    assert base("noshow")["No-show"].eq("Yes").mean() == pytest.approx(0.20, abs=0.02)


def test_hotel_amostra_mantem_defeitos_raros():
    df = base("hotel")
    assert df["children"].isna().any()
    assert (df["adr"] < 0).any() and (df["adr"] > 1000).any()
    assert df["company"].isna().mean() > 0.8


def test_telco_spec_defaults_completos():
    d = REGISTRY["telco"].spec_defaults
    assert d["problema"] and d["usuario"] and d["metrica_sucesso"]
    assert len(d["funcionalidades"]) >= 4
    assert len(d["regras_negocio"]) >= 3
    assert len(d["criterios_aceitacao"]) >= 4


def test_telco_regras_de_checklist_na_base_crua():
    tema = REGISTRY["telco"]
    df = base("telco")
    resultado = {r.id: r.funcao(df, df, [])[0] for r in tema.regras_checklist}
    assert resultado == {"TEL01": True, "TEL02": False, "TEL03": True, "TEL04": True, "TEL05": True}
