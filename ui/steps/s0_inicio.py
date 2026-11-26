import streamlit as st

from ui.components import cabecalho, ir_para

JORNADA = [
    ("Missão", "Uma área da empresa (a área cliente) pede ajuda com um problema. Você escolhe qual missão aceitar."),
    ("Diagnóstico", "Você investiga a base de dados que veio do sistema, do jeito que estava, e anota o que encontrar."),
    ("Pipeline", "Você monta, bloco a bloco, a sequência de tratamentos que deixa a base pronta para uso."),
    ("Revisão", "Você compara a base original com a tratada e decide se precisa ajustar algo."),
    ("SPEC", "Você escreve a especificação: o que construir, para quem, com quais regras e como conferir."),
    ("Exportar", "Você baixa a base tratada e a SPEC, que um agente de IA usa para construir o painel."),
]


def _comecar() -> None:
    nome = (st.session_state.get("form_equipe") or "").strip()
    if not nome:
        st.session_state.equipe_vazia = True
        return
    st.session_state.equipe = nome
    ir_para(1)


def render() -> None:
    cabecalho(
        "Da Spec ao App",
        "Você vai atuar como analista de dados: entender um pedido, preparar os dados e escrever a "
        "especificação de uma aplicação que um agente de IA vai construir.",
    )

    c1, c2, c3 = st.columns(3)
    papeis = [
        (":material/business_center:", "A área cliente", "Tem um problema de negócio e uma base de dados exportada "
         "do sistema. Sabe o que dói, mas não sabe o que os dados dizem."),
        (":material/query_stats:", "Você (analista)", "Investiga a base, decide como tratá-la e escreve uma SPEC "
         "clara. As decisões são suas: não há um único caminho certo."),
        (":material/smart_toy:", "O agente de código", "Recebe a base tratada e a SPEC e constrói a aplicação. "
         "Ele faz exatamente o que estiver escrito — nem mais, nem menos."),
    ]
    for col, (icone, titulo, texto) in zip((c1, c2, c3), papeis):
        with col, st.container(border=True, height="stretch"):
            st.markdown(f"#### {icone} {titulo}")
            st.write(texto)

    st.subheader("O que você vai construir", anchor=False)
    st.write(
        "No hackathon, a entrega final é um **painel** (dashboard): uma aplicação web com números, gráficos, "
        "filtros e listas que ajuda a área cliente a decidir. Você não vai programar o painel aqui. "
        "Aqui você prepara as duas peças que permitem a um agente de IA construí-lo bem:"
    )
    a, b = st.columns(2)
    with a, st.container(border=True):
        st.markdown("**`dados_tratados.csv`**")
        st.caption("A base depois da sua pipeline de tratamento, numa tabela simples em texto (CSV) que a IA lê. "
                   "O kit final também traz uma planilha .xlsx que abre direto no Excel.")
    with b, st.container(border=True):
        st.markdown("**`SPEC.md`**")
        st.caption("A especificação escrita por você: problema, escopo, dados, regras e critérios de aceitação.")

    st.subheader("A jornada", anchor=False)
    for i, (nome, texto) in enumerate(JORNADA, start=1):
        st.markdown(f"**{i}. {nome}** — {texto}")
    st.caption("Tempo estimado: cerca de 60 minutos. Termos novos estão explicados no Glossário, na barra lateral.")

    st.subheader("Sua equipe", anchor=False)
    with st.form("form_inicio", border=False):
        st.text_input(
            "Nome da equipe",
            value=st.session_state.equipe,
            key="form_equipe",
            placeholder="Ex.: Equipe Alfa",
            help="Aparece no nome dos arquivos e na SPEC.",
            max_chars=40,
        )
        _, direita = st.columns([4, 1])
        direita.form_submit_button("Começar", type="primary", icon=":material/arrow_forward:",
                                   icon_position="right", on_click=_comecar, width="stretch")
    if st.session_state.pop("equipe_vazia", False):
        st.warning("Digite um nome para sua equipe antes de começar.", icon=":material/edit:")
    st.caption(
        "O app não guarda nada no servidor. Use \"Salvar ou retomar progresso\", na barra lateral, para não "
        "perder o trabalho se a página recarregar."
    )
