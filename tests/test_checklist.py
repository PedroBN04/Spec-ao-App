"""Checklist (seções 6/etapa 4, 8.1 e 8.4)."""

from core import checklist as ck
from core import executor as ex
from core.themes import REGISTRY
from tests.conftest import base

TELCO = REGISTRY["telco"]


def _avaliar(ids):
    original = base("telco")
    pipe = ex.reexecutar(original, TELCO, ids)
    assert pipe.passos == ids
    return {r.check.id: r for r in ck.avaliar(TELCO, original, pipe.df, ids)}


def test_base_crua_dispara_g05_e_totalcharges():
    r = _avaliar([])
    assert not r["G05"].passou and "TotalCharges" in r["G05"].mensagem
    assert not r["TEL02"].passou
    assert all(r[g].passou for g in ("G01", "G02", "G03", "G04", "G06"))


def test_t09_dispara_vazamento_generico_e_do_tema():
    r = _avaliar(["T09"])
    assert not r["G02"].passou and "taxa_churn_pagamento" in r["G02"].mensagem
    assert not r["TEL01"].passou
    assert r["TEL01"].check.nivel == "erro"


def test_t01_t02_passa_g04_e_g05():
    r = _avaliar(["T01", "T02"])
    assert r["G04"].passou and r["G05"].passou and r["TEL02"].passou


def test_t01_sozinho_deixa_nulos():
    r = _avaliar(["T01"])
    assert not r["G04"].passou and "11" in r["G04"].mensagem


def test_t03_dispara_alerta_de_cobranca_inventada():
    assert not _avaliar(["T01", "T03"])["TEL04"].passou


def test_t11_dispara_colunas_e_perde_alvo():
    r = _avaliar(["T11"])
    assert not r["G06"].passou and not r["TEL05"].passou
    assert not r["G01"].passou  # Churn virou Churn_No/Churn_Yes
    assert not r["TEL03"].passou


def test_t08_alerta_customer_id():
    assert not _avaliar(["T08"])["TEL03"].passou


def test_g03_linhas_mantidas():
    assert _avaliar(["T10"])["G03"].passou  # T10 remove ~8%


def test_g07_lista_categorias():
    msg = _avaliar(["T01", "T02", "T03", "T04"])["G07"].mensagem
    assert "Boa prática: 2 (T01, T02)" in msg and "Armadilha: 1 (T03)" in msg and "Depende do objetivo: 1 (T04)" in msg


def test_nota():
    r = list(_avaliar(["T09"]).values())
    p = ck.placar(r)
    assert p["erros"] == 3 and p["alertas"] == 1 and p["passou"] == 7  # G02, TEL01, TEL02 · G05
    assert p["nota"] == 100 - 75 - 10
    assert ck.placar([])["nota"] == 100


def test_nota_minimo_zero():
    p = ck.placar(list(_avaliar(["T09", "T11"]).values()))
    assert p["nota"] == 0


def test_pendencias_e_justificativa():
    resultados = list(_avaliar(["T01"]).values())
    pend = ck.pendencias(resultados, {})
    assert [r.check.id for r in pend] == ["G04"]
    assert ck.pendencias(resultados, {"G04": {"decisao": "manter", "texto": "curta"}})
    assert ck.pendencias(resultados, {"G04": {"decisao": "corrigir", "texto": ""}})
    assert not ck.pendencias(resultados, {"G04": {"decisao": "manter", "texto": "Mantive para análise de novos"}})
    assert not ck.justificativa_valida("   14 caractere ")  # 14 após strip
    assert ck.justificativa_valida("15 caracteres!!")


def _avaliar_tema(tema_id, ids):
    tema = REGISTRY[tema_id]
    original = base(tema_id)
    pipe = ex.reexecutar(original, tema, ids)
    assert pipe.passos == ids
    return {r.check.id: r for r in ck.avaliar(tema, original, pipe.df, ids)}


def test_hotel_base_crua():
    r = _avaliar_tema("hotel", [])
    assert not r["G02"].passou and not r["HOT01"].passou
    assert not r["G04"].passou and not r["HOT03"].passou and not r["HOT04"].passou and not r["HOT05"].passou


def test_hotel_boas_praticas_resolvem():
    r = _avaliar_tema("hotel", ["H01", "H02", "H03", "H04", "H06", "H08", "H09", "H10", "H13", "H14"])
    pendentes = {k for k, v in r.items() if v.pendente}
    assert pendentes == set()


def test_hotel_h05_e_h07():
    r = _avaliar_tema("hotel", ["H05"])
    assert not r["HOT02"].passou and not r["G03"].passou
    r = _avaliar_tema("hotel", ["H07"])
    assert not r["G02"].passou and "status_Canceled" in r["G02"].mensagem and not r["HOT01"].passou


def test_noshow_regras():
    r = _avaliar_tema("noshow", [])
    assert not r["NOS04"].passou and not r["NOS05"].passou and r["G01"].passou
    r = _avaliar_tema("noshow", ["N02"])
    assert not r["NOS01"].passou
    r = _avaliar_tema("noshow", ["N03", "N05"])
    assert not r["NOS02"].passou
    r = _avaliar_tema("noshow", ["N03", "N05", "N06"])
    assert not r["NOS03"].passou and r["NOS02"].passou
    r = _avaliar_tema("noshow", ["N01", "N14"])
    assert r["G01"].passou and r["NOS04"].passou
    assert not r["NOS05"].passou and "`idade`" in r["NOS05"].mensagem
    r = _avaliar_tema("noshow", ["N14"])
    assert r["G01"].passou and "no_show_original" in r["G01"].mensagem


def test_g05_ignora_identificadores():
    assert ck.eh_identificador("PatientId") and ck.eh_identificador("id_paciente") and ck.eh_identificador("customerID")
    assert not ck.eh_identificador("TotalCharges") and not ck.eh_identificador("Neighbourhood")


def test_noshow_boas_praticas_resolvem():
    r = _avaliar_tema("noshow", ["N01", "N03", "N04", "N06", "N07", "N10", "N11", "N12"])
    assert {k for k, v in r.items() if v.pendente} == set()
