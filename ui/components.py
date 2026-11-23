"""Componentes de interface, estilo e estado compartilhados pelas etapas (v2)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core.models import Theme
from core.themes import REGISTRY

RAIZ = Path(__file__).resolve().parent.parent

# (título curto, subtítulo). A etapa 7 (gabarito) só é liberada depois da exportação.
ETAPAS = [
    ("Início", "Entenda a jornada"),
    ("Missão", "Escolha a solicitação"),
    ("Diagnóstico", "Investigue a base"),
    ("Pipeline", "Monte o tratamento"),
    ("Revisão", "Confira o resultado"),
    ("SPEC", "Escreva a especificação"),
    ("Exportar", "Baixe os arquivos"),
    ("Gabarito", "Revisão com o facilitador"),
]
ULTIMA_ETAPA_JORNADA = 6
ETAPA_GABARITO = 7

GLOSSARIO = {
    "Base de dados": "A tabela com os dados do desafio: cada linha é um registro (cliente, reserva, consulta) "
    "e cada coluna é uma informação sobre ele.",
    "Alvo": "A coluna com o resultado que a área cliente quer entender (ex.: se o cliente cancelou).",
    "Nulo / vazio": "Célula sem valor. Pode ser erro, informação que não existe ou algo com significado próprio.",
    "Tipo": "Como o computador entende a coluna: texto, número inteiro, número decimal, data...",
    "Pipeline": "A sequência de passos que transforma a base original na base tratada. Cada passo recebe a "
    "tabela do passo anterior, faz uma coisa e entrega para o próximo.",
    "Bloco / nó": "Um passo da pipeline. Pode ser um bloco pronto do catálogo ou um bloco que você configura.",
    "pandas": "Biblioteca de Python para trabalhar com tabelas. O código de cada bloco é escrito com ela.",
    "Painel (dashboard)": "Aplicação com números, gráficos e filtros que ajuda alguém a tomar decisões.",
    "SPEC": "Especificação: o documento que descreve o que construir, para quem, com quais regras e como "
    "conferir se ficou certo.",
    "Agente de código": "Assistente de IA que escreve programas a partir de instruções (ex.: Claude Code).",
    "CSV": "Planilha salva como texto, com valores separados por vírgula. Abre no Excel.",
    "Vazamento de dados": "Usar para prever um resultado uma informação que só existe depois desse resultado.",
}

# Chaves de st.session_state que dependem do tema escolhido. Trocar de tema zera todas.
VALORES_INICIAIS = {
    "etapa": 0,
    "max_etapa": 0,
    "equipe": "",
    "tema_id": None,
    "tema_pendente": None,
    "passos": list,
    "resultados": dict,
    "blocos": dict,
    "df_atual": None,
    "avisos": list,
    "notas_diag": "",
    "notas_revisao": "",
    "revisao_ok": False,
    "spec": dict,
    "spec_passo": 0,
    "prox_uid": 1,
    "exportou": False,
}
CHAVES_DO_TEMA = (
    "passos", "resultados", "blocos", "df_atual", "avisos", "notas_diag", "notas_revisao", "revisao_ok",
    "spec", "spec_passo", "prox_uid", "exportou",
)


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------


def _inicial(chave: str):
    v = VALORES_INICIAIS[chave]
    return v() if callable(v) else v


def iniciar_estado() -> None:
    for chave in VALORES_INICIAIS:
        if chave not in st.session_state:
            st.session_state[chave] = _inicial(chave)


def ir_para(etapa: int) -> None:
    limite = ETAPA_GABARITO if st.session_state.get("exportou") else ULTIMA_ETAPA_JORNADA
    st.session_state.etapa = max(0, min(etapa, limite))
    st.session_state.max_etapa = max(st.session_state.max_etapa, st.session_state.etapa)


def tema_atual() -> Theme | None:
    tema_id = st.session_state.get("tema_id")
    return REGISTRY.get(tema_id) if tema_id else None


def tem_trabalho_feito() -> bool:
    return bool(st.session_state.get("passos")) or bool((st.session_state.get("notas_diag") or "").strip())


def escolher_tema(tema_id: str) -> None:
    """Define o tema e zera tudo o que dependia do tema anterior."""
    if st.session_state.get("tema_id") != tema_id:
        for chave in CHAVES_DO_TEMA:
            st.session_state[chave] = _inicial(chave)
        for chave in [k for k in st.session_state if str(k).startswith(("w_", "nv_")) and k != "w_equipe"]:
            del st.session_state[chave]
        st.session_state.max_etapa = min(st.session_state.max_etapa, 1)
    st.session_state.tema_id = tema_id
    st.session_state.tema_pendente = None


@st.cache_resource(show_spinner="Carregando a base...")
def _ler_csv(caminho: str) -> pd.DataFrame:
    return pd.read_csv(RAIZ / caminho)


def carregar_base(tema: Theme) -> pd.DataFrame:
    """Base original do tema, carregada uma vez e compartilhada entre as sessões.

    NUNCA altere este DataFrame: o executor sempre trabalha sobre `df.copy()`.
    """
    return _ler_csv(tema.arquivo)


def df_atual(tema: Theme) -> pd.DataFrame:
    """Base no fim do fluxo (a original, sem cópia, enquanto não há passos)."""
    atual = st.session_state.get("df_atual")
    return carregar_base(tema) if atual is None else atual


def avisar(tipo: str, texto: str, detalhe: str | None = None) -> None:
    st.session_state.avisos.append((tipo, texto, detalhe))


def mostrar_avisos() -> None:
    icones = {"info": ":material/info:", "warning": ":material/warning:", "error": ":material/error:",
              "success": ":material/check_circle:"}
    for tipo, texto, detalhe in st.session_state.get("avisos", []):
        getattr(st, tipo)(texto, icon=icones.get(tipo))
        if detalhe:
            with st.expander("Detalhe técnico"):
                st.code(detalhe, language="text")
    st.session_state.avisos = []


def fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def fmt_pct(x: float, casas: int = 1) -> str:
    return f"{x * 100:.{casas}f}%".replace(".", ",")


MAX_COLUNAS_TABELA = 50


def tabela_amostra(df: pd.DataFrame, linhas: int = 20, altura: int | None = None) -> None:
    """Primeiras linhas; limita as colunas exibidas para bases muito largas."""
    if df.shape[1] > MAX_COLUNAS_TABELA:
        st.caption(
            f"A base tem {fmt_int(df.shape[1])} colunas; mostrando só as {MAX_COLUNAS_TABELA} primeiras "
            "para a tela não travar. O arquivo exportado terá todas."
        )
        df = df.iloc[:, :MAX_COLUNAS_TABELA]
    st.dataframe(df.head(linhas), width="stretch", height=altura or "auto")


def campo_persistente(chave: str) -> str:
    """Chave de widget (`w_<chave>`) que sobrevive à troca de etapa (o valor fica em `chave`)."""
    chave_widget = f"w_{chave}"
    if chave_widget not in st.session_state:
        st.session_state[chave_widget] = st.session_state.get(chave)
    return chave_widget


def salvar_campo(chave: str) -> None:
    st.session_state[chave] = st.session_state[f"w_{chave}"]


# ---------------------------------------------------------------------------
# Visual
# ---------------------------------------------------------------------------

CSS = """
<style>
[data-testid='InputInstructions']{display:none}
.block-container{padding-top:4rem;max-width:1240px}
[data-testid='stSidebar'] .stButton button{justify-content:flex-start !important;text-align:left}
[data-testid='stSidebar'] .stButton button > div{justify-content:flex-start !important;width:100%}
.st-key-previa h1{font-size:1.45rem}.st-key-previa h2{font-size:1.15rem}.st-key-previa h3{font-size:1rem}
.eyebrow{font-size:.78rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:#4338CA;margin-bottom:.1rem}
.subtitulo{color:#5B6275;font-size:1rem;margin-top:-.4rem;margin-bottom:1.2rem}
.pill{display:inline-block;font-size:.75rem;font-weight:600;padding:.12rem .55rem;border-radius:999px;
      background:#EEF0FB;color:#4338CA;margin-right:.35rem}
.pill.cinza{background:#F1F2F6;color:#5B6275}
.no-extremo{border:1px dashed #C9CEDB;border-radius:.6rem;padding:.6rem .9rem;background:#FAFBFD;
            color:#3A4154;font-size:.92rem}
.conector{width:2px;height:18px;background:#C9CEDB;margin:2px 0 2px 26px}
.missao{border-left:4px solid #4338CA;background:#F7F7FD;padding:1rem 1.2rem;border-radius:.5rem;
        font-size:1.02rem;line-height:1.55}
.muted{color:#5B6275;font-size:.9rem}
</style>
"""


def aplicar_estilo() -> None:
    st.html(CSS)


def cabecalho(titulo: str, subtitulo: str = "") -> None:
    etapa = st.session_state.etapa
    if etapa == ETAPA_GABARITO:
        rotulo = "Depois da exportação"
    else:
        rotulo = f"Etapa {etapa} de {ULTIMA_ETAPA_JORNADA}" if etapa else "Boas-vindas"
    st.html(f"<div class='eyebrow'>{rotulo}</div>")
    st.title(titulo, anchor=False)
    if subtitulo:
        st.html(f"<div class='subtitulo'>{subtitulo}</div>")


def barra_lateral() -> None:
    with st.sidebar:
        st.markdown("### Da Spec ao App")
        st.caption("Laboratório guiado de dados e especificação")
        tema = tema_atual()
        if st.session_state.equipe or tema:
            with st.container(border=True):
                if st.session_state.equipe:
                    st.markdown(f"**Equipe:** {st.session_state.equipe}")
                if tema:
                    st.markdown(f"**Missão:** {tema.area_cliente}")
        st.markdown("**Jornada**")
        limite = st.session_state.max_etapa
        ultima = ETAPA_GABARITO if st.session_state.get("exportou") else ULTIMA_ETAPA_JORNADA
        for i, (nome, _) in enumerate(ETAPAS[: ultima + 1]):
            atual = i == st.session_state.etapa
            if atual:
                icone = ":material/radio_button_checked:"
            elif i <= limite:
                icone = ":material/check_circle:"
            else:
                icone = ":material/radio_button_unchecked:"
            st.button(
                f"{i}. {nome}" if i <= ULTIMA_ETAPA_JORNADA else nome,
                key=f"nav_{i}",
                icon=icone,
                type="primary" if atual else "tertiary",
                disabled=i > limite,
                on_click=ir_para,
                args=(i,),
                width="stretch",
            )
        st.divider()
        with st.expander("Glossário", icon=":material/menu_book:"):
            for termo, definicao in GLOSSARIO.items():
                st.markdown(f"**{termo}** — {definicao}")
        st.caption("Não recarregue a página antes de baixar os arquivos: o app não guarda nada no servidor.")


def dica(texto: str, titulo: str = "Por que isso importa?") -> None:
    st.info(f"**{titulo}**  \n{texto}", icon=":material/lightbulb:")


def rodape(pode_avancar: bool = True, motivo: str = "", rotulo_avancar: str = "Avançar") -> None:
    st.divider()
    etapa = st.session_state.etapa
    esquerda, meio, direita = st.columns([1, 3, 1], vertical_alignment="center")
    with esquerda:
        if etapa > 0:
            st.button("Voltar", icon=":material/arrow_back:", on_click=ir_para, args=(etapa - 1,), width="stretch")
    with meio:
        if not pode_avancar and motivo:
            st.caption(f":material/lock: {motivo}")
    with direita:
        if etapa < ULTIMA_ETAPA_JORNADA:
            st.button(
                rotulo_avancar,
                icon=":material/arrow_forward:",
                icon_position="right",
                type="primary",
                disabled=not pode_avancar,
                on_click=ir_para,
                args=(etapa + 1,),
                width="stretch",
            )
