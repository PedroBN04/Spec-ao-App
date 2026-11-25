"""Jornadas simuladas (v2) com o AppTest do Streamlit, como um participante faria."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")
NOTA_DIAG = "TotalCharges parece número mas está como texto; conferir vazios e valores estranhos."


def _app() -> AppTest:
    return AppTest.from_file(APP, default_timeout=90).run()


def _botao(at, rotulo):
    return next(b for b in at.button if b.label == rotulo)


def _sem_erros(at):
    assert not at.exception, at.exception
    assert not any("Algo deu errado" in e.value for e in at.error), [e.value for e in at.error]


def _avancar(at, rotulo="Avançar"):
    _botao(at, rotulo).click().run()
    _sem_erros(at)


def _comecar(at, equipe):
    at.text_input(key="form_equipe").input(equipe)
    _botao(at, "Começar").click().run()
    _sem_erros(at)


def _ate_missao(tema_id, equipe="Equipe Teste"):
    at = _app()
    _comecar(at, equipe)
    at.button(key=f"escolher_{tema_id}").click().run()
    return at


def _ate_pipeline(tema_id):
    at = _ate_missao(tema_id)
    _avancar(at)
    at.text_area(key="w_notas_diag").input(NOTA_DIAG).run()
    _avancar(at)
    assert at.session_state.etapa == 3
    return at


def _adicionar(at, block_id):
    at.button(key=f"aplicar_{block_id}").click().run()
    _sem_erros(at)


def _textos(at) -> str:
    partes = [m.value for m in at.markdown] + [c.value for c in at.caption] + [w.value for w in at.warning]
    partes += [i.value for i in at.info] + [s.value for s in at.success]
    partes += [h.value for h in at.title] + [h.value for h in at.subheader]
    return "\n".join(partes)


# --- Etapas 0 a 2 -------------------------------------------------------------


def test_inicio_exige_equipe_e_explica_jornada():
    at = _app()
    _sem_erros(at)
    texto = _textos(at)
    assert "painel" in texto and "agente" in texto.lower()
    _botao(at, "Começar").click().run()  # sem nome: não avança e avisa
    assert at.session_state.etapa == 0
    assert any("Digite um nome" in w.value for w in at.warning)
    _comecar(at, "  Equipe Teste  ")  # digitar e clicar direto, sem Enter
    assert at.session_state.etapa == 1 and at.session_state.equipe == "Equipe Teste"


def test_missao_como_solicitacao_e_liberdade_para_ir_alem():
    at = _ate_missao("telco")
    _sem_erros(at)
    texto = _textos(at)
    assert "Diretoria de Retenção de Clientes" in texto
    assert "Você não precisa fazer exatamente o que foi pedido" in texto
    assert not _botao(at, "Avançar").disabled


@pytest.mark.parametrize("tema_id", ["telco", "hotel", "noshow"])
def test_diagnostico_sem_alertas_e_exige_anotacoes(tema_id):
    at = _ate_missao(tema_id)
    _avancar(at)
    assert at.session_state.etapa == 2
    texto = _textos(at)
    assert "Roteiro de investigação" in texto
    for denuncia in ("parecem números", "Esta coluna revela o resultado", "Alertas automáticos"):
        assert denuncia not in texto
    assert _botao(at, "Avançar").disabled
    for opcao in at.selectbox(key="diag_coluna").options[:5]:
        at.selectbox(key="diag_coluna").select(opcao).run()
        _sem_erros(at)
    at.text_area(key="w_notas_diag").input("curta").run()
    assert _botao(at, "Avançar").disabled
    at.text_area(key="w_notas_diag").input(NOTA_DIAG).run()
    assert not _botao(at, "Avançar").disabled


# --- Etapa 3: pipeline ----------------------------------------------------------


def test_pipeline_nao_revela_categoria_nem_feedback():
    at = _ate_pipeline("telco")
    for b in ["T01", "T03", "T09", "T11"]:
        _adicionar(at, b)
    texto = _textos(at)
    for palavra in ("Boa prática", "Armadilha", "Depende do objetivo", "Experimente o bloco", "calculada a partir do próprio resultado"):
        assert palavra not in texto
    assert [p["id"] for p in at.session_state.passos] == ["T01", "T03", "T09", "T11"]
    assert at.button(key="aplicar_T01").disabled and at.button(key="aplicar_T01").label == "No fluxo"


def test_pipeline_reordenar_remover_e_cascata():
    at = _ate_pipeline("telco")
    for b in ["T01", "T02", "T07"]:
        _adicionar(at, b)
    uid_t07 = at.session_state.passos[2]["uid"]
    at.button(key=f"subir_{uid_t07}").click().run()
    assert [p["id"] for p in at.session_state.passos] == ["T01", "T07", "T02"]
    uid_t01 = at.session_state.passos[0]["uid"]
    at.button(key=f"desfazer_{uid_t01}").click().run()
    _sem_erros(at)
    assert [p["id"] for p in at.session_state.passos] == ["T07"]
    assert "saiu do fluxo" in _textos(at)


def test_pipeline_bloco_personalizado():
    at = _ate_pipeline("telco")
    at.selectbox(key="nv_acao").select("criar_indicador").run()
    at.selectbox(key="nv_coluna_f").select("Churn").run()
    at.selectbox(key="nv_op").select("==").run()
    at.text_input(key="nv_valor_f").input("Yes").run()
    at.text_input(key="nv_nome_ind").input("cancelou").run()
    assert not at.button(key="nv_adicionar").disabled
    at.button(key="nv_adicionar").click().run()
    _sem_erros(at)
    passo = at.session_state.passos[0]
    assert passo["tipo"] == "livre" and "cancelou" in at.session_state.df_atual.columns
    at.text_input(key=f"nota_{passo['uid']}").input("Precisamos do alvo em 0/1").run()
    assert at.session_state.passos[0]["nota"] == "Precisamos do alvo em 0/1"


def test_pipeline_parametro_invalido_desabilita():
    at = _ate_pipeline("telco")
    at.selectbox(key="nv_acao").select("filtrar_linhas").run()
    at.selectbox(key="nv_coluna_f").select("tenure").run()
    at.text_input(key="nv_valor_f").input("abc").run()
    assert at.button(key="nv_adicionar").disabled
    assert "não é um número" in _textos(at)


def test_trocar_de_missao_pede_confirmacao_e_zera():
    at = _ate_pipeline("telco")
    _adicionar(at, "T01")
    at.button(key="nav_1").click().run()
    at.button(key="escolher_hotel").click().run()
    assert at.session_state.tema_id == "telco"
    _botao(at, "Sim, trocar de missão").click().run()
    assert at.session_state.tema_id == "hotel"
    assert at.session_state.passos == [] and at.session_state.notas_diag == ""
    assert at.button(key="nav_3").disabled


# --- Etapas 4 a 7 -----------------------------------------------------------------


def _ate_spec(tema_id, blocos):
    at = _ate_pipeline(tema_id)
    for b in blocos:
        _adicionar(at, b)
    _avancar(at)
    assert at.session_state.etapa == 4
    texto = _textos(at)
    assert "Antes × depois" in texto and "Nota" not in texto
    assert _botao(at, "Avançar").disabled
    at.checkbox(key="w_revisao_ok").check().run()
    _avancar(at)
    assert at.session_state.etapa == 5
    return at


def _preview(at) -> str:
    return next(m.value for m in at.markdown if m.value.startswith("# SPEC — "))


def _ir_passo_spec(at, n):
    while at.session_state.spec_passo < n:
        _botao(at, "Próximo passo").click().run()
        _sem_erros(at)


def _preencher_spec(at):
    at.text_area(key="w_spec_problema").input("A gerência não sabe quem cancela mais.").run()
    at.radio(key="w_spec_usuario").set_value("gestor").run()
    _ir_passo_spec(at, 1)
    at.text_area(key="w_spec_escopo_proprio").input("Painel de taxa por contrato").run()
    _ir_passo_spec(at, 3)
    at.text_area(key="w_spec_funcionalidades").input("Ver taxa geral\nFiltrar por contrato").run()
    _ir_passo_spec(at, 4)
    at.text_area(key="w_spec_regras_negocio").input("Taxa = cancelados ÷ total").run()
    _ir_passo_spec(at, 6)
    at.text_area(key="w_spec_criterios_aceitacao").input("Sem filtros mostra a taxa geral").run()


@pytest.mark.parametrize("tema_id,blocos", [
    ("telco", ["T01", "T02", "T07", "T10", "T08"]),
    ("hotel", ["H01", "H04", "H06", "H08", "H11"]),
    ("noshow", ["N01", "N03", "N05", "N06", "N14"]),
])
def test_jornada_completa_ate_gabarito(tema_id, blocos):
    at = _ate_spec(tema_id, blocos)
    assert _botao(at, "Avançar").disabled  # SPEC começa vazia
    assert "# SPEC — Solução — Equipe Teste" in _preview(at)
    _preencher_spec(at)
    texto = _preview(at)
    assert "A gerência não sabe quem cancela mais." in texto and "Painel de taxa por contrato" in texto
    for palavra in ("Boa prática", "Armadilha", "Depende do objetivo"):
        assert palavra not in texto
    assert not _botao(at, "Avançar").disabled
    _avancar(at)
    assert at.session_state.etapa == 6
    assert any("Leia o arquivo SPEC.md e construa" in c.value for c in at.code)
    assert not any(b.key == "nav_7" for b in at.button)  # gabarito só depois da exportação
    _botao(at, "Abrir revisão com o facilitador").click().run()
    _sem_erros(at)
    assert at.session_state.etapa == 7
    gab = _textos(at)
    assert "Armadilha" in gab or "Depende do objetivo" in gab or "Boa prática" in gab


def test_missao_troca_pendente_mostra_mensagem_certa():
    at = _ate_missao("telco")
    _avancar(at)
    at.text_area(key="w_notas_diag").input(NOTA_DIAG).run()
    at.button(key="nav_1").click().run()
    at.button(key="escolher_hotel").click().run()
    assert any("Confirme ou cancele a troca" in c.value for c in at.caption)
    _botao(at, "Cancelar").click().run()
    assert not _botao(at, "Avançar").disabled and at.session_state.tema_id == "telco"


def test_diagnostico_mostra_celulas_so_com_espacos():
    at = _ate_missao("telco")
    _avancar(at)
    metricas = {m.label: m.value for m in at.metric}
    assert metricas["Células só com espaços"] == "11"
    assert metricas["Células vazias (nulos)"] == "0,0%"


def test_pipeline_mover_invalido_nao_remove_passo():
    at = _ate_pipeline("telco")
    for b in ["T01", "T02"]:
        _adicionar(at, b)
    uid_t02 = at.session_state.passos[1]["uid"]
    at.text_input(key=f"nota_{uid_t02}").input("Clientes novos ainda não foram cobrados").run()
    at.button(key=f"subir_{uid_t02}").click().run()
    _sem_erros(at)
    assert [p["id"] for p in at.session_state.passos] == ["T01", "T02"]
    assert at.session_state.passos[1]["nota"] == "Clientes novos ainda não foram cobrados"
    texto = _textos(at)
    assert "A ordem não foi alterada" in texto and '"Converter `TotalCharges` para número"' in texto
    assert "T01" not in "\n".join(w.value for w in at.warning)


def test_pipeline_mostra_linhas_repetidas_no_efeito():
    at = _ate_pipeline("telco")
    _adicionar(at, "T08")
    assert "linhas repetidas: 0 → 22" in _textos(at)


def test_spec_esqueleto_preenche_vazios_e_exige_completar_lacunas():
    at = _ate_spec("telco", ["T01"])
    at.button(key="esqueleto_0").click().run()
    _sem_erros(at)
    assert at.session_state.spec["problema"].startswith("Hoje a [área cliente]")
    assert any("complete as lacunas" in c.value for c in at.caption)
    at.text_area(key="w_spec_problema").input("Hoje a diretoria não sabe quem cancela.").run()
    assert not any("passo 1: complete as lacunas" in c.value for c in at.caption)
