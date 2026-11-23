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
CHAVES_DO_TEMA = ("passos", "resultados", "df_atual", "avisos", "diagnostico_lido", "justificativas", "spec", "spec_passo")


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
    "resultados": dict,
    "df_atual": None,
    "avisos": list,
    "diagnostico_lido": False,
    "justificativas": dict,
    "spec": dict,
    "spec_passo": 0,
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
        for chave in [k for k in st.session_state if str(k).startswith("w_") and k != "w_equipe"]:
            del st.session_state[chave]
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


def df_atual(tema: Theme) -> pd.DataFrame:
    """Base atual do pipeline (a original, sem cópia, enquanto nenhum bloco foi aplicado)."""
    atual = st.session_state.get("df_atual")
    return carregar_base(tema) if atual is None else atual


def avisar(tipo: str, texto: str, detalhe: str | None = None) -> None:
    """Guarda uma mensagem para mostrar no topo da etapa na próxima execução."""
    st.session_state.avisos.append((tipo, texto, detalhe))


def mostrar_avisos() -> None:
    for tipo, texto, detalhe in st.session_state.get("avisos", []):
        getattr(st, tipo)(texto)
        if detalhe:
            with st.expander("Detalhe técnico do erro"):
                st.code(detalhe, language="text")
    st.session_state.avisos = []


def fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def fmt_pct(x: float, casas: int = 1) -> str:
    return f"{x * 100:.{casas}f}%".replace(".", ",")


SELO = {
    "boa_pratica": ("Boa prática", "✅", "green"),
    "armadilha": ("Armadilha", "⚠️", "red"),
    "depende": ("Depende do objetivo", "🤔", "orange"),
}


def selo(categoria: str) -> None:
    rotulo, icone, cor = SELO[categoria]
    st.badge(rotulo, icon=icone, color=cor)


MAX_COLUNAS_TABELA = 50


def tabela_amostra(df: pd.DataFrame, linhas: int = 20) -> None:
    """Mostra as primeiras linhas; limita as colunas exibidas para bases muito largas."""
    if df.shape[1] > MAX_COLUNAS_TABELA:
        st.caption(
            f"A base tem {fmt_int(df.shape[1])} colunas; mostrando só as {MAX_COLUNAS_TABELA} primeiras "
            "para a tela não travar. O arquivo exportado terá todas."
        )
        df = df.iloc[:, :MAX_COLUNAS_TABELA]
    st.dataframe(df.head(linhas), width="stretch")


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
