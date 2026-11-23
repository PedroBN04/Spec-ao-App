import streamlit as st

from ui.components import cabecalho, campo_persistente, rodape, salvar_campo

JORNADA = [
    ("Missão", "Uma área da empresa (a área cliente) pede ajuda com um problema. Você escolhe qual missão aceitar."),
    ("Diagnóstico", "Você investiga a base de dados que veio do sistema, do jeito que estava, e anota o que encontrar."),
    ("Pipeline", "Você monta, bloco a bloco, a sequência de tratamentos que deixa a base pronta para uso."),
    ("Revisão", "Você compara a base original com a tratada e decide se precisa ajustar algo."),
    ("SPEC", "Você escreve a especificação: o que construir, para quem, com quais regras e como conferir."),
    ("Exportar", "Você baixa a base tratada e a SPEC, que um agente de IA usa para construir o painel."),
]


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
        st.caption("A base depois da sua pipeline de tratamento. CSV é uma planilha salva como texto.")
    with b, st.container(border=True):
        st.markdown("**`SPEC.md`**")
        st.caption("A especificação escrita por você: problema, escopo, dados, regras e critérios de aceitação.")

    st.subheader("A jornada", anchor=False)
    for i, (nome, texto) in enumerate(JORNADA, start=1):
        st.markdown(f"**{i}. {nome}** — {texto}")
    st.caption("Tempo estimado: cerca de 60 minutos. Termos novos estão explicados no Glossário, na barra lateral.")

    st.subheader("Sua equipe", anchor=False)
    st.text_input(
        "Nome da equipe",
        key=campo_persistente("equipe"),
        on_change=salvar_campo,
        args=("equipe",),
        placeholder="Ex.: Equipe Alfa",
        help="Aparece no nome dos arquivos e na SPEC. Digite e tecle Enter.",
        max_chars=40,
    )
    salvar_campo("equipe")
    st.caption(
        "O app não guarda nada no servidor: se a página for recarregada, a jornada recomeça do zero. "
        "Baixe os arquivos no final."
    )
    rodape(pode_avancar=bool(st.session_state.equipe.strip()), motivo="Digite o nome da equipe para começar.",
           rotulo_avancar="Começar")
