import streamlit as st

from core import gabarito as gb
from ui.components import cabecalho, carregar_base, df_atual, ir_para, tema_atual

SELO = {
    "boa_pratica": ("Boa prática", ":material/check_circle:", "green"),
    "armadilha": ("Armadilha", ":material/warning:", "red"),
    "depende": ("Depende do objetivo", ":material/help:", "orange"),
    "livre": ("Personalizado", ":material/tune:", "gray"),
}
NIVEL = {"erro": ("Crítico", "red"), "alerta": ("Atenção", "orange"), "info": ("Informação", "blue")}


def render() -> None:
    tema = tema_atual()
    if tema is None or not st.session_state.get("exportou"):
        st.warning("O gabarito fica disponível depois que a equipe exporta os arquivos.")
        return
    original, df = carregar_base(tema), df_atual(tema)
    cabecalho(
        "Revisão com o facilitador",
        "Agora que a entrega foi feita, compare suas decisões com o gabarito do desafio. Use esta tela na "
        "conversa com o facilitador: o objetivo é entender o porquê, não tirar nota.",
    )

    aba1, aba2, aba3 = st.tabs(["Seus passos", "Pontos de qualidade", "SPEC de referência"])
    with aba1:
        for item in gb.passos_comentados(tema, st.session_state.passos, st.session_state.blocos):
            rotulo, icone, cor = SELO[item.categoria]
            with st.container(border=True):
                st.markdown(f"**{item.n}. {item.titulo}**")
                st.badge(rotulo, icon=icone, color=cor)
                st.write(item.feedback)
                if item.pergunta:
                    st.caption(f"Para discutir: {item.pergunta}")
                if item.sugestao:
                    st.caption(item.sugestao)
        faltaram = gb.boas_praticas_nao_usadas(tema, st.session_state.passos)
        if faltaram:
            with st.expander(f"Boas práticas do catálogo que você não usou ({len(faltaram)})"):
                for b in faltaram:
                    st.markdown(f"- **{b.titulo}** — {b.feedback}")
    with aba2:
        st.caption("Regras que o facilitador usa para conferir a base tratada (genéricas e do desafio).")
        for r in gb.regras(tema, original, df, st.session_state.passos):
            if r.check.nivel == "info":
                continue
            rotulo, cor = NIVEL[r.check.nivel]
            with st.container(border=True):
                a, b = st.columns([5, 1], vertical_alignment="center")
                a.markdown(f"**{r.check.titulo}**")
                if r.passou:
                    b.badge("Ok", icon=":material/check:", color="green")
                else:
                    b.badge(rotulo, color=cor)
                st.caption(f"{r.mensagem} {r.check.explicacao}")
        if tema.observacoes:
            with st.expander("Cuidados com os dados que o facilitador esperava ver na SPEC"):
                for _, texto in tema.observacoes:
                    st.markdown(f"- {texto}")
    with aba3:
        d = tema.spec_defaults
        st.caption("Uma possível SPEC para esta missão. Não é a única resposta certa: compare as ideias com a sua.")
        st.markdown(f"**Problema:** {d.get('problema', '')}")
        for titulo, chave in (("Funcionalidades", "funcionalidades"), ("Regras de negócio", "regras_negocio"),
                              ("Critérios de aceitação", "criterios_aceitacao")):
            st.markdown(f"**{titulo}**")
            st.markdown("\n".join(f"- {x}" for x in d.get(chave, [])))
        st.markdown(f"**Métrica de sucesso:** {d.get('metrica_sucesso', '')}")
    st.divider()
    st.button("Voltar para a exportação", icon=":material/arrow_back:", on_click=ir_para, args=(6,))
