"""Jornadas simuladas com o AppTest do Streamlit, como um participante faria."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _app() -> AppTest:
    return AppTest.from_file(APP, default_timeout=60).run()


def _botao(at: AppTest, rotulo: str):
    return next(b for b in at.button if b.label == rotulo)


def _sem_erros(at: AppTest):
    assert not at.exception, at.exception
    textos = [e.value for e in at.error]
    assert not any("Ops! Algo deu errado" in t for t in textos), textos


def _avancar(at: AppTest):
    _botao(at, "Avançar →").click().run()
    _sem_erros(at)


def _ate_diagnostico(tema_id: str, equipe: str = "Equipe Teste") -> AppTest:
    at = _app()
    at.text_input(key="w_equipe").input(equipe).run()
    _avancar(at)
    at.button(key=f"escolher_{tema_id}").click().run()
    _avancar(at)
    return at


def _ate_tratamento(tema_id: str) -> AppTest:
    at = _ate_diagnostico(tema_id)
    at.checkbox(key="w_diagnostico_lido").check().run()
    _avancar(at)
    assert at.session_state.etapa == 3
    return at


def _selos(at: AppTest) -> list[str]:
    return [m.value for m in at.markdown if "-badge[" in m.value]


def _aplicar(at: AppTest, block_id: str):
    at.button(key=f"aplicar_{block_id}").click().run()
    _sem_erros(at)


# --- Etapas 0 a 2 ------------------------------------------------------------


def test_boas_vindas_exige_nome_da_equipe():
    at = _app()
    _sem_erros(at)
    assert _botao(at, "Avançar →").disabled
    at.text_input(key="w_equipe").input("   ").run()
    assert _botao(at, "Avançar →").disabled
    at.text_input(key="w_equipe").input("Equipe Teste").run()
    assert not _botao(at, "Avançar →").disabled


def test_desafio_exige_tema_e_mostra_detalhes():
    at = _app()
    at.text_input(key="w_equipe").input("Equipe Teste").run()
    _avancar(at)
    assert at.session_state.etapa == 1
    assert _botao(at, "Avançar →").disabled
    at.button(key="escolher_telco").click().run()
    assert at.session_state.tema_id == "telco"
    assert not _botao(at, "Avançar →").disabled
    assert any("Problemática" in m.value for m in at.markdown)


@pytest.mark.parametrize("tema_id", ["telco", "hotel", "noshow"])
def test_diagnostico_abre_sem_erros(tema_id):
    at = _ate_diagnostico(tema_id)
    assert at.session_state.etapa == 2
    assert _botao(at, "Avançar →").disabled
    at.checkbox(key="w_diagnostico_lido").check().run()
    assert not _botao(at, "Avançar →").disabled
    for opcao in at.selectbox[0].options[:4]:
        at.selectbox[0].select(opcao).run()
        _sem_erros(at)


def test_nome_da_equipe_e_checkbox_sobrevivem_a_navegacao():
    at = _ate_diagnostico("telco")
    at.checkbox(key="w_diagnostico_lido").check().run()
    _botao(at, "← Voltar").click().run()
    _botao(at, "← Voltar").click().run()
    assert at.text_input(key="w_equipe").value == "Equipe Teste"
    _avancar(at)
    _avancar(at)
    assert at.checkbox(key="w_diagnostico_lido").value is True


# --- Etapa 3 -----------------------------------------------------------------


def test_tratamento_categoria_so_aparece_depois_de_aplicar():
    at = _ate_tratamento("telco")
    assert _botao(at, "Avançar →").disabled
    assert not _selos(at)
    assert not any("Experimente o bloco" in w.value for w in at.warning)
    _aplicar(at, "T01")
    assert at.button(key="aplicar_T01").disabled and at.button(key="aplicar_T01").label == "✓ Aplicado"
    assert at.session_state.passos == ["T01"]
    _aplicar(at, "T03")
    assert _selos(at) == [":green-badge[✅ Boa prática]", ":red-badge[⚠️ Armadilha]"]
    assert any("Experimente o bloco **T02**" in w.value for w in at.warning)
    assert not _botao(at, "Avançar →").disabled


def test_tratamento_prerequisito_desabilitado():
    at = _ate_tratamento("telco")
    assert at.button(key="aplicar_T02").disabled
    assert any("precisa que o bloco T01" in c.value for c in at.caption)
    _aplicar(at, "T01")
    assert not at.button(key="aplicar_T02").disabled


def test_tratamento_desfazer_t01_remove_t02_com_aviso():
    at = _ate_tratamento("telco")
    for b in ["T01", "T02", "T07"]:
        _aplicar(at, b)
    assert at.session_state.passos == ["T01", "T02", "T07"]
    at.button(key="desfazer_T01").click().run()
    _sem_erros(at)
    assert at.session_state.passos == ["T07"]
    assert any("O passo **T02** também foi removido" in w.value for w in at.warning)
    assert at.session_state.df_atual["Churn"].isin([0, 1]).all()
    assert at.session_state.df_atual["TotalCharges"].dtype == object


def test_tratamento_armadilha_que_remove_linhas_mostra_erro():
    at = _ate_tratamento("telco")
    _aplicar(at, "T11")
    assert at.session_state.df_atual.shape[1] > 1000
    assert any("mostrando só as 50 primeiras" in c.value for c in at.caption)


def test_trocar_de_desafio_com_trabalho_feito_pede_confirmacao():
    at = _ate_tratamento("telco")
    _aplicar(at, "T01")
    for _ in range(2):
        _botao(at, "← Voltar").click().run()
    at.button(key="escolher_hotel").click().run()
    assert at.session_state.tema_id == "telco"
    assert any("Trocar para" in w.value for w in at.warning)
    _botao(at, "Cancelar").click().run()
    assert at.session_state.tema_id == "telco" and at.session_state.passos == ["T01"]
    at.button(key="escolher_hotel").click().run()
    _botao(at, "Sim, trocar de desafio").click().run()
    assert at.session_state.tema_id == "hotel"
    assert at.session_state.passos == [] and at.session_state.df_atual is None
    assert at.session_state.diagnostico_lido is False


# --- Etapa 4 -----------------------------------------------------------------


def test_checklist_vazamento_e_justificativas():
    at = _ate_tratamento("telco")
    for b in ["T01", "T02", "T09"]:
        _aplicar(at, b)
    _avancar(at)
    assert at.session_state.etapa == 4
    assert any("taxa_churn_pagamento" in m.value for m in at.markdown)
    assert _botao(at, "Avançar →").disabled
    # G02 e TEL01 pendentes
    at.radio(key="w_dec_G02").set_value("manter").run()
    at.text_area(key="w_just_G02").input("curta").run()
    assert _botao(at, "Avançar →").disabled
    at.text_area(key="w_just_G02").input("Mantida só para a aula de vazamento").run()
    assert _botao(at, "Avançar →").disabled  # TEL01 ainda pendente
    at.radio(key="w_dec_TEL01").set_value("corrigir").run()
    assert _botao(at, "Avançar →").disabled
    at.button(key="corrigir_TEL01").click().run()
    assert at.session_state.etapa == 3
    at.button(key="desfazer_T09").click().run()
    _avancar(at)
    _sem_erros(at)
    assert not _botao(at, "Avançar →").disabled


def test_checklist_sem_pendencias_com_boas_praticas():
    at = _ate_tratamento("telco")
    for b in ["T01", "T02", "T05", "T07"]:
        _aplicar(at, b)
    _avancar(at)
    assert not _botao(at, "Avançar →").disabled
    assert any(m.value == "100/100" for m in at.metric)


# --- Etapas 5 e 6 ------------------------------------------------------------


def _ate_spec(blocos, justificar=None):
    at = _ate_tratamento("telco")
    for b in blocos:
        _aplicar(at, b)
    _avancar(at)
    for cid, texto in (justificar or {}).items():
        at.radio(key=f"w_dec_{cid}").set_value("manter").run()
        at.text_area(key=f"w_just_{cid}").input(texto).run()
    _avancar(at)
    assert at.session_state.etapa == 5
    return at


def _preview(at) -> str:
    return next(m.value for m in at.markdown if m.value.startswith("# SPEC — "))


def test_jornada_completa_telco_ate_exportar():
    # 2 boas práticas, 1 armadilha (T10), 1 "depende" (T04) e um alerta justificado
    at = _ate_spec(["T01", "T02", "T07", "T10", "T04"])
    assert not _botao(at, "Avançar →").disabled  # defaults do tema preenchem os obrigatórios
    # preview acompanha cada campo
    at.text_area(key="w_spec_problema").input("Problema editado pela equipe para o teste").run()
    assert "Problema editado pela equipe para o teste" in _preview(at)
    at.text_area(key="w_spec_problema").input("").run()
    assert _botao(at, "Avançar →").disabled
    assert any("passo 1: Problema" in c.value for c in at.caption)
    at.text_area(key="w_spec_problema").input("Reduzir cancelamentos de clientes novos").run()
    for _ in range(7):
        _botao(at, "Próximo passo ▶").click().run()
        _sem_erros(at)
    at.text_area(key="w_spec_roteiro").input("Problema → dados → demo").run()
    assert "Roteiro: Problema → dados → demo" in _preview(at)
    _botao(at, "◀ Passo anterior").click().run()
    at.text_area(key="w_spec_criterios_aceitacao").input("").run()
    assert _botao(at, "Avançar →").disabled
    at.text_area(key="w_spec_criterios_aceitacao").input("O app abre sem erros").run()
    _avancar(at)
    assert at.session_state.etapa == 6
    assert any("Leia SPEC.md e construa" in c.value for c in at.code)


def test_spec_reflete_justificativa_do_checklist():
    at = _ate_spec(["T01"], justificar={"G04": "Vou tratar os vazios no app final"})
    texto = _preview(at)
    assert "Justificativa da equipe: Vou tratar os vazios no app final" in texto
    assert "1. Converter `TotalCharges` para número — Boa prática" in texto


def test_respostas_sobrevivem_a_ida_e_volta():
    at = _ate_spec(["T01", "T02"])
    at.text_input(key="w_spec_nome_solucao").input("Radar de Churn").run()
    _botao(at, "Próximo passo ▶").click().run()
    at.checkbox(key="w_spec_aprofundamentos_0").check().run()
    _avancar(at)
    _botao(at, "← Voltar").click().run()
    _botao(at, "← Voltar").click().run()
    _avancar(at)
    assert at.session_state.spec["nome_solucao"] == "Radar de Churn"
    assert "# SPEC — Radar de Churn" in _preview(at)
    assert at.session_state.spec["aprofundamentos"] == [at.session_state.spec["aprofundamentos"][0]]


# --- Jornadas completas dos três temas ------------------------------------------


def _jornada_completa(tema_id, blocos):
    import io

    import pandas as pd

    from core import exporter
    from core.themes import REGISTRY
    from ui.steps.s5_spec import estado_spec  # noqa: F401  (garante que o módulo importa)

    at = _ate_diagnostico(tema_id, equipe="Equipe São João")
    at.checkbox(key="w_diagnostico_lido").check().run()
    _avancar(at)
    for b in blocos:
        _aplicar(at, b)
    assert at.session_state.passos == blocos
    _avancar(at)
    for radio in [r for r in at.radio if r.key and r.key.startswith("w_dec_")]:
        cid = radio.key.removeprefix("w_dec_")
        radio.set_value("manter").run()
        at.text_area(key=f"w_just_{cid}").input(f"Decisão consciente da equipe sobre {cid}").run()
    assert not _botao(at, "Avançar →").disabled
    _avancar(at)
    assert not _botao(at, "Avançar →").disabled
    _avancar(at)
    assert at.session_state.etapa == 6
    tema = REGISTRY[tema_id]
    df = at.session_state.df_atual
    texto = _preview_export(at)
    lido = pd.read_csv(io.BytesIO(exporter.gerar_csv(df)), encoding="utf-8-sig")
    assert lido.shape == df.shape
    for c in df.columns:
        assert f"| `{c}` |" in texto
    for b in blocos:
        assert tema.bloco(b).titulo in texto
    return at, texto


def _preview_export(at):
    """Monta a SPEC com o mesmo estado da sessão (o AppTest não clica em download)."""
    from core import checklist as ck
    from core import spec_builder as sb
    from core.themes import REGISTRY

    ss = at.session_state
    tema = REGISTRY[ss.tema_id]
    import pandas as pd

    original = pd.read_csv(Path(APP).parent / tema.arquivo)
    e = sb.EstadoSpec(tema, ss.equipe, ss.df_atual, list(ss.passos), ss.resultados,
                      ck.avaliar(tema, original, ss.df_atual, list(ss.passos)), ss.justificativas, ss.spec)
    return sb.montar_spec(e)


def test_jornada_completa_hotel():
    _, texto = _jornada_completa("hotel", ["H01", "H02", "H03", "H04", "H06", "H08", "H11", "H12", "H14"])
    assert "Alvo: `is_canceled`" in texto
    assert "Depende do objetivo" in texto and "Armadilha" in texto
    assert "`adr` = 0 é válido" in texto


def test_jornada_completa_noshow():
    _, texto = _jornada_completa("noshow", ["N01", "N03", "N05", "N06", "N08", "N13", "N14"])
    assert "Alvo: `faltou`" in texto
    assert "Erro mantido" in texto  # NOS03 (N05+N06 apagaram 1/3) justificado
    assert "| `idade` |" in texto and "| `Age` |" not in texto


def test_hotel_h07_desabilita_h08_na_tela():
    at = _ate_tratamento("hotel")
    _aplicar(at, "H07")
    assert at.button(key="aplicar_H08").disabled
    assert any("`reservation_status`, que não existe mais" in c.value for c in at.caption)


def test_hotel_h05_mostra_erro_de_remocao():
    at = _ate_tratamento("hotel")
    _aplicar(at, "H05")
    assert any("Este passo removeu" in e.value for e in at.error)


def test_noshow_n14_desabilita_nomes_antigos_na_tela():
    at = _ate_tratamento("noshow")
    _aplicar(at, "N14")
    for b in ["N01", "N03", "N07", "N09", "N13"]:
        assert at.button(key=f"aplicar_{b}").disabled
