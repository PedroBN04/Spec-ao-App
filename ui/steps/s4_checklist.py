import streamlit as st

from ui.components import em_construcao, rodape


def render() -> None:
    st.header("4. Checklist de qualidade")
    em_construcao("M4")
    rodape()
