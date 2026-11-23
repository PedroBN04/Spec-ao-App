"""Assistente da SPEC (v2) e exportação."""

import io
from datetime import date

import pandas as pd

from core import executor as ex
from core import exporter
from core import spec_builder as sb
from core.themes import REGISTRY
from tests.conftest import base

TELCO = REGISTRY["telco"]


def _preenchidas(**extra):
    r = sb.respostas_iniciais(TELCO)
    r.update({
        "problema": "A gerência não sabe quais perfis cancelam mais.",
        "usuario": "gestor",
        "escopo_pedido": [TELCO.proposta_inicial[0]],
        "funcionalidades": "Ver a taxa de churn geral",
        "regras_negocio": "Taxa = soma de Churn ÷ clientes do filtro",
        "criterios_aceitacao": "Sem filtros mostra a taxa geral",
    })
    r.update(extra)
    return r


def _estado(passos, respostas=None, notas="", tema=TELCO, tema_id="telco"):
    original = base(tema_id)
    pipe = ex.reexecutar(original, tema, passos)
    assert [ex.uid(p) for p in pipe.passos] == [ex.uid(p) for p in passos]
    return sb.EstadoSpec(tema=tema, equipe="Equipe Ação", df=pipe.df, passos=pipe.passos, blocos=pipe.blocos,
                         resultados=pipe.resultados, respostas=respostas or _preenchidas(), notas_revisao=notas,
                         data=date(2026, 11, 24))


def _secao(texto, titulo):
    resto = texto[texto.index(titulo) + len(titulo):]
    proximas = [resto.index(m) for m in ("\n## ", "\n### ") if m in resto]
    return resto[: min(proximas)] if proximas else resto


def test_respostas_comecam_vazias_e_obrigatorios_faltam():
    r = sb.respostas_iniciais(TELCO)
    assert not r["problema"] and r["usuario"] is None and not r["funcionalidades"] and r["escopo_pedido"] == []
    assert set(sb.faltando_por_passo(r)) == {0, 1, 3, 4, 6}
    assert sb.faltando_por_passo(_preenchidas()) == {}
    assert 1 not in sb.faltando_por_passo(sb.respostas_iniciais(TELCO) | {"escopo_proprio": "Meu item"})


def test_passos_guia_e_exemplos_de_outro_dominio():
    assert len(sb.PASSOS) == 8
    for p in sb.PASSOS:
        assert p.guia and p.exemplo and p.porque
    assert "Biblioteca Municipal" in sb.PASSOS[0].exemplo
    exemplos = " ".join(p.exemplo for p in sb.PASSOS)
    for palavra in ("churn", "Churn", "cancelamento", "hotel", "consulta"):
        assert palavra not in exemplos  # exemplos são de outro domínio


def test_spec_tem_todas_as_colunas_do_df_final_na_secao_3():
    e = _estado(["T01", "T02", "T07", "T12", "T08"])
    secao3 = _secao(sb.montar_spec(e), "## 3. Dados")
    for coluna in e.df.columns:
        assert f"| `{coluna}` |" in secao3
    assert "| `customerID` |" not in secao3
    assert "| `Churn` | número inteiro | 0, 1 |" in secao3


def test_3_1_lista_passos_sem_categoria_e_com_motivo():
    passos = [
        {"uid": "P1", "tipo": "catalogo", "id": "T01", "nota": "estava como texto"},
        {"uid": "P2", "tipo": "catalogo", "id": "T03", "nota": ""},
        {"uid": "P3", "tipo": "livre", "acao": "remover_colunas", "params": {"colunas": ["gender"]}, "nota": "não usamos"},
    ]
    texto = sb.montar_spec(_estado(passos))
    secao = _secao(texto, "### 3.1 Tratamentos já aplicados (não refazer)")
    linhas = [l for l in secao.strip().splitlines() if l]
    assert linhas[0] == "1. Converter `TotalCharges` para número — motivo da equipe: estava como texto"
    assert linhas[1] == "2. Preencher `TotalCharges` vazio com a média"
    assert linhas[2] == "3. Remover `gender` — motivo da equipe: não usamos"
    for palavra in ("Boa prática", "Armadilha", "Depende do objetivo"):
        assert palavra not in texto


def test_coluna_criada_por_bloco_personalizado():
    passos = [{"uid": "P1", "tipo": "livre", "acao": "calcular_coluna",
               "params": {"coluna_a": "MonthlyCharges", "conta": "*", "coluna_b": "tenure", "nome": "estimado"}}]
    texto = sb.montar_spec(_estado(passos))
    assert "Criada pelo passo \"Criar estimado = MonthlyCharges vezes tenure\"" in texto


