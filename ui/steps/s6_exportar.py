import streamlit as st

from core import exporter
from core import spec_builder as sb
from ui.components import ETAPA_GABARITO, cabecalho, carregar_base, fmt_int, fmt_pct, ir_para, rodape, tema_atual
from ui.steps.s5_spec import estado_spec

PROMPT = (
    "Leia SPEC.md e construa a aplicação descrita usando apenas dados_tratados.csv. "
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

    cabecalho("Exporte sua entrega", "Baixe os dois arquivos e leve para o agente de código.")
    c = st.columns(4)
    c[0].metric("Missão", tema.dominio, help=tema.area_cliente)
    c[1].metric("Passos na pipeline", len(estado.passos))
    c[2].metric("Linhas mantidas", fmt_pct(len(estado.df) / len(original)),
                help=f"{fmt_int(len(estado.df))} de {fmt_int(len(original))}")
    c[3].metric("Colunas", fmt_int(estado.df.shape[1]))

    if sb.faltando_por_passo(st.session_state.spec):
        st.warning("A SPEC tem campos obrigatórios vazios. Volte à etapa 5 para completar.", icon=":material/warning:")

    nome_csv = exporter.nome_arquivo(st.session_state.equipe, "dados_tratados.csv")
    nome_spec = exporter.nome_arquivo(st.session_state.equipe, "SPEC.md")
    with st.container(border=True):
        st.markdown("**Seus arquivos**")
        d1, d2 = st.columns(2)
        d1.download_button(f"Baixar {nome_csv}", data=exporter.gerar_csv(estado.df), file_name=nome_csv,
                           mime="text/csv", type="primary", width="stretch", icon=":material/table:",
                           on_click=_marcar_exportou)
        d2.download_button(f"Baixar {nome_spec}", data=exporter.gerar_spec(estado).encode("utf-8"),
                           file_name=nome_spec, mime="text/markdown", type="primary", width="stretch",
                           icon=":material/description:", on_click=_marcar_exportou)
        st.caption(f"CSV com {fmt_int(len(estado.df))} linhas e {fmt_int(estado.df.shape[1])} colunas, em UTF-8 "
                   "(abre com acentos corretos no Excel).")

    st.subheader("Próximo passo: construir a solução", anchor=False)
    st.markdown(
        "1. Crie uma pasta nova no seu computador.\n"
        "2. Coloque os dois arquivos nela e renomeie para `dados_tratados.csv` e `SPEC.md`.\n"
        "3. Abra o Claude Code nessa pasta.\n"
        "4. Envie o prompt abaixo (use o botão de copiar no canto do quadro):"
    )
    st.code(PROMPT, language="text")

    st.subheader("Revisão com o facilitador", anchor=False)
    st.write("Depois de baixar os arquivos, abra o gabarito do desafio para discutir suas decisões em grupo.")
    st.button("Abrir revisão com o facilitador", icon=":material/school:", on_click=_abrir_gabarito)
    rodape()
