"""Componentes de interface e helpers de estado compartilhados pelas etapas."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core.models import Theme
from core.themes import REGISTRY

RAIZ = Path(__file__).resolve().parent.parent

ETAPAS = ["Boas-vindas", "Desafio", "Diagnóstico", "Tratamento", "Checklist", "Spec", "Exportar"]

# Chaves de st.session_state que dependem do tema escolhido. Trocar de tema zera todas.
CHAVES_DO_TEMA = ("passos", "df_atual", "diagnostico_lido", "justificativas", "spec")


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------


# Valores iniciais do estado. Listas/dicionários vêm de fábricas para não serem compartilhados.
VALORES_INICIAIS = {
    "etapa": 0,
    "equipe": "",
    "tema_id": None,
    "tema_pendente": None,
    "passos": list,
    "df_atual": None,
    "diagnostico_lido": False,
    "justificativas": dict,
    "spec": dict,
}


def iniciar_estado() -> None:
    for chave, valor in VALORES_INICIAIS.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor() if callable(valor) else valor


def ir_para(etapa: int) -> None:
    st.session_state.etapa = max(0, min(etapa, len(ETAPAS) - 1))


def tema_atual() -> Theme | None:
    tema_id = st.session_state.get("tema_id")
    return REGISTRY.get(tema_id) if tema_id else None


def tem_trabalho_feito() -> bool:
    return bool(st.session_state.get("passos")) or bool(st.session_state.get("spec"))


def escolher_tema(tema_id: str) -> None:
    """Define o tema e zera tudo o que dependia do tema anterior."""
    if st.session_state.get("tema_id") != tema_id:
        for chave in CHAVES_DO_TEMA:
            st.session_state[chave] = VALORES_INICIAIS[chave]() if callable(VALORES_INICIAIS[chave]) else VALORES_INICIAIS[chave]
            st.session_state.pop(f"w_{chave}", None)
    st.session_state.tema_id = tema_id
    st.session_state.tema_pendente = None


@st.cache_resource(show_spinner="Carregando a base...")
def _ler_csv(caminho: str) -> pd.DataFrame:
    return pd.read_csv(RAIZ / caminho)


def carregar_base(tema: Theme) -> pd.DataFrame:
    """Base original do tema, carregada uma vez e compartilhada entre as sessões.

    NUNCA altere este DataFrame: o executor sempre trabalha sobre `df.copy()`.
    (cache_resource evita uma cópia por sessão; ver DECISOES.md.)
    """
    return _ler_csv(tema.arquivo)


def campo_persistente(chave: str) -> str:
    """Chave de widget que sobrevive à troca de etapa.

    O Streamlit apaga o estado de widgets que deixam de ser desenhados. Guardamos o valor
    em `chave` e reabastecemos o widget (`w_<chave>`) sempre que ele volta à tela.
    """
    chave_widget = f"w_{chave}"
    if chave_widget not in st.session_state:
        st.session_state[chave_widget] = st.session_state.get(chave)
    return chave_widget


def salvar_campo(chave: str) -> None:
    st.session_state[chave] = st.session_state[f"w_{chave}"]


# ---------------------------------------------------------------------------
# Visual
# ---------------------------------------------------------------------------


def barra_progresso() -> None:
    etapa = st.session_state.etapa
    st.progress(etapa / (len(ETAPAS) - 1))
    partes = []
    for i, nome in enumerate(ETAPAS):
        rotulo = f"{i} {nome}"
        if i == etapa:
            partes.append(f"**:blue[{rotulo}]**")
        elif i < etapa:
            partes.append(f"✓ {rotulo}")
        else:
            partes.append(f":gray[{rotulo}]")
    st.markdown(" → ".join(partes))


def por_que_importa(texto: str, titulo: str = "💡 Por que isso importa?") -> None:
    st.info(f"**{titulo}**\n\n{texto}")


def rodape(pode_avancar: bool = True, motivo: str = "") -> None:
    """Botões Voltar/Avançar no fim da etapa."""
    st.divider()
    etapa = st.session_state.etapa
    esquerda, meio, direita = st.columns([1, 3, 1])
    with esquerda:
        if etapa > 0:
            st.button("← Voltar", on_click=ir_para, args=(etapa - 1,), width="stretch")
    with meio:
        if not pode_avancar and motivo:
            st.caption(f"🔒 {motivo}")
    with direita:
        if etapa < len(ETAPAS) - 1:
            st.button(
                "Avançar →",
                type="primary",
                disabled=not pode_avancar,
                on_click=ir_para,
                args=(etapa + 1,),
                width="stretch",
            )


def em_construcao(marco: str) -> None:
    st.info(f"🚧 Esta etapa será construída no marco **{marco}**. Por enquanto, você pode navegar entre as etapas.")
