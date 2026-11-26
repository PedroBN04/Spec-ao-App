"""Melhorias da proposta da equipe (exportação, rascunho, traduções, significado, gabarito)."""

import io
import json
import zipfile

import pandas as pd
import pytest

from core import diagnostics as dg
from core import executor as ex
from core import exporter
from core import gabarito as gb
from core import rascunho
from core import spec_builder as sb
from core.themes import REGISTRY
from tests.conftest import base

TELCO = REGISTRY["telco"]


def test_kit_zip_com_nomes_finais_e_xlsx_legivel():
    df = ex.reexecutar(base("telco"), TELCO, ["T01", "T02", "T12"]).df
    kit = zipfile.ZipFile(io.BytesIO(exporter.gerar_zip(df, "# SPEC — teste")))
    assert sorted(kit.namelist()) == ["SPEC.md", "dados_tratados.csv", "dados_tratados_excel.xlsx"]
    assert kit.read("SPEC.md").decode("utf-8") == "# SPEC — teste"
    xlsx = pd.read_excel(io.BytesIO(kit.read("dados_tratados_excel.xlsx")))
    assert xlsx.shape == df.shape and list(xlsx.columns) == list(df.columns)
    assert pd.api.types.is_float_dtype(xlsx["MonthlyCharges"])  # número de verdade, não texto
    assert "Unnamed: 0" not in xlsx.columns


def test_xlsx_com_datas_e_acentos():
    df = pd.DataFrame({"bairro": ["SÃO JOSÉ"], "d": pd.to_datetime(["2016-04-29T18:38:08Z"])})
    lido = pd.read_excel(io.BytesIO(exporter.gerar_xlsx(df)))
    assert lido.loc[0, "bairro"] == "SÃO JOSÉ" and lido.loc[0, "d"] == pd.Timestamp("2016-04-29 18:38:08")


def test_kit_sem_xlsx_para_base_muito_larga():
    df = ex.executar_codigo(TELCO.bloco("T11").codigo, base("telco"))
    assert not exporter.xlsx_viavel(df)


def test_rascunho_ida_e_volta():
    estado = {"equipe": "Equipe Ação", "tema_id": "telco", "notas_diag": "anotações", "notas_revisao": "",
              "revisao_ok": True, "prox_uid": 4, "spec_passo": 2, "etapa": 5, "max_etapa": 5, "exportou": False,
              "passos": [{"uid": "P1", "tipo": "catalogo", "id": "T01", "nota": "texto"},
                         {"uid": "P2", "tipo": "livre", "acao": "remover_colunas", "params": {"colunas": ["gender"]},
                          "nota": ""}],
              "spec": {"problema": "x", "escopo_pedido": ["a"], "significados": {"tenure": "meses"}}}
    lido = rascunho.ler(rascunho.gerar(estado))
    assert lido["passos"] == estado["passos"] and lido["spec"] == estado["spec"] and lido["etapa"] == 5
    pipe = ex.reexecutar(base("telco"), TELCO, lido["passos"])
    assert [ex.uid(p) for p in pipe.passos] == ["P1", "P2"]


@pytest.mark.parametrize("conteudo,trecho", [
    (b"nao e json", "não é um rascunho válido"),
    (json.dumps({"app": "outro"}).encode(), "não é um rascunho do Da Spec ao App"),
    (json.dumps({"app": "da-spec-ao-app", "tema_id": "xyz"}).encode(), "missão que não existe"),
    (json.dumps({"app": "da-spec-ao-app", "tema_id": "telco",
                 "passos": [{"uid": "P1", "tipo": "catalogo", "id": "H01"}]}).encode(), "bloco que não existe"),
    (json.dumps({"app": "da-spec-ao-app", "tema_id": "telco",
                 "passos": [{"uid": "P1", "tipo": "livre", "acao": "exec", "params": {}}]}).encode(), "inválido"),
    (json.dumps({"app": "da-spec-ao-app", "tema_id": "telco", "spec": {"problema": {"x": 1}}}).encode(), "formato"),
])
def test_rascunho_invalido_tem_mensagem_simples(conteudo, trecho):
    with pytest.raises(rascunho.RascunhoInvalido, match=trecho):
        rascunho.ler(conteudo)


def test_traducoes_cobrem_colunas_e_valores_comuns():
    for tema in REGISTRY.values():
        assert set(pd.read_csv(tema.arquivo, nrows=1).columns) <= set(tema.nomes_pt)
    assert TELCO.valores_pt["Month-to-month"] == "Mensal"
    freq = dg.tabela_frequentes(base("telco")["Contract"], TELCO.valores_pt)
    assert list(freq.columns) == ["Valor", "Em português", "Linhas", "% da base"]
    assert freq.iloc[0].tolist() == ["Month-to-month", "Mensal", "3.875", "55,0%"]


def test_raio_x_e_estatisticas_em_formato_brasileiro():
    raio = dg.raio_x_v2(base("telco"), TELCO.dicionario, TELCO.nomes_pt).set_index("Coluna")
    assert raio.loc["MonthlyCharges", "Em português"] == "mensalidade"
    assert raio.loc["MonthlyCharges", "Máximo"] == "118,75" and raio.loc["customerID", "Distintos"] == "7.043"
    assert dg.estatisticas(base("telco")["MonthlyCharges"])["Média"].count(",") == 1


def test_metricas_contam_celulas_so_com_espacos():
    assert dg.metricas(base("telco"))["espacos"] == 11
    assert dg.metricas(base("hotel"))["espacos"] == 0


def test_significado_acompanha_conversao_conhecida():
    pipe = ex.reexecutar(base("telco"), TELCO, ["T05", "T07"])
    tabela = sb.tabela_dados(TELCO, pipe.df, {}, {}, None, pipe.blocos, sb.catalogo_aplicado(pipe.passos))
    sig = tabela.set_index("Coluna")["Significado"]
    assert sig["Churn"] == "Alvo: o cliente cancelou? (1 = cancelou, 0 = continua)"
    assert sig["SeniorCitizen"] == "Cliente idoso? (Yes = sim, No = não)"


def test_texto_sem_tempo_fixo():
    assert all("1 hora" not in p.porque for p in sb.PASSOS)


def test_gabarito_sem_regra_duplicada_e_explica_repetidas():
    original = base("telco")
    pipe = ex.reexecutar(original, TELCO, ["T08"])
    ids = [r.check.id for r in gb.regras(TELCO, original, pipe.df, pipe.passos)]
    assert "G06" not in ids and "TEL05" in ids
    hotel = REGISTRY["hotel"]
    assert "G06" in [r.check.id for r in gb.regras(hotel, base("hotel"), base("hotel"), [])]
    item = gb.passos_comentados(TELCO, pipe.passos, pipe.blocos, pipe.resultados)[0]
    assert "surgiram 22 linhas repetidas" in item.observacao


def test_contagem_de_repetidas_desligada_em_base_larga():
    _, r = ex.aplicar(base("telco"), TELCO.bloco("T11"))
    assert r.repetidas_antes is None and r.repetidas_depois is None
    _, r = ex.aplicar(base("telco"), TELCO.bloco("T08"))
    assert (r.repetidas_antes, r.repetidas_depois) == (0, 22)
