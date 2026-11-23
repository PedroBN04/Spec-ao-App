"""Blocos personalizados (v2): geração de código segura e execução na base real."""

import pandas as pd
import pytest

from core import blocos_livres as bl
from core import executor as ex
from core.themes import REGISTRY
from tests.conftest import base

TELCO = REGISTRY["telco"]


def _rodar(acao, params, df=None):
    df = base("telco") if df is None else df
    bloco = bl.gerar_bloco("P1", acao, params, df)
    novo, r = ex.aplicar(df, bloco)
    assert r.erro is None, (bloco.codigo, r.erro)
    return bloco, novo


def test_cada_acao_gera_codigo_que_roda():
    t01 = ex.executar_codigo(TELCO.bloco("T01").codigo, base("telco"))
    casos = [
        ("remover_colunas", {"colunas": ["gender", "Partner"]}, None),
        ("preencher_vazios", {"coluna": "TotalCharges", "metodo": "valor", "valor": "0"}, t01),
        ("preencher_vazios", {"coluna": "TotalCharges", "metodo": "mediana"}, t01),
        ("preencher_vazios", {"coluna": "TotalCharges", "metodo": "moda"}, t01),
        ("remover_linhas_vazias", {"colunas": ["TotalCharges"]}, t01),
        ("remover_linhas_vazias", {"colunas": []}, t01),
        ("converter_tipo", {"coluna": "TotalCharges", "para": "numero"}, None),
        ("converter_tipo", {"coluna": "tenure", "para": "texto"}, None),
        ("filtrar_linhas", {"coluna": "tenure", "operador": ">", "valor": "0"}, None),
        ("filtrar_linhas", {"coluna": "Contract", "operador": "==", "valor": "Month-to-month"}, None),
        ("substituir_valor", {"coluna": "MultipleLines", "de": "No phone service", "para": "No"}, None),
        ("criar_faixas", {"coluna": "tenure", "cortes": "0 12 24 72", "nome": "faixa"}, None),
        ("criar_indicador", {"coluna": "Churn", "operador": "==", "valor": "Yes", "nome": "cancelou"}, None),
        ("calcular_coluna", {"coluna_a": "MonthlyCharges", "conta": "*", "coluna_b": "tenure", "nome": "est"}, None),
        ("renomear_coluna", {"coluna": "tenure", "novo": "meses"}, None),
        ("remover_duplicados", {"colunas": []}, None),
    ]
    for acao, params, df in casos:
        bloco, _ = _rodar(acao, params, df)
        assert bloco.categoria == "livre" and bloco.grupo == "Personalizado"
    assert {a.id for a in bl.ACOES} == {c[0] for c in casos}


def test_efeitos():
    _, d = _rodar("criar_indicador", {"coluna": "Churn", "operador": "==", "valor": "Yes", "nome": "cancelou"})
    assert d["cancelou"].mean() == pytest.approx(0.265, abs=0.001)
    _, d = _rodar("filtrar_linhas", {"coluna": "tenure", "operador": ">", "valor": "0"})
    assert len(d) == 7043 - 11
    _, d = _rodar("criar_faixas", {"coluna": "tenure", "cortes": "0, 12, 72", "nome": "faixa"})
    assert d["faixa"].nunique() == 2


def test_valores_digitados_viram_literais_seguros():
    bloco = bl.gerar_bloco("P1", "substituir_valor",
                           {"coluna": "gender", "de": '"); import os; os.system("x"); ("', "para": "x"}, base("telco"))
    assert "import os" in bloco.codigo  # só como texto dentro do literal
    compile(bloco.codigo, "<bloco>", "exec")
    novo, r = ex.aplicar(base("telco"), bloco)
    assert r.erro is None and novo.equals(base("telco"))


def test_parametros_invalidos_tem_mensagem_simples():
    df = base("telco")
    with pytest.raises(bl.ParametroInvalido, match="não é um número"):
        bl.gerar_bloco("P1", "filtrar_linhas", {"coluna": "tenure", "operador": ">", "valor": "abc"}, df)
    with pytest.raises(bl.ParametroInvalido, match="pelo menos uma coluna"):
        bl.gerar_bloco("P1", "remover_colunas", {"colunas": []}, df)
    with pytest.raises(bl.ParametroInvalido, match="não é numérica"):
        bl.gerar_bloco("P1", "criar_faixas", {"coluna": "TotalCharges", "cortes": "0 10", "nome": "f"}, df)
    with pytest.raises(bl.ParametroInvalido, match="ordem crescente"):
        bl.gerar_bloco("P1", "criar_faixas", {"coluna": "tenure", "cortes": "10 0", "nome": "f"}, df)
    with pytest.raises(bl.ParametroInvalido, match="Já existe"):
        bl.gerar_bloco("P1", "renomear_coluna", {"coluna": "tenure", "novo": "Churn"}, df)


def test_fluxo_misto_reexecuta_e_reordena():
    original = base("telco")
    passos = [
        {"uid": "P1", "tipo": "catalogo", "id": "T01"},
        {"uid": "P2", "tipo": "livre", "acao": "preencher_vazios",
         "params": {"coluna": "TotalCharges", "metodo": "valor", "valor": "0"}},
        {"uid": "P3", "tipo": "livre", "acao": "criar_faixas",
         "params": {"coluna": "TotalCharges", "cortes": "0 1000 9000", "nome": "faixa_total"}},
    ]
    pipe = ex.reexecutar(original, TELCO, passos)
    assert [ex.uid(p) for p in pipe.passos] == ["P1", "P2", "P3"] and pipe.df["TotalCharges"].isna().sum() == 0
    # Faixas antes da conversão: TotalCharges ainda é texto -> o passo sai do fluxo, com motivo
    reord = ex.mover(passos, "P3", -2)
    pipe = ex.reexecutar(original, TELCO, reord)
    assert [ex.uid(p) for p in pipe.passos] == ["P1", "P2"]
    assert pipe.removidos[0][0] == "P3" and "não é numérica" in pipe.removidos[0][1]
