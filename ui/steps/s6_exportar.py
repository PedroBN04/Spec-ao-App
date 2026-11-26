import streamlit as st

from core import exporter
from core import spec_builder as sb
from ui.components import ETAPA_GABARITO, cabecalho, carregar_base, fmt_int, fmt_pct, ir_para, rodape, tema_atual
from ui.steps.s5_spec import estado_spec

PROMPT = (
    "Leia o arquivo SPEC.md e construa a aplicação descrita usando apenas o arquivo dados_tratados.csv. "
    "Siga os critérios de aceitação e não invente dados."
)


def _marcar_exportou() -> None:
    st.session_state.exportou = True


def _abrir_gabarito() -> None:
    st.session_state.exportou = True
    ir_para(ETAPA_GABARITO)


def render() -> None:
    tema = tema_atual()
    if tema is None:
        st.warning("Escolha uma missão antes de exportar.")
        rodape()
        return
    estado = estado_spec()
    original = carregar_base(tema)

    cabecalho("Exporte sua entrega", "Baixe o kit da equipe e leve para o assistente de IA que vai construir o painel.")
    c = st.columns(4)
    c[0].metric("Missão", tema.dominio, help=tema.area_cliente)
    c[1].metric("Passos na pipeline", len(estado.passos))
    c[2].metric("Linhas mantidas", fmt_pct(len(estado.df) / len(original)),
                help=f"{fmt_int(len(estado.df))} de {fmt_int(len(original))}")
    c[3].metric("Colunas", fmt_int(estado.df.shape[1]))

    if sb.faltando_por_passo(st.session_state.spec):
        st.warning("A SPEC tem campos obrigatórios vazios. Volte à etapa 5 para completar.", icon=":material/warning:")

    df = estado.df
    spec = exporter.gerar_spec(estado)
    slug = exporter.slug_equipe(st.session_state.equipe)
    tem_xlsx = exporter.xlsx_viavel(df)

    with st.container(border=True):
        st.markdown("**Kit da equipe (recomendado)**")
        st.caption(
            "Um arquivo .zip com tudo pronto e com os nomes certos: `dados_tratados.csv` (para o assistente de IA), "
            + ("`dados_tratados_excel.xlsx` (abre direto no Excel, em linhas e colunas) " if tem_xlsx else "")
            + "e `SPEC.md`. É só extrair numa pasta — não precisa renomear nada."
        )
        st.download_button(
            f"Baixar kit_{slug}.zip",
            data=lambda: exporter.gerar_zip(df, spec),
            file_name=f"kit_{slug}.zip",
            mime="application/zip",
            type="primary",
            icon=":material/folder_zip:",
            width="stretch",
            on_click=_marcar_exportou,
            key="baixar_kit",
        )
        if not tem_xlsx:
            st.caption(f"A base tem {fmt_int(df.shape[1])} colunas: grande demais para uma planilha de Excel "
                       "confortável, então o kit traz só o CSV e a SPEC.")
        st.caption("Os arquivos já saem compatíveis com acentos em português. O primeiro download pode levar "
                   "alguns segundos enquanto a planilha é montada.")

    with st.expander("Baixar arquivos separados", icon=":material/download:"):
        a, b, c = st.columns(3)
        if tem_xlsx:
            a.download_button("Planilha para Excel (.xlsx)", data=lambda: exporter.gerar_xlsx(df),
                              file_name="dados_tratados_excel.xlsx", icon=":material/table:", width="stretch",
                              mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                              on_click=_marcar_exportou, key="baixar_xlsx")
        b.download_button("CSV para a IA (.csv)", data=lambda: exporter.gerar_csv(df), file_name="dados_tratados.csv",
                          mime="text/csv", icon=":material/data_object:", width="stretch", on_click=_marcar_exportou,
                          key="baixar_csv")
        c.download_button("Especificação (SPEC.md)", data=spec.encode("utf-8"), file_name="SPEC.md",
                          mime="text/markdown", icon=":material/description:", width="stretch",
                          on_click=_marcar_exportou, key="baixar_spec")
        st.caption(f"Base tratada: {fmt_int(len(df))} linhas e {fmt_int(df.shape[1])} colunas.")

    st.subheader("Próximo passo: construir a solução com um assistente de IA", anchor=False)
    st.write("Use o assistente de código que a turma estiver usando. O pedido (prompt) é o mesmo para todos:")
    st.code(PROMPT, language="text", wrap_lines=True)
    aba1, aba2 = st.tabs(["Assistente no computador (terminal ou editor)", "Chat na web"])
    with aba1:
        st.markdown(
            "Ex.: Claude Code, Cursor, Windsurf, GitHub Copilot, Antigravity.\n\n"
            "1. Extraia o kit `.zip` numa pasta nova.\n"
            "2. Abra o assistente **nessa pasta** (no terminal ou abrindo a pasta no editor).\n"
            "3. Cole o prompt acima e acompanhe o que ele faz."
        )
    with aba2:
        st.markdown(
            "Ex.: ChatGPT, Gemini, Claude no navegador.\n\n"
            "1. Extraia o kit `.zip`.\n"
            "2. Envie os arquivos `dados_tratados.csv` e `SPEC.md` na conversa.\n"
            "3. Cole o prompt acima. Se a base for grande demais para o chat, peça o código do app e rode-o no "
            "seu computador com o CSV."
        )

    st.subheader("Revisão com o facilitador", anchor=False)
    st.write("Depois de baixar os arquivos, abra o gabarito do desafio para discutir suas decisões em grupo.")
    st.button("Abrir revisão com o facilitador", icon=":material/school:", on_click=_abrir_gabarito)
    rodape()