def test_3_2_e_3_3_vem_da_equipe():
    r = _preenchidas(cuidados="Churn 1 = cancelou\n- tenure 0 = cliente novo")
    texto = sb.montar_spec(_estado(["T01"], respostas=r, notas="Mantivemos os vazios de propósito"))
    assert "- Mantivemos os vazios de propósito" in _secao(texto, "### 3.2 Decisões e observações da revisão")
    s33 = _secao(texto, "### 3.3 Cuidados com os dados")
    assert "- Churn 1 = cancelou" in s33 and "- tenure 0 = cliente novo" in s33
    assert "### 3.2" not in sb.montar_spec(_estado(["T01"]))


def test_nada_do_tema_entra_sem_a_equipe_escrever():
    texto = sb.montar_spec(_estado([], respostas=sb.respostas_iniciais(TELCO)))
    for d in TELCO.spec_defaults.values():
        for item in (d if isinstance(d, list) else [d]):
            if item not in ("gestor",):
                assert item not in texto
    for _, obs in TELCO.observacoes:
        assert obs not in texto
    assert "## 1." not in texto and "## 4." not in texto and "## 9. Instruções" in texto


def test_template_cabecalho_e_secoes_em_ordem():
    r = _preenchidas(fora_escopo="Login", escopo_proprio="Mapa de calor", nome_solucao="Radar",
                     stack="Python", restricoes=[sb.RESTRICOES[0]], metrica_sucesso="Reduzir churn",
                     formato="Pitch", roteiro="Problema → demo", cuidados="X")
    texto = sb.montar_spec(_estado(["T01"], respostas=r, notas="ok"))
    assert texto.startswith(f"# SPEC — Radar\nEquipe: Equipe Ação · Desafio: {TELCO.nome} · Gerado em 24/11/2026")
    titulos = ["## 1.", "## 2.", "### Entra nesta versão", "### Fora do escopo", "## 3. Dados", "### 3.1",
               "### 3.2", "### 3.3", "## 4.", "## 5.", "## 6.", "## 7.", "## 8.", "## 9."]
    pos = [texto.index(t) for t in titulos]
    assert pos == sorted(pos)
    assert "- Mapa de calor" in texto and "Usuário principal: Gestor(a)" in texto
    assert "Números de referência" in texto and "média de `Churn`" not in texto  # Churn ainda é Yes/No
    assert 'proporção de `Churn` = "Yes": 26,5%' in texto


def test_nome_padrao_da_solucao():
    assert sb.montar_spec(_estado([])).startswith("# SPEC — Solução — Equipe Ação")


def test_valores_reais():
    s = pd.Series
    assert sb.valores_coluna(s(["No", "Yes", "No", None])) == "No, Yes; 1 vazio(s)"
    assert sb.valores_coluna(s([1.5, 2.25, 10.0])) == "1.50 a 10"
    assert sb.valores_coluna(s([0, 1, 1])) == "0, 1"
    assert sb.valores_coluna(pd.to_datetime(s(["2016-04-29", "2016-06-08"]))) == "2016-04-29 a 2016-06-08"


def test_numeros_de_referencia_noshow_usa_faltou():
    tema = REGISTRY["noshow"]
    texto = sb.montar_spec(_estado(["N01"], tema=tema, tema_id="noshow"))
    assert "média de `faltou` = 19,9%" in texto


def test_colunas_citadas_que_nao_existem():
    e = _estado(["T08"])
    assert sb.colunas_citadas_ausentes("Lista com customerID e tenure", TELCO, e.df) == ["customerID"]
    assert sb.colunas_citadas_ausentes("taxa por Contract", TELCO, e.df) == []


def test_linhas_limpa_marcadores_e_numeracao():
    assert sb.linhas("- a\n\n* b\n• c\n1. d\n2) e") == ["a", "b", "c", "d", "e"]


def test_csv_utf8_sig_sem_indice_e_mesmo_formato():
    e = _estado(["T01", "T02", "T12"])
    dados = exporter.gerar_csv(e.df)
    assert dados.startswith("﻿".encode("utf-8"))
    lido = pd.read_csv(io.BytesIO(dados), encoding="utf-8-sig")
    assert lido.shape == e.df.shape and list(lido.columns) == list(e.df.columns)


def test_csv_acentos_e_datas():
    df = pd.DataFrame({"bairro": ["SÃO JOSÉ"], "d": pd.to_datetime(["2016-04-29T18:38:08Z"])})
    texto = exporter.gerar_csv(df).decode("utf-8-sig")
    assert "SÃO JOSÉ,2016-04-29 18:38:08" in texto


def test_nomes_de_arquivo():
    assert exporter.nome_arquivo("Equipe Ação & Cia", "SPEC.md") == "equipe_acao_cia_SPEC.md"
    assert exporter.slug_equipe("!!!") == "equipe"
