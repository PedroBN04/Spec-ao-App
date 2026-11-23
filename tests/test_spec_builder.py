"""Assistente da SPEC e exportação (seções 9, 9.1 e 10)."""

import io
from datetime import date

import pandas as pd

from core import checklist as ck
from core import executor as ex
from core import exporter
from core import spec_builder as sb
from core.themes import REGISTRY
from tests.conftest import base

TELCO = REGISTRY["telco"]


def _estado(ids, justificativas=None, respostas=None, tema=TELCO, tema_id="telco"):
    original = base(tema_id)
    pipe = ex.reexecutar(original, tema, ids)
    assert pipe.passos == ids
    return sb.EstadoSpec(
        tema=tema,
        equipe="Equipe Ação",
        df=pipe.df,
        passos=pipe.passos,
        resultados=pipe.resultados,
        checks=ck.avaliar(tema, original, pipe.df, pipe.passos),
        justificativas=justificativas or {},
        respostas=respostas or sb.respostas_iniciais(tema),
        data=date(2026, 11, 24),
    )


def _secao(texto, titulo):
    inicio = texto.index(titulo)
    resto = texto[inicio + len(titulo):]
    proximas = [resto.index(m) for m in ("\n## ", "\n### ") if m in resto]
    return resto[: min(proximas)] if proximas else resto


def test_spec_tem_todas_as_colunas_do_df_final_na_secao_3():
    e = _estado(["T01", "T02", "T07", "T12", "T08"])
    texto = sb.montar_spec(e)
    secao3 = _secao(texto, "## 3. Dados")
    for coluna in e.df.columns:
        assert f"| `{coluna}` |" in secao3
    assert "customerID" not in secao3
    assert f"{len(e.df)} linhas, {e.df.shape[1]} colunas" in secao3
    assert "| `faixa_tenure` | texto | Faixa de tempo de casa" in secao3
    assert "| `TotalCharges` | número decimal |" in secao3


def test_spec_lista_blocos_aplicados_com_categoria_na_3_1():
    e = _estado(["T01", "T03", "T04"])
    secao = _secao(sb.montar_spec(e), "### 3.1 Tratamentos já aplicados (não refazer)")
    linhas = [l for l in secao.strip().splitlines() if l]
    assert linhas[0].startswith("1. Converter `TotalCharges` para número — Boa prática — A coluna era texto")
    assert linhas[1].startswith("2. Preencher `TotalCharges` vazio com a média — Armadilha —")
    assert linhas[2].startswith("3. Remover linhas com qualquer valor vazio — Depende do objetivo —")


def test_spec_justificativa_na_3_2_e_vazamento_na_3_3():
    just = {"G02": {"decisao": "manter", "texto": "Mantida para a aula de vazamento"},
            "TEL01": {"decisao": "corrigir", "texto": ""}}
    texto = sb.montar_spec(_estado(["T09"], just))
    secao = _secao(texto, "### 3.2 Decisões conscientes e justificativas")
    assert "Erro mantido — Nenhuma coluna que revela o resultado" in secao
    assert "Justificativa da equipe: Mantida para a aula de vazamento" in secao
    assert "Sem coluna derivada do alvo" not in secao  # TEL01 não foi justificado
    assert "Não usar como entrada de previsão: `taxa_churn_pagamento`" in _secao(texto, "### 3.3 Cuidados com os dados")


def test_secoes_vazias_nao_aparecem():
    r = sb.respostas_iniciais(TELCO) | {"fora_escopo": "", "metrica_sucesso": "", "formato": "", "roteiro": ""}
    texto = sb.montar_spec(_estado([], respostas=r))
    assert "### 3.1" not in texto and "### 3.2" not in texto and "### Fora do escopo" not in texto
    assert "## 8. Apresentação" not in texto and "Métrica de sucesso" not in texto
    assert "## 9. Instruções para o agente de código" in texto


