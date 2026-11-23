"""Revisão factual e gabarito do facilitador (v2)."""

from core import executor as ex
from core import gabarito as gb
from core import revisao as rv
from core.themes import REGISTRY
from tests.conftest import base

TELCO = REGISTRY["telco"]


def test_indicadores_so_fatos():
    original = base("telco")
    df = ex.reexecutar(original, TELCO, ["T01"]).df
    ind = {i.titulo: i for i in rv.indicadores(TELCO, original, df)}
    assert ind["Células vazias"].antes == "0" and ind["Células vazias"].depois == "11"
    assert "`TotalCharges`" in ind["Células vazias"].detalhe
    assert ind["Colunas de texto com valores que parecem números"].antes == "1"
    assert ind["Colunas de texto com valores que parecem números"].depois == "0"
    textos = " ".join(f"{i.titulo} {i.detalhe}" for i in ind.values()).lower()
    for palavra in ("erro", "armadilha", "boa prática", "nota"):
        assert palavra not in textos


def test_comparativo_colunas():
    original = base("telco")
    df = ex.reexecutar(original, TELCO, ["T08", "T12"]).df
    comp = rv.comparativo_colunas(original, df).set_index("Coluna")
    assert comp.loc["customerID", "Situação"] == "removida ou renomeada"
    assert comp.loc["faixa_tenure", "Situação"] == "nova"


def test_gabarito_revela_categorias_e_regras():
    original = base("telco")
    passos = ["T01", "T03", {"uid": "P9", "tipo": "livre", "acao": "remover_colunas", "params": {"colunas": ["gender"]}}]
    pipe = ex.reexecutar(original, TELCO, passos)
    itens = gb.passos_comentados(TELCO, pipe.passos, pipe.blocos)
    assert [i.categoria for i in itens] == ["boa_pratica", "armadilha", "livre"]
    assert "T02" in itens[1].sugestao
    assert "T02" in {b.id for b in gb.boas_praticas_nao_usadas(TELCO, pipe.passos)}
    regras = {r.check.id: r for r in gb.regras(TELCO, original, pipe.df, pipe.passos)}
    assert not regras["TEL04"].passou  # T03 inventou cobrança para clientes novos
