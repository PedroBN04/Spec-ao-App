import streamlit as st

from core import executor as ex
from core import revisao as rv
from ui.components import cabecalho, campo_persistente, carregar_base, df_atual, ir_para, rodape, salvar_campo, tabela_amostra, tema_atual


def render() -> None:
    tema = tema_atual()
    if tema is None:
        st.warning("Escolha uma missão antes da revisão.")
        rodape(pode_avancar=False)
        return
    original, df = carregar_base(tema), df_atual(tema)

    cabecalho(
        "Revise o resultado",
        "Compare a base original com a base tratada. Aqui não há nota nem certo e errado: é o momento de "
        "conferir se o resultado é o que você queria e, se não for, voltar ao fluxo.",
    )

    st.subheader("Antes × depois", anchor=False)
    indicadores = rv.indicadores(tema, original, df)
    for linha in (indicadores[:3], indicadores[3:]):
        cols = st.columns(3)
        for col, ind in zip(cols, linha):
            with col, st.container(border=True, height="stretch"):
                st.caption(ind.titulo)
                st.markdown(f"**{ind.antes}** &nbsp;→&nbsp; **{ind.depois}**")
                if ind.detalhe:
                    st.caption(ind.detalhe)

    esquerda, direita = st.columns([3, 2], gap="large")
    with esquerda:
        st.subheader("Colunas", anchor=False)
        st.dataframe(rv.comparativo_colunas(original, df), hide_index=True, width="stretch", height=380)
    with direita:
        st.subheader("Seu fluxo", anchor=False)
        with st.container(border=True):
            for n, passo in enumerate(st.session_state.passos, start=1):
                bloco = st.session_state.blocos[ex.uid(passo)]
                nota = passo.get("nota", "") if isinstance(passo, dict) else ""
                st.markdown(f"**{n}.** {bloco.titulo}")
                st.caption(f"Motivo: {nota}" if nota else "Sem motivo registrado (você pode escrever no fluxo).")
        st.button("Voltar ao fluxo para ajustar", icon=":material/account_tree:", on_click=ir_para, args=(3,),
                  width="stretch")

    st.subheader("Amostra da base tratada", anchor=False)
    tabela_amostra(df, altura=300)

    st.subheader("Suas observações", anchor=False)
    st.text_area(
        "Algo que você decidiu manter de propósito, ou que o agente precisa saber sobre o tratamento? (opcional)",
        key=campo_persistente("notas_revisao"),
        on_change=salvar_campo,
        args=("notas_revisao",),
        height=110,
        placeholder="Uma observação por linha. Ex.: mantive os clientes novos mesmo com cobrança zero.",
        help="Vai para a seção 3.2 da SPEC.",
    )
    salvar_campo("notas_revisao")
    st.checkbox("Revisei o resultado e quero seguir para a SPEC", key=campo_persistente("revisao_ok"),
                on_change=salvar_campo, args=("revisao_ok",))
    salvar_campo("revisao_ok")
    rodape(pode_avancar=bool(st.session_state.revisao_ok), motivo="Marque que revisou o resultado para avançar.")
