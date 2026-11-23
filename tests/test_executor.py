"""Executor: aplicar, medir, pré-requisitos e desfazer (seções 5.1, 7.1, 7.2 e 14)."""

import dataclasses

import pandas as pd
import pytest

from core import executor as ex
from core.models import Block
from core.themes import REGISTRY
from tests.conftest import base

TELCO = REGISTRY["telco"]


def _aplicar_em_ordem(tema, ids, df):
    for i in ids:
        df, r = ex.aplicar(df, tema.bloco(i))
        assert r.erro is None, r.erro
    return df


def test_aplicar_nao_altera_o_original_e_mede():
    df = base("telco")
    copia = df.copy()
    novo, r = ex.aplicar(df, TELCO.bloco("T01"))
    pd.testing.assert_frame_equal(df, copia)
    assert (r.linhas_antes, r.linhas_depois) == (7043, 7043)
    assert (r.nulos_antes, r.nulos_depois) == (0, 11)
    assert r.tipos_alterados == {"TotalCharges": ("object", "float64")}
    assert r.colunas_criadas == [] and r.colunas_removidas == []


def test_medir_colunas_criadas_e_removidas():
    df = base("telco")
    _, r = ex.aplicar(df, TELCO.bloco("T12"))
    assert r.colunas_criadas == ["faixa_tenure"]
    _, r = ex.aplicar(df, TELCO.bloco("T08"))
    assert r.colunas_removidas == ["customerID"]


def test_t10_remove_linhas_abaixo_do_limite_de_alerta():
    _, r = ex.aplicar(base("telco"), TELCO.bloco("T10"))
    assert 0 < ex.pct_linhas_removidas(r) < ex.LIMITE_REMOCAO_LINHAS


@pytest.mark.parametrize("ordem", [["T01", "T02", "T07", "T12"], ["T05", "T01", "T13", "T08", "T09"]])
def test_desfazer_cada_passo_igual_a_aplicar_os_demais_do_zero(ordem):
    original = base("telco")
    for k in ordem:
        pipe = ex.desfazer(original, TELCO, ordem, k)
        validos = ex.reexecutar(original, TELCO, [i for i in ordem if i != k])
        pd.testing.assert_frame_equal(pipe.df, validos.df)
        assert pipe.passos == validos.passos
        esperado = _aplicar_em_ordem(TELCO, pipe.passos, original)
        pd.testing.assert_frame_equal(pipe.df.reset_index(drop=True), esperado.reset_index(drop=True))


def test_desfazer_t01_remove_t02_e_avisa():
    original = base("telco")
    pipe = ex.reexecutar(original, TELCO, ["T01", "T02", "T07"])
    assert pipe.passos == ["T01", "T02", "T07"]
    pipe = ex.desfazer(original, TELCO, pipe.passos, "T01")
    assert pipe.passos == ["T07"]
    assert [r[0] for r in pipe.removidos] == ["T02"]
    assert "T01" in pipe.removidos[0][1]
    so_t07 = ex.executar_codigo(TELCO.bloco("T07").codigo, original)
    pd.testing.assert_frame_equal(pipe.df, so_t07)


def test_bloco_sem_prerequisito_fica_desabilitado_com_motivo():
    df = base("telco")
    motivo = ex.motivo_desabilitado(TELCO, TELCO.bloco("T02"), df, [])
    assert motivo == "Este bloco precisa que o bloco T01 seja aplicado antes."
    assert ex.motivo_desabilitado(TELCO, TELCO.bloco("T02"), ex.executar_codigo(TELCO.bloco("T01").codigo, df), ["T01"]) is None


def test_coluna_removida_por_passo_anterior():
    df = ex.executar_codigo(TELCO.bloco("T11").codigo, base("telco"))
    motivo = ex.motivo_desabilitado(TELCO, TELCO.bloco("T08"), df, ["T11"], list(base("telco").columns))
    assert motivo.startswith("Este bloco precisa da coluna `customerID`, que não existe mais")


def test_motivo_indica_bloco_que_cria_a_coluna():
    falso = Block(id="X01", titulo="x", grupo="g", explicacao="", codigo="df = df", requer_colunas=("faixa_tenure",))
    tema = dataclasses.replace(TELCO, blocos=TELCO.blocos + (falso,))
    motivo = ex.motivo_desabilitado(tema, falso, base("telco"), [], list(base("telco").columns))
    assert motivo == "Este bloco precisa da coluna `faixa_tenure`. Aplique antes o bloco T12."


def test_excecao_em_bloco_nao_altera_estado():
    df = base("telco")
    quebrado = Block(id="X99", titulo="Quebrado", grupo="Teste", explicacao="", codigo='df["x"] = df["nao_existe"] + 1')
    novo, r = ex.aplicar(df, quebrado)
    assert novo is df
    assert r.erro and "KeyError" in r.erro
    assert (r.linhas_antes, r.colunas_antes) == (r.linhas_depois, r.colunas_depois)


def test_codigo_completo_na_ordem():
    texto = ex.codigo_completo(TELCO, ["T01", "T02"])
    assert texto.index(TELCO.bloco("T01").codigo) < texto.index(TELCO.bloco("T02").codigo)


HOTEL = REGISTRY["hotel"]
NOSHOW = REGISTRY["noshow"]


def test_h07_desabilita_h08_com_motivo():
    original = base("hotel")
    pipe = ex.reexecutar(original, HOTEL, ["H07"])
    motivo = ex.motivo_desabilitado(HOTEL, HOTEL.bloco("H08"), pipe.df, pipe.passos, list(original.columns))
    assert motivo.startswith("Este bloco precisa da coluna `reservation_status`, que não existe mais")


def test_n14_desabilita_blocos_com_nomes_antigos():
    original = base("noshow")
    pipe = ex.reexecutar(original, NOSHOW, ["N14"])
    bloqueados = {
        b.id for b in NOSHOW.blocos
        if b.id != "N14" and ex.motivo_desabilitado(NOSHOW, b, pipe.df, pipe.passos, list(original.columns))
    }
    assert bloqueados == {"N01", "N02", "N03", "N04", "N05", "N06", "N07", "N08", "N09", "N10", "N11", "N12", "N13"}
    motivo = ex.motivo_desabilitado(NOSHOW, NOSHOW.bloco("N07"), pipe.df, pipe.passos, list(original.columns))
    assert "`Age`, que não existe mais" in motivo


def test_n06_sem_dias_espera_indica_blocos():
    original = base("noshow")
    motivo = ex.motivo_desabilitado(NOSHOW, NOSHOW.bloco("N06"), original, [], list(original.columns))
    assert motivo == "Este bloco precisa da coluna `dias_espera`. Aplique antes o bloco N04 ou N05."


def test_desfazer_n03_remove_dependentes():
    original = base("noshow")
    pipe = ex.reexecutar(original, NOSHOW, ["N03", "N04", "N06", "N11", "N01"])
    pipe = ex.desfazer(original, NOSHOW, pipe.passos, "N03")
    assert pipe.passos == ["N01"]
    assert {r[0] for r in pipe.removidos} == {"N04", "N06", "N11"}
