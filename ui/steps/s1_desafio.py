import streamlit as st

from core.themes import REGISTRY
from ui.components import carregar_base, escolher_tema, rodape, tem_trabalho_feito, tema_atual


def _pedir_tema(tema_id: str) -> None:
    """Escolhe direto ou, se já houver trabalho feito com outro tema, pede confirmação."""
    atual = st.session_state.tema_id
    if atual and atual != tema_id and tem_trabalho_feito():
        st.session_state.tema_pendente = tema_id
    else:
        escolher_tema(tema_id)


def _cancelar_troca() -> None:
    st.session_state.tema_pendente = None


def render() -> None:
    st.header("1. Escolha o seu desafio")
    st.caption("Cada desafio tem um tema, uma base de dados real e um problema para resolver.")

    colunas = st.columns(len(REGISTRY))
    for coluna, tema in zip(colunas, REGISTRY.values()):
        df = carregar_base(tema)
        escolhido = st.session_state.tema_id == tema.id
        with coluna, st.container(border=True):
            st.markdown(f"## {tema.emoji}")
            st.markdown(f"### {tema.nome}")
            st.caption(tema.dominio)
            st.write(tema.problematica)
            st.markdown(f"**Base:** {len(df):,} linhas × {df.shape[1]} colunas".replace(",", "."))
            st.button(
                "✓ Escolhido" if escolhido else "Escolher este desafio",
                key=f"escolher_{tema.id}",
                type="primary" if escolhido else "secondary",
                disabled=escolhido,
                on_click=_pedir_tema,
                args=(tema.id,),
                width="stretch",
            )

    pendente = st.session_state.tema_pendente
    if pendente:
        st.warning(
            f"Você já começou a trabalhar no desafio **{tema_atual().nome}**. "
            f"Trocar para **{REGISTRY[pendente].nome}** apaga o pipeline de tratamento e as respostas da SPEC. "
            "Deseja continuar?"
        )
        c1, c2, _ = st.columns([1, 1, 3])
        c1.button("Sim, trocar de desafio", type="primary", on_click=escolher_tema, args=(pendente,))
        c2.button("Cancelar", on_click=_cancelar_troca)

    tema = tema_atual()
    if tema:
        st.divider()
        st.subheader(f"{tema.emoji} {tema.nome}")
        st.markdown(f"**Problemática**\n\n{tema.problematica}")
        st.markdown("**Proposta inicial de entrega** (o mínimo que a solução deve ter)")
        st.markdown("\n".join(f"- {item}" for item in tema.proposta_inicial))
        st.markdown("**Aprofundamentos opcionais** (para quem quiser ir além)")
        st.markdown("\n".join(f"- {item}" for item in tema.aprofundamentos))
        st.markdown(f"**Sobre a base:** {tema.descricao_base}")
        st.markdown(f"**Fonte:** [{tema.fonte}]({tema.fonte})  \n**Licença:** {tema.licenca}")

    rodape(pode_avancar=tema is not None and not pendente, motivo="Escolha um desafio para avançar.")
