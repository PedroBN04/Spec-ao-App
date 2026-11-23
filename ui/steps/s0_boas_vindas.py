import streamlit as st

from ui.components import campo_persistente, rodape, salvar_campo


def render() -> None:
    st.title("🧪 Da Spec ao App")
    st.subheader("Laboratório guiado de dados e especificação")

    st.markdown(
        "Nesta jornada você vai:\n"
        "1. **escolher um desafio** com uma base de dados real;\n"
        "2. **entender e tratar os dados** clicando em blocos prontos, vendo o efeito de cada escolha;\n"
        "3. **escrever uma especificação** (SPEC) que um agente de código usa para construir a solução."
    )

    col_arquivos, col_tempo = st.columns([3, 1])
    with col_arquivos:
        st.markdown(
            "**No final você baixa 2 arquivos:**\n"
            "- `dados_tratados.csv` — a base depois dos seus tratamentos "
            "(CSV é uma planilha salva como texto: abre no Excel e em qualquer programa de dados);\n"
            "- `SPEC.md` — o documento que explica ao **agente de código** o que construir "
            "(agente de código é um assistente de IA que escreve programas, como o Claude Code)."
        )
    with col_tempo:
        st.metric("Tempo estimado", "≈ 60 min")

    st.text_input(
        "Nome da equipe *",
        key=campo_persistente("equipe"),
        on_change=salvar_campo,
        args=("equipe",),
        placeholder="Ex.: Equipe Alfa (digite e tecle Enter)",
        help="Obrigatório. Aparece no nome dos arquivos e na SPEC. Digite e tecle Enter.",
        max_chars=40,
    )
    salvar_campo("equipe")

    st.warning(
        "**Como funciona**\n\n"
        "Os blocos de tratamento misturam **boas práticas** e **armadilhas** — de propósito. "
        "O app não vai te impedir de errar: ele executa o que você escolher e depois mostra a consequência. "
        "Leia a explicação de cada bloco, pense no seu objetivo e decida. Qualquer passo pode ser desfeito.\n\n"
        "⚠️ **Não recarregue a página (F5) nem feche a aba** até baixar os arquivos: o app não salva nada "
        "no servidor e, ao recarregar a página, recomeça do zero."
    )

    equipe_ok = bool(st.session_state.equipe.strip())
    rodape(pode_avancar=equipe_ok, motivo="Digite o nome da equipe para avançar.")
