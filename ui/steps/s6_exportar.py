import streamlit as st

from core import checklist as ck
from core import exporter
from core import spec_builder as sb
from ui.components import carregar_base, fmt_int, fmt_pct, rodape, tema_atual
from ui.steps.s5_spec import estado_spec

PROMPT = (
    "Leia SPEC.md e construa a aplicação descrita usando apenas dados_tratados.csv. "
    "Siga os critérios de aceitação e não invente dados."
)


def render() -> None:
    tema = tema_atual()
    if tema is None:
        st.warning("Escolha um desafio na etapa 1 antes de exportar.")
        rodape()
        return

    estado = estado_spec()
    original = carregar_base(tema)
    p = ck.placar(estado.checks)

    st.header("6. Exportar")
    st.caption("Confira o resumo e baixe os dois arquivos da sua equipe.")

    contagem = {cat: 0 for cat in ck.ROTULO_CATEGORIA}
    for bid in estado.passos:
        contagem[tema.bloco(bid).categoria] += 1
    c = st.columns(4)
    c[0].metric("Desafio", f"{tema.emoji} {tema.dominio}", help=tema.nome)
    c[1].metric("Blocos aplicados", len(estado.passos))
    c[2].metric("Nota do checklist", f"{p['nota']}/100")
    c[3].metric("Linhas mantidas", fmt_pct(len(estado.df) / len(original)), help=f"{fmt_int(len(estado.df))} de {fmt_int(len(original))}")
    st.markdown(
        " · ".join(f"{ck.ICONE_CATEGORIA[cat]} {ck.ROTULO_CATEGORIA[cat]}: **{n}**" for cat, n in contagem.items())
    )

    pendentes = ck.pendencias(estado.checks, st.session_state.justificativas)
    faltando = sb.faltando_por_passo(st.session_state.spec)
    if pendentes:
        st.warning(
            f"O checklist tem {len(pendentes)} item(ns) sem correção nem justificativa (a base mudou depois do "
            "checklist?). Volte à etapa 4 para resolver antes de baixar."
        )
    if faltando:
        st.warning("A SPEC tem campos obrigatórios vazios. Volte à etapa 5 para completar.")

    csv = exporter.gerar_csv(estado.df)
    spec = exporter.gerar_spec(estado)
    nome_csv = exporter.nome_arquivo(st.session_state.equipe, "dados_tratados.csv")
    nome_spec = exporter.nome_arquivo(st.session_state.equipe, "SPEC.md")

    st.subheader("⬇️ Seus arquivos")
    d1, d2 = st.columns(2)
    d1.download_button(
        f"Baixar {nome_csv}",
        data=csv,
        file_name=nome_csv,
        mime="text/csv",
        type="primary",
        width="stretch",
        icon="📊",
        on_click="ignore",
    )
    d2.download_button(
        f"Baixar {nome_spec}",
        data=spec.encode("utf-8"),
        file_name=nome_spec,
        mime="text/markdown",
        type="primary",
        width="stretch",
        icon="📝",
        on_click="ignore",
    )
    st.caption(
        f"O CSV tem {fmt_int(len(estado.df))} linhas e {fmt_int(estado.df.shape[1])} colunas, em UTF-8 "
        "(abre com acentos corretos no Excel). Ao usar no Claude Code, renomeie para `dados_tratados.csv` "
        "e `SPEC.md`."
    )

    st.subheader("🚀 Próximo passo: construir a solução")
    st.markdown(
        "1. Crie uma pasta nova no seu computador.\n"
        "2. Coloque os dois arquivos nela, com os nomes `dados_tratados.csv` e `SPEC.md`.\n"
        "3. Abra o Claude Code nessa pasta.\n"
        "4. Envie o prompt abaixo (use o botão de copiar no canto do quadro):"
    )
    st.code(PROMPT, language="text")
    rodape()
