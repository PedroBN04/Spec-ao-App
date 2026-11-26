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
    "Base de dados": "A tabela com os dados do desafio. Cada linha é um registro (um cliente, uma reserva, uma "
    "consulta) e cada coluna é uma informação sobre ele.",
    "Alvo": "A coluna com o resultado que a área cliente quer entender. Ex.: se o cliente cancelou.",
    "Nulo / vazio": "Célula sem valor. Pode ser erro, informação que não existe ou algo com significado próprio. "
    "Cuidado com \"vazios disfarçados\": células que têm só espaços em branco.",
    "Tipo": "Como o computador lê a coluna: texto, número inteiro, número decimal, data... Um número lido como "
    "texto não soma nem faz média.",
    "Pipeline": "A sequência de passos que transforma a base bruta na base pronta, como uma linha de montagem ou "
    "uma receita: cada passo recebe o resultado do anterior.",
    "Bloco / nó": "Um passo da pipeline. Pode ser um bloco pronto do catálogo ou um bloco que você configura.",
    "pandas": "Biblioteca da linguagem Python para trabalhar com tabelas. O código de cada bloco usa o pandas.",
    "Painel (dashboard)": "Aplicação com números, gráficos e filtros que ajuda alguém a tomar decisões.",
    "SPEC": "Especificação: o documento que diz o que construir, para quem, com quais regras e como conferir.",
    "Agente de código": "Assistente de IA que escreve programas a partir de instruções (ex.: Claude Code, Cursor, "
    "Copilot, ChatGPT).",
    "CSV": "Tabela simples salva como texto, usada por programas e pela IA. Para abrir direto no Excel, use a "
    "planilha .xlsx do kit da Etapa 6.",
    "Vazamento de dados": "Dar \"a cola da prova\" para o cálculo: usar uma informação que só existe depois do "
    "resultado acontecer.",
    "Cancelamento de clientes (churn)": "Quando o cliente encerra o contrato. A taxa de churn é a porcentagem de "
    "clientes que cancelaram.",
    "Antecedência da reserva (lead time)": "Quantos dias antes da chegada a reserva foi feita.",
    "Diária média (ADR)": "Quanto o hotel recebe, em média, por noite de uma reserva.",
    "Venda acima da capacidade (overbooking)": "Vender mais quartos do que existem, contando com os cancelamentos.",
    "Não comparecimento (no-show)": "Quando a pessoa tem horário marcado e não aparece.",
    "Valores fora da curva (outliers)": "Valores muito diferentes dos demais. Podem ser erros ou casos reais "
    "importantes. O z-score mede o quanto um valor se afasta da média.",
    "Codificação 0/1 (one-hot)": "Transformar uma coluna de texto em várias colunas de Sim/Não (0 e 1), uma para "
    "cada resposta possível.",
    "Kaggle": "Site gratuito com bases de dados reais publicadas para estudo e competições.",
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
    st.dataframe(df.head(linhas), width="stretch", height=altura or "auto", hide_index=True)


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
.block-container{padding-top:4rem;padding-bottom:6rem;max-width:1240px}
[data-testid='stFileUploaderDropzoneInstructions']{display:none}
[data-testid='stFileUploaderDropzone'] button{font-size:0}
[data-testid='stFileUploaderDropzone'] button::after{content:'Escolher arquivo';font-size:.875rem}
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
        _salvar_progresso()
        with st.expander("Glossário", icon=":material/menu_book:"):
            for termo, definicao in GLOSSARIO.items():
                st.markdown(f"**{termo}** — {definicao}")
        st.caption("O app não guarda nada no servidor. Salve um rascunho de vez em quando: se a página recarregar "
                   "ou a internet cair, é só retomar.")


def _restaurar() -> None:
    from core import executor as ex
    from core import rascunho

    arquivo = st.session_state.get("upload_rascunho")
    if arquivo is None:
        return
    try:
        dados = rascunho.ler(arquivo.getvalue())
    except rascunho.RascunhoInvalido as erro:
        st.session_state.aviso_rascunho = ("error", str(erro))
        return
    for chave in [k for k in st.session_state if str(k).startswith(("w_", "nv_", "nota_", "spec_nav_"))]:
        del st.session_state[chave]
    for chave in CHAVES_DO_TEMA:
        st.session_state[chave] = _inicial(chave)
    for chave, valor in dados.items():
        if chave != "passos":
            st.session_state[chave] = valor
    st.session_state.tema_pendente = None
    if dados["tema_id"]:
        tema = REGISTRY[dados["tema_id"]]
        pipe = ex.reexecutar(carregar_base(tema), tema, dados["passos"])
        st.session_state.passos = pipe.passos
        st.session_state.resultados = pipe.resultados
        st.session_state.blocos = pipe.blocos
        st.session_state.df_atual = pipe.df if pipe.passos else None
        st.session_state.prox_uid = max(dados["prox_uid"], len(dados["passos"]) + 1)
    st.session_state.aviso_rascunho = ("success", "Rascunho retomado. Você está na última etapa em que parou.")


def _salvar_progresso() -> None:
    from core import exporter, rascunho

    with st.expander("Salvar ou retomar progresso", icon=":material/save:"):
        estado = {c: st.session_state.get(c) for c in rascunho.CAMPOS}
        st.download_button(
            "Salvar rascunho (.json)",
            data=rascunho.gerar(estado),
            file_name=f"rascunho_{exporter.slug_equipe(st.session_state.equipe or 'equipe')}.json",
            mime="application/json",
            icon=":material/download:",
            width="stretch",
            on_click="ignore",
        )
        st.file_uploader("Retomar rascunho (.json)", type=["json"], key="upload_rascunho", on_change=_restaurar)
        aviso = st.session_state.pop("aviso_rascunho", None)
        if aviso:
            getattr(st, aviso[0])(aviso[1])


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
