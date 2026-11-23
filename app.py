"""Da Spec ao App — ponto de entrada. Rode com:  streamlit run app.py"""

import streamlit as st

from ui.components import aplicar_estilo, barra_lateral, iniciar_estado
from ui.steps import s0_inicio, s1_missao, s2_diagnostico, s3_pipeline, s4_revisao, s5_spec, s6_exportar, s7_gabarito

ETAPAS = [s0_inicio, s1_missao, s2_diagnostico, s3_pipeline, s4_revisao, s5_spec, s6_exportar, s7_gabarito]

st.set_page_config(page_title="Da Spec ao App", page_icon=":material/schema:", layout="wide",
                   initial_sidebar_state="expanded")

aplicar_estilo()
iniciar_estado()
barra_lateral()

try:
    ETAPAS[st.session_state.etapa].render()
except Exception as erro:  # nenhuma exceção técnica deve aparecer crua para o participante
    st.error(
        "Algo deu errado nesta tela. Tente voltar para a etapa anterior. "
        "Se o problema continuar, chame a organização.",
        icon=":material/error:",
    )
    with st.expander("Detalhes técnicos (para a organização)"):
        st.code(f"{type(erro).__name__}: {erro}", language="text")
