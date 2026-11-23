"""Teste de fumaça da interface com o AppTest do Streamlit (etapas 0 a 2)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


def _app() -> AppTest:
    at = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "app.py"), default_timeout=60)
    return at.run()


def _botao(at: AppTest, rotulo: str):
    return next(b for b in at.button if b.label == rotulo)


def _sem_erros(at: AppTest):
    assert not at.exception, at.exception
    assert not at.error, [e.value for e in at.error]


def _ate_diagnostico(tema_id: str) -> AppTest:
    at = _app()
    at.text_input(key="w_equipe").input("Equipe Teste").run()
    _botao(at, "Avançar →").click().run()
    at.button(key=f"escolher_{tema_id}").click().run()
    _botao(at, "Avançar →").click().run()
    return at


def test_boas_vindas_exige_nome_da_equipe():
    at = _app()
    _sem_erros(at)
    assert _botao(at, "Avançar →").disabled
    at.text_input(key="w_equipe").input("Equipe Teste").run()
    assert not _botao(at, "Avançar →").disabled


def test_desafio_exige_tema_e_mostra_detalhes():
    at = _app()
    at.text_input(key="w_equipe").input("Equipe Teste").run()
    _botao(at, "Avançar →").click().run()
    _sem_erros(at)
    assert at.session_state.etapa == 1
    assert _botao(at, "Avançar →").disabled
    at.button(key="escolher_telco").click().run()
    assert at.session_state.tema_id == "telco"
    assert not _botao(at, "Avançar →").disabled
    assert any("Problemática" in m.value for m in at.markdown)


@pytest.mark.parametrize("tema_id", ["telco", "hotel", "noshow"])
def test_diagnostico_abre_sem_erros(tema_id):
    at = _ate_diagnostico(tema_id)
    _sem_erros(at)
    assert at.session_state.etapa == 2
    assert _botao(at, "Avançar →").disabled
    at.checkbox(key="w_diagnostico_lido").check().run()
    assert not _botao(at, "Avançar →").disabled
    at.selectbox[0].select("tenure" if tema_id == "telco" else at.selectbox[0].options[1]).run()
    _sem_erros(at)


def test_nome_da_equipe_e_checkbox_sobrevivem_a_navegacao():
    at = _ate_diagnostico("telco")
    at.checkbox(key="w_diagnostico_lido").check().run()
    _botao(at, "← Voltar").click().run()
    _botao(at, "← Voltar").click().run()
    assert at.text_input(key="w_equipe").value == "Equipe Teste"
    _botao(at, "Avançar →").click().run()
    _botao(at, "Avançar →").click().run()
    assert at.checkbox(key="w_diagnostico_lido").value is True


def test_trocar_de_desafio_com_trabalho_feito_pede_confirmacao():
    at = _ate_diagnostico("telco")
    at.session_state.passos = ["T01"]
    _botao(at, "← Voltar").click().run()
    at.button(key="escolher_hotel").click().run()
    assert at.session_state.tema_id == "telco"
    assert at.warning
    _botao(at, "Sim, trocar de desafio").click().run()
    assert at.session_state.tema_id == "hotel"
    assert at.session_state.passos == []


def test_etapas_futuras_navegaveis_sem_erros():
    at = _ate_diagnostico("telco")
    at.checkbox(key="w_diagnostico_lido").check().run()
    for etapa in range(3, 7):
        _botao(at, "Avançar →").click().run()
        _sem_erros(at)
        assert at.session_state.etapa == etapa
