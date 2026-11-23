"""Da Spec ao App — ponto de entrada. Rode com:  streamlit run app.py"""

import streamlit as st

from ui.components import barra_progresso, iniciar_estado
from ui.steps import (
    s0_boas_vindas,
    s1_desafio,
    s2_diagnostico,
    s3_tratamento,
    s4_checklist,
    s5_spec,
    s6_exportar,
)

ETAPAS = [s0_boas_vindas, s1_desafio, s2_diagnostico, s3_tratamento, s4_checklist, s5_spec, s6_exportar]

st.set_page_config(page_title="Da Spec ao App", page_icon="🧪", layout="wide")

iniciar_estado()
barra_progresso()

try:
    ETAPAS[st.session_state.etapa].render()
except Exception as erro:  # nenhuma exceção técnica deve aparecer crua para o participante
    st.error(
        "Ops! Algo deu errado nesta tela. Tente voltar para a etapa anterior. "
        "Se o problema continuar, chame a organização."
    )
    with st.expander("Detalhes técnicos (para a organização)"):
        st.exception(erro)
