"""Diagnóstico automático (marco M2)."""

import pandas as pd

from core import diagnostics as dg
from core.themes import REGISTRY
from tests.conftest import base


def _tipos(alertas, coluna):
    return {a.tipo for a in alertas if a.coluna == coluna}


def test_metricas_telco():
    m = dg.metricas(base("telco"))
    assert m["linhas"] == 7043 and m["colunas"] == 21
    assert m["pct_nulos"] == 0 and m["duplicadas"] == 0
    assert m["numericas"] == 3 and m["texto"] == 18


def test_telco_totalcharges_parece_numero():
    alertas = dg.alertas_base(base("telco"))
    assert _tipos(alertas, "TotalCharges") == {"texto_numero"}
    colunas_com_alerta = {a.coluna for a in alertas}
    assert colunas_com_alerta == {"TotalCharges"}


def test_hotel_alertas():
    tema = REGISTRY["hotel"]
    alertas = dg.alertas_base(base("hotel"), tema.colunas_vazamento)
    assert "duplicadas" in {a.tipo for a in alertas if a.coluna is None}
    assert "muitos_nulos" in _tipos(alertas, "company")
    assert "negativos" in _tipos(alertas, "adr")
    assert _tipos(alertas, "reservation_status") == {"vazamento"}
    assert _tipos(alertas, "reservation_status_date") == {"vazamento", "texto_data"}


def test_noshow_alertas():
    alertas = dg.alertas_base(base("noshow"))
    assert "texto_data" in _tipos(alertas, "ScheduledDay")
    assert "texto_data" in _tipos(alertas, "AppointmentDay")
    assert "negativos" in _tipos(alertas, "Age")
    assert not _tipos(alertas, "PatientId")


def test_alertas_sinteticos():
    df = pd.DataFrame(
        {
            "constante": ["a", "a", "a", "a"],
            "num_texto": ["1", " 2", "3 ", "x"],
            "vazia": [None, None, None, 1.0],
            "datas": ["2020-01-01", "2020-02-01", "2020-03-01", None],
        }
    )
    alertas = dg.alertas_base(df)
    assert _tipos(alertas, "constante") == {"valor_unico"}
    assert "texto_numero" not in _tipos(alertas, "num_texto")  # 75% < 90%
    assert _tipos(alertas, "vazia") == {"muitos_nulos", "valor_unico"}
    assert _tipos(alertas, "datas") == {"texto_data"}


def test_texto_numero_acima_de_90_porcento():
    serie = pd.Series([str(i) for i in range(19)] + [" "])
    assert dg.parece_numero(serie)
    assert not dg.parece_data(serie)


def test_raio_x_uma_linha_por_coluna_com_significado():
    tema = REGISTRY["telco"]
    tabela = dg.raio_x(base("telco"), tema.dicionario)
    assert list(tabela["Coluna"]) == list(base("telco").columns)
    assert tabela["Significado"].str.len().gt(0).all()
    linha = tabela.set_index("Coluna").loc["TotalCharges"]
    assert linha["Tipo"] == "object" and "números" in linha["Alerta"]


def test_distribuicao_com_percentual_e_vazios():
    dist = dg.distribuicao(pd.Series(["a", "a", None, "b"]))
    assert dist.set_index("valor")["%"].to_dict() == {"a": 50.0, "(vazio)": 25.0, "b": 25.0}
    assert len(dg.distribuicao(base("hotel")["country"], top=15)) == 15


def test_telco_distribuicao_do_alvo_26_5_porcento():
    dist = dg.distribuicao(base("telco")["Churn"]).set_index("valor")["%"]
    assert dist["Yes"] == 26.5 and dist["No"] == 73.5