def test_template_cabecalho_e_secoes_em_ordem():
    r = sb.respostas_iniciais(TELCO) | {"fora_escopo": "Login\nPrevisão com IA", "aprofundamentos": [TELCO.aprofundamentos[1]]}
    texto = sb.montar_spec(_estado(["T01", "T02"], respostas=r))
    assert texto.startswith(f"# SPEC — Painel — {TELCO.nome}\nEquipe: Equipe Ação · Desafio: {TELCO.nome} · Gerado em 24/11/2026")
    titulos = ["## 1. Contexto e problema", "## 2. Objetivo e escopo", "### Entra nesta versão", "### Fora do escopo",
               "## 3. Dados", "### 3.1", "### 3.3", "## 4. Funcionalidades", "## 5. Regras de negócio",
               "## 6. Arquitetura e restrições", "## 7. Critérios de aceitação", "## 8. Apresentação", "## 9. Instruções"]
    posicoes = [texto.index(t) for t in titulos]
    assert posicoes == sorted(posicoes)
    assert "Usuário principal: Gestor(a)" in texto
    assert "- Estimativa de receita mensal em risco" in texto
    assert "- [ ] Sem filtros, o painel mostra a taxa de churn geral calculada do CSV" in texto
    assert "- Stack: Python + Streamlit + pandas + plotly" in texto


def test_significado_editado_vai_para_a_spec():
    r = sb.respostas_iniciais(TELCO) | {"significados": {"tenure": "Meses de contrato do cliente"}}
    assert "| `tenure` | número inteiro | Meses de contrato do cliente |" in sb.montar_spec(_estado([], respostas=r))


def test_obrigatorios():
    r = sb.respostas_iniciais(TELCO)
    assert sb.faltando_por_passo(r) == {}
    vazio = r | {"problema": " ", "usuario": "outro", "usuario_outro": "", "proposta_itens": [],
                 "funcionalidades": "\n \n", "regras_negocio": "", "criterios_aceitacao": ""}
    assert set(sb.faltando_por_passo(vazio)) == {0, 1, 3, 4, 6}
    assert sb.faltando_por_passo(r | {"usuario": "outro", "usuario_outro": "Marketing"}) == {}


def test_linhas_limpa_marcadores():
    assert sb.linhas("- a\n\n* b\n• c\n  ") == ["a", "b", "c"]


def test_csv_utf8_sig_sem_indice_e_mesmo_formato():
    e = _estado(["T01", "T02", "T12"])
    dados = exporter.gerar_csv(e.df)
    assert dados.startswith("﻿".encode("utf-8"))
    lido = pd.read_csv(io.BytesIO(dados), encoding="utf-8-sig")
    assert lido.shape == e.df.shape and list(lido.columns) == list(e.df.columns)
    assert "Unnamed: 0" not in lido.columns


def test_csv_acentos():
    df = pd.DataFrame({"bairro": ["SÃO JOSÉ", "JARDIM CAMBURI"], "dia": ["Terça", "Sábado"]})
    assert pd.read_csv(io.BytesIO(exporter.gerar_csv(df)), encoding="utf-8-sig").equals(df)


def test_csv_datas_em_iso():
    df = pd.DataFrame({
        "so_data": pd.to_datetime(["2016-04-29", "2016-05-02"]),
        "com_hora": pd.to_datetime(["2016-04-29T18:38:08Z", "2016-05-02T08:00:00Z"]),
    })
    texto = exporter.gerar_csv(df).decode("utf-8-sig")
    assert "2016-04-29,2016-04-29 18:38:08" in texto


def test_nomes_de_arquivo():
    assert exporter.nome_arquivo("Equipe Ação & Cia", "SPEC.md") == "equipe_acao_cia_SPEC.md"
    assert exporter.nome_arquivo("  Força   Tarefa  ", "dados_tratados.csv") == "forca_tarefa_dados_tratados.csv"
    assert exporter.slug_equipe("!!!") == "equipe"


def test_coluna_transformada_ganha_aviso_no_significado():
    texto = sb.montar_spec(_estado(["T07"]))
    assert "| `Churn` | número inteiro | Alvo: o cliente cancelou? (Yes = cancelou, No = continua). ATENÇÃO: valores convertidos pelo bloco T07 (Converter Churn para 0/1) |" in texto


def test_colunas_citadas_que_nao_existem():
    e = _estado(["T08"])
    criterios = sb.respostas_iniciais(TELCO)["criterios_aceitacao"]
    assert sb.colunas_citadas_ausentes(criterios, TELCO, e.df) == ["customerID"]
    assert sb.colunas_citadas_ausentes(criterios, TELCO, base("telco")) == []
    assert sb.colunas_citadas_ausentes("taxa por Contract", TELCO, e.df) == []
