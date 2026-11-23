import pandas as pd
import plotly.express as px
import streamlit as st

from core import diagnostics as dg
from ui.components import cabecalho, campo_persistente, carregar_base, dica, fmt_int, rodape, salvar_campo, tema_atual

MIN_ANOTACAO = 30


@st.cache_data(show_spinner="Analisando a base...")
def _resumo(tema_id: str, _df: pd.DataFrame, dicionario: dict):
    return dg.metricas(_df), dg.raio_x_v2(_df, dicionario)


def _grafico_distribuicao(df: pd.DataFrame, coluna: str):
    s = df[coluna]
    if dg.eh_numerica(s):
        fig = px.histogram(df, x=coluna, nbins=40)
        fig.update_layout(yaxis_title="Quantidade de linhas", bargap=0.05)
    else:
        dist = dg.distribuicao(s, top=15)
        fig = px.bar(dist.iloc[::-1], x="quantidade", y="valor", orientation="h",
                     text=dist.iloc[::-1]["%"].map(lambda p: f"{p:.1f}%".replace(".", ",")),
                     labels={"valor": coluna, "quantidade": "Quantidade de linhas"})
        fig.update_layout(yaxis_type="category")
    fig.update_layout(height=340, margin=dict(t=10, b=10, l=10, r=10))
    return fig


def _grafico_alvo(tabela: pd.DataFrame, coluna: str, rotulo: str):
    fig = px.bar(tabela, x=coluna, y="taxa", text=tabela["taxa"].map(lambda v: f"{v * 100:.1f}%".replace(".", ",")),
                 hover_data={"linhas": True}, labels={"taxa": rotulo.replace("`", ""), coluna: coluna})
    fig.update_layout(height=340, margin=dict(t=10, b=10, l=10, r=10), xaxis_type="category")
    fig.update_yaxes(tickformat=".0%")
    return fig


def render() -> None:
    tema = tema_atual()
    if tema is None:
        st.warning("Escolha uma missão antes do diagnóstico.")
        rodape(pode_avancar=False)
        return
    df = carregar_base(tema)
    met, tabela = _resumo(tema.id, df, tema.dicionario)

    cabecalho(
        "Diagnóstico da base",
        "A base veio direto do sistema, sem tratamento. Investigue antes de mexer: o que você descobrir aqui "
        "orienta a sua pipeline.",
    )

    c = st.columns(5)
    c[0].metric("Linhas", fmt_int(met["linhas"]), help="Cada linha é um registro.")
    c[1].metric("Colunas", met["colunas"], help="Cada coluna é uma informação sobre o registro.")
    c[2].metric("Células vazias", f"{met['pct_nulos']:.1f}%".replace(".", ","),
                help="Porcentagem de células sem valor, considerando a tabela inteira.")
    c[3].metric("Linhas repetidas", fmt_int(met["duplicadas"]), help="Linhas iguais a outra em todas as colunas.")
    c[4].metric("Numéricas / texto", f"{met['numericas']} / {met['texto']}",
                help="Quantas colunas o computador leu como número e quantas como texto.")

    with st.container(border=True):
        st.markdown("**Roteiro de investigação**")
        st.caption("Use o Raio-X e o explorador abaixo para responder. Anote o que encontrar no fim da página.")
        r1, r2 = st.columns(2)
        metade = (len(dg.ROTEIRO) + 1) // 2
        for col, perguntas, inicio in ((r1, dg.ROTEIRO[:metade], 1), (r2, dg.ROTEIRO[metade:], metade + 1)):
            col.markdown("\n".join(f"{i}. {q}" for i, q in enumerate(perguntas, start=inicio)))

    st.subheader("Raio-X das colunas", anchor=False)
    st.dataframe(tabela, hide_index=True, width="stretch", height=420,
                 column_config={"Significado": st.column_config.TextColumn(width="large"),
                                "% vazios": st.column_config.NumberColumn(format="%.1f")})
    st.caption("Significado = documentação da base publicada no Kaggle. Tipo = como o computador leu a coluna.")

    st.subheader("Explorar uma coluna", anchor=False)
    colunas = list(df.columns)
    padrao = next((i for i, c in enumerate(colunas) if df[c].nunique() < len(df) * 0.5), 0)
    coluna = st.selectbox("Coluna", colunas, index=padrao, key="diag_coluna")
    serie = df[coluna]
    a, b = st.columns([1, 2], gap="large")
    with a, st.container(border=True):
        st.markdown(f"**`{coluna}`**")
        if tema.dicionario.get(coluna):
            st.caption(tema.dicionario[coluna])
        for k, v in dg.estatisticas(serie).items():
            st.markdown(f"<span class='muted'>{k}</span> &nbsp; **{v}**", unsafe_allow_html=True)
    with b:
        aba1, aba2, aba3 = st.tabs(["Distribuição", "Relação com o alvo", "Valores mais frequentes"])
        with aba1:
            st.plotly_chart(_grafico_distribuicao(df, coluna), width="stretch", key="g_dist")
        with aba2:
            rel = dg.relacao_com_alvo(df, coluna, tema.alvo)
            if rel is None:
                st.caption(f"Escolha uma coluna diferente do alvo (`{tema.alvo}`) para ver a relação.")
            else:
                tab, rotulo = rel
                st.caption(f"Para cada valor (ou faixa) de `{coluna}`: {rotulo}. Passe o mouse para ver quantas linhas.")
                st.plotly_chart(_grafico_alvo(tab, coluna, rotulo), width="stretch", key="g_alvo")
        with aba3:
            st.dataframe(dg.distribuicao(serie, top=20), hide_index=True, width="stretch", height=340)

    st.subheader("Amostra da base", anchor=False)
    st.dataframe(df.head(20), width="stretch")

    st.subheader("Suas anotações", anchor=False)
    st.text_area(
        "O que você encontrou? Que problemas ou cuidados você viu nos dados?",
        key=campo_persistente("notas_diag"),
        on_change=salvar_campo,
        args=("notas_diag",),
        height=150,
        placeholder="Escreva uma observação por linha. Ex.: a coluna X tem vazios; a coluna Y parece número mas é texto...",
        help="Suas anotações ficam visíveis na pipeline e na SPEC. Clique fora do campo para salvar.",
    )
    salvar_campo("notas_diag")
    dica(
        "Tratar sem diagnosticar é como receitar remédio sem examinar o paciente. Cada decisão da pipeline "
        "deveria responder a algo que você anotou aqui.",
        titulo="Por que diagnosticar antes de tratar?",
    )
    faltam = MIN_ANOTACAO - len((st.session_state.notas_diag or "").strip())
    rodape(pode_avancar=faltam <= 0,
           motivo=f"Escreva suas anotações para avançar (faltam {max(faltam, 0)} caracteres).")
