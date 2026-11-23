import pandas as pd
import plotly.express as px
import streamlit as st

from core import diagnostics as dg
from ui.components import campo_persistente, carregar_base, por_que_importa, rodape, salvar_campo, tema_atual

LEGENDA_TIPOS = (
    "Tipos: `object` = texto · `int64` = número inteiro · `float64` = número com casas decimais "
    "(uma coluna de inteiros com vazios também vira `float64`) · `bool` = verdadeiro/falso."
)


@st.cache_data(show_spinner="Analisando a base...")
def _diagnostico(tema_id: str, _df: pd.DataFrame, dicionario: dict, vazamento: tuple):
    """Cache por tema (o DataFrame original nunca muda, então não precisa ser comparado)."""
    df = _df
    return dg.metricas(df), dg.alertas_base(df, vazamento), dg.raio_x(df, dicionario, vazamento)


def _fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _grafico_alvo(df: pd.DataFrame, alvo: str):
    dist = dg.distribuicao(df[alvo])
    fig = px.bar(
        dist,
        x="valor",
        y="quantidade",
        text=dist["%"].map(lambda p: f"{p:.1f}%".replace(".", ",")),
        labels={"valor": alvo, "quantidade": "Quantidade de linhas"},
    )
    fig.update_layout(height=320, margin=dict(t=30, b=10), xaxis_type="category")
    return fig


def _grafico_coluna(df: pd.DataFrame, coluna: str):
    serie = df[coluna]
    if dg.eh_numerica(serie):
        fig = px.histogram(df, x=coluna, nbins=40, labels={coluna: coluna, "count": "Quantidade"})
        fig.update_layout(yaxis_title="Quantidade de linhas")
        legenda = "Histograma: mostra quantas linhas caem em cada faixa de valores."
    else:
        dist = dg.distribuicao(serie, top=15)
        fig = px.bar(
            dist.iloc[::-1],
            x="quantidade",
            y="valor",
            orientation="h",
            text=dist.iloc[::-1]["%"].map(lambda p: f"{p:.1f}%".replace(".", ",")),
            labels={"valor": coluna, "quantidade": "Quantidade de linhas"},
        )
        fig.update_layout(yaxis_type="category")
        legenda = "Barras: os 15 valores mais frequentes (o número na barra é a % da base)."
    fig.update_layout(height=380, margin=dict(t=30, b=10))
    return fig, legenda


def render() -> None:
    tema = tema_atual()
    if tema is None:
        st.warning("Escolha um desafio na etapa 1 antes do diagnóstico.")
        rodape(pode_avancar=False)
        return

    df = carregar_base(tema)
    met, alertas, tabela = _diagnostico(tema.id, df, tema.dicionario, tema.colunas_vazamento)

    st.header("2. Diagnóstico da base")
    st.caption(f"{tema.emoji} {tema.nome} — base original, antes de qualquer tratamento.")
    st.write(tema.descricao_base)

    # Métricas -----------------------------------------------------------------
    c = st.columns(5)
    c[0].metric("Linhas", _fmt(met["linhas"]), help="Cada linha é um registro (um cliente, uma reserva, uma consulta).")
    c[1].metric("Colunas", met["colunas"], help="Cada coluna é uma informação sobre o registro.")
    c[2].metric(
        "Células nulas",
        f"{met['pct_nulos']:.1f}%".replace(".", ","),
        help="Nulo = célula vazia, sem valor. A % considera todas as células da tabela.",
    )
    c[3].metric(
        "Linhas duplicadas",
        _fmt(met["duplicadas"]),
        help="Linhas exatamente iguais a outra linha, em todas as colunas.",
    )
    c[4].metric(
        "Numéricas × texto",
        f"{met['numericas']} × {met['texto']}",
        help="Quantas colunas o pandas leu como número e quantas leu como texto.",
    )

    # Alertas ------------------------------------------------------------------
    st.subheader(f"🚨 Alertas automáticos ({len(alertas)})")
    if alertas:
        with st.container(border=True):
            for a in alertas:
                alvo_txt = f"**`{a.coluna}`** — " if a.coluna else "**Base inteira** — "
                st.markdown(f"{a.icone} {alvo_txt}{a.mensagem}")
    else:
        st.success("Nenhum alerta automático nesta base.")
    st.caption("Alerta não é erro: é um sinal para investigar. Você decide o que fazer na etapa de tratamento.")

    # Raio-X -------------------------------------------------------------------
    st.subheader("🩻 Raio-X das colunas")
    st.dataframe(tabela, hide_index=True, width="stretch")
    st.caption(LEGENDA_TIPOS)

    # Gráficos -----------------------------------------------------------------
    st.subheader("📊 Gráficos")
    g1, g2 = st.columns(2)
    with g1:
        st.markdown(f"**Distribuição do alvo: `{tema.alvo}`**")
        st.caption("Alvo = a coluna com o resultado que queremos entender ou prever.")
        st.plotly_chart(_grafico_alvo(df, tema.alvo), width="stretch")
    with g2:
        colunas = list(df.columns)
        padrao = next((i for i, c in enumerate(colunas) if c != tema.alvo), 0)
        coluna = st.selectbox("Escolha uma coluna para ver a distribuição", colunas, index=padrao)
        fig, legenda = _grafico_coluna(df, coluna)
        st.plotly_chart(fig, width="stretch")
        st.caption(legenda)

    # Amostra ------------------------------------------------------------------
    st.subheader("🔎 Amostra: as 20 primeiras linhas")
    st.dataframe(df.head(20), width="stretch")

    por_que_importa(
        "Tratar sem diagnosticar é como receitar remédio sem examinar o paciente.  \n"
        "O diagnóstico mostra onde estão os vazios, os tipos errados e as colunas perigosas.  \n"
        "Anote os problemas: cada bloco da próxima etapa resolve (ou cria!) um deles.",
        titulo="💡 Por que diagnosticar antes de tratar?",
    )

    st.checkbox(
        "Li o diagnóstico e anotei os problemas que encontrei",
        key=campo_persistente("diagnostico_lido"),
        on_change=salvar_campo,
        args=("diagnostico_lido",),
    )
    salvar_campo("diagnostico_lido")

    rodape(
        pode_avancar=bool(st.session_state.diagnostico_lido),
        motivo="Marque a caixa acima para confirmar que leu o diagnóstico.",
    )
