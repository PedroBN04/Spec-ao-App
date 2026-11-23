"""Blocos de tratamento: fidelidade à APP_SPEC e execução na base real.

REGRA DO PROJETO: o código de TODOS os blocos (inclusive armadilhas e "depende") deve ser
idêntico ao da seção 8 da APP_SPEC. Estes testes garantem que ninguém "corrija" um bloco.
"""

import pandas as pd
import pytest

from core.themes import REGISTRY
from tests.conftest import aplicar_com_requisitos, base, blocos_da_spec, executar

SPEC = blocos_da_spec()
IMPLEMENTADOS = [(t.id, b.id) for t in REGISTRY.values() for b in t.blocos]


def test_spec_tem_todos_os_blocos():
    assert len(SPEC) == 13 + 14 + 14


def test_telco_implementa_todos_os_blocos_da_spec():
    ids_spec = sorted(b for b, d in SPEC.items() if d["tema"] == "telco")
    assert [b.id for b in REGISTRY["telco"].blocos] == ids_spec


@pytest.mark.parametrize("tema_id,block_id", IMPLEMENTADOS)
def test_bloco_identico_a_spec(tema_id, block_id):
    bloco = REGISTRY[tema_id].bloco(block_id)
    esperado = SPEC[block_id]
    assert esperado["tema"] == tema_id
    assert bloco.codigo == esperado["codigo"]
    assert bloco.titulo == esperado["titulo"]
    assert bloco.grupo == esperado["grupo"]
    assert bloco.categoria == esperado["categoria"]
    assert bloco.requer_colunas == esperado["requer_colunas"]
    assert bloco.requer_blocos == esperado["requer_blocos"]
    assert bloco.feedback == esperado["feedback"]


@pytest.mark.parametrize("tema_id,block_id", IMPLEMENTADOS)
def test_bloco_tem_textos_didaticos(tema_id, block_id):
    bloco = REGISTRY[tema_id].bloco(block_id)
    assert bloco.explicacao and bloco.pergunta_reflexao
    if bloco.sugestao:
        assert bloco.categoria == "armadilha"
        REGISTRY[tema_id].bloco(bloco.sugestao)  # o bloco sugerido existe


@pytest.mark.parametrize("tema_id,block_id", IMPLEMENTADOS)
def test_bloco_executa_na_base_real(tema_id, block_id):
    tema = REGISTRY[tema_id]
    df = base(tema_id)
    bloco = tema.bloco(block_id)
    for col in bloco.requer_colunas:
        assert col in df.columns
    resultado = aplicar_com_requisitos(tema, block_id, df)
    assert isinstance(resultado, pd.DataFrame)


# --- Telco: seção 14 e efeitos descritos nos feedbacks ----------------------


def test_t01_totalcharges_numerica_com_nulos(telco):
    df = executar(telco.bloco("T01").codigo, base("telco"))
    assert pd.api.types.is_numeric_dtype(df["TotalCharges"])
    assert df["TotalCharges"].isna().sum() == 11


def test_t01_t02_sem_nulos_em_totalcharges(telco):
    df = aplicar_com_requisitos(telco, "T02", base("telco"))
    assert df["TotalCharges"].isna().sum() == 0
    assert (df.loc[df["tenure"] == 0, "TotalCharges"] == 0).all()


def test_t03_armadilha_inventa_cobranca_para_clientes_novos(telco):
    df = aplicar_com_requisitos(telco, "T03", base("telco"))
    novos = df.loc[df["tenure"] == 0, "TotalCharges"]
    assert len(novos) == 11 and novos.between(2200, 2350).all()


def test_t04_remove_apenas_clientes_novos(telco):
    df = aplicar_com_requisitos(telco, "T04", base("telco"))
    assert len(df) == 7043 - 11
    assert (df["tenure"] > 0).all()


def test_t09_cria_coluna_de_vazamento(telco):
    df = executar(telco.bloco("T09").codigo, base("telco"))
    assert "taxa_churn_pagamento" in df.columns
    assert df["taxa_churn_pagamento"].between(0, 1).all()
    assert df["taxa_churn_pagamento"].nunique() == 4


def test_t10_armadilha_remove_clientes_reais(telco):
    df = executar(telco.bloco("T10").codigo, base("telco"))
    assert 0 < 7043 - len(df) < 7043 * 0.2


def test_t11_explode_em_mais_de_mil_colunas(telco):
    df = executar(telco.bloco("T11").codigo, base("telco"))
    assert df.shape[1] > 1000


def test_t12_faixas_de_tenure(telco):
    df = executar(telco.bloco("T12").codigo, base("telco"))
    assert set(df["faixa_tenure"]) == {"0-12 meses", "13-24 meses", "25-48 meses", "49-72 meses"}


def test_t13_normaliza_entre_0_e_1(telco):
    df = aplicar_com_requisitos(telco, "T13", base("telco"))
    for c in ["MonthlyCharges", "TotalCharges"]:
        assert df[c].min() == 0 and df[c].max() == 1
