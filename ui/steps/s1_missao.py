import streamlit as st

from core.themes import REGISTRY
from ui.components import cabecalho, carregar_base, escolher_tema, fmt_int, rodape, tem_trabalho_feito, tema_atual


def _pedir_tema(tema_id: str) -> None:
    atual = st.session_state.tema_id
    if atual and atual != tema_id and tem_trabalho_feito():
        st.session_state.tema_pendente = tema_id
    else:
        escolher_tema(tema_id)


def _cancelar_troca() -> None:
    st.session_state.tema_pendente = None


def render() -> None:
    cabecalho(
        "Escolha sua missão",
        "Cada missão é uma solicitação real de uma área cliente, com uma base de dados exportada do sistema.",
    )

    colunas = st.columns(len(REGISTRY))
    for coluna, tema in zip(colunas, REGISTRY.values()):
        df = carregar_base(tema)
        escolhido = st.session_state.tema_id == tema.id
        with coluna, st.container(border=True, height="stretch"):
            st.html(f"<span class='pill'>{tema.dominio}</span>")
            st.markdown(f"#### {tema.area_cliente}")
            st.write(tema.problematica)
            st.caption(f"Base: {fmt_int(len(df))} linhas × {df.shape[1]} colunas")
            st.button(
                "Missão aceita" if escolhido else "Aceitar esta missão",
                key=f"escolher_{tema.id}",
                icon=":material/check:" if escolhido else None,
                type="primary" if not escolhido else "secondary",
                disabled=escolhido,
                on_click=_pedir_tema,
                args=(tema.id,),
                width="stretch",
            )

    pendente = st.session_state.tema_pendente
    if pendente:
        st.warning(
            f"Você já começou a missão da **{tema_atual().area_cliente}**. Trocar para "
            f"**{REGISTRY[pendente].area_cliente}** apaga suas anotações, a pipeline e a SPEC. Deseja continuar?",
            icon=":material/warning:",
        )
        c1, c2, _ = st.columns([1, 1, 3])
        c1.button("Sim, trocar de missão", type="primary", on_click=escolher_tema, args=(pendente,))
        c2.button("Cancelar", on_click=_cancelar_troca)

    tema = tema_atual()
    if tema:
        st.subheader("A solicitação", anchor=False)
        with st.container(border=True):
            st.markdown(f"**De:** {tema.solicitante} · {tema.area_cliente}  \n**Para:** Time de dados")
            st.html(f"<div class='missao'>{tema.missao}</div>")
            a, b = st.columns(2)
            with a:
                st.markdown("**O que a área pediu**")
                st.markdown("\n".join(f"- {item}" for item in tema.proposta_inicial))
            with b:
                st.markdown("**Ideias que a área também gostaria de ver**")
                st.markdown("\n".join(f"- {item}" for item in tema.aprofundamentos))
        st.info(
            "**Você não precisa fazer exatamente o que foi pedido.** O pedido é o ponto de partida: você pode "
            "priorizar o que considerar mais importante, deixar algo de fora com uma boa justificativa ou ir "
            "além com análises que a área nem imaginou. O que importa é que suas decisões façam sentido para o "
            "problema e estejam explicadas na SPEC.",
            icon=":material/explore:",
        )
        with st.expander("Sobre a base de dados", icon=":material/dataset:"):
            st.write(tema.descricao_base)
            st.markdown(f"**Fonte:** [{tema.fonte}]({tema.fonte})  \n**Licença:** {tema.licenca}")
            st.caption("As bases são usadas apenas para fins educativos, com atribuição às fontes.")

    rodape(pode_avancar=tema is not None and not pendente, motivo="Aceite uma missão para avançar.")
