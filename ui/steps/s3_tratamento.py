import streamlit as st

from ui.components import em_construcao, rodape


def render() -> None:
    st.header("3. Tratamento em blocos")
    em_construcao("M3")
    rodape()
