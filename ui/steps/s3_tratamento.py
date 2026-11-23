import streamlit as st

from core import executor as ex
from core.diagnostics import tipo_amigavel
from core.models import Block, StepResult, Theme
from ui.components import (
    avisar,
    carregar_base,
    df_atual,
    fmt_int,
    fmt_pct,
    mostrar_avisos,
    rodape,
    selo,
    tabela_amostra,
    tema_atual,
)


# ---------------------------------------------------------------------------
# Ações (callbacks: rodam antes da tela ser redesenhada)
# ---------------------------------------------------------------------------


def _aplicar(tema: Theme, block_id: str) -> None:
    if block_id in st.session_state.passos:  # clique duplo: ignora
        return
    original = carregar_base(tema)
    atual = df_atual(tema)
    bloco = tema.bloco(block_id)
    motivo = ex.motivo_desabilitado(tema, bloco, atual, st.session_state.passos, list(original.columns))
    if motivo:
        avisar("warning", motivo)
        return
    novo, resultado = ex.aplicar(atual, bloco)
    if resultado.erro:
        avisar(
            "error",
            f"O bloco **{bloco.id}** não pôde ser aplicado nesta base, então nada mudou. "
            "Isso costuma acontecer quando um passo anterior mudou o formato de uma coluna. "
            "Experimente desfazer o último passo ou aplicar os blocos em outra ordem.",
            resultado.erro,
        )
        return
    st.session_state.df_atual = novo
    st.session_state.passos = st.session_state.passos + [block_id]
    st.session_state.resultados = {**st.session_state.resultados, block_id: resultado}
    avisar("info", f"Bloco **{block_id}** aplicado. Veja a avaliação e o impacto em **Meu pipeline**.")


def _desfazer(tema: Theme, block_id: str) -> None:
    if block_id not in st.session_state.passos:
        return
    pipe = ex.desfazer(carregar_base(tema), tema, st.session_state.passos, block_id)
    st.session_state.passos = pipe.passos
    st.session_state.resultados = pipe.resultados
    st.session_state.df_atual = pipe.df if pipe.passos else None
    avisar("success", f"Passo **{block_id}** desfeito. Os demais passos foram reaplicados a partir da base original.")
    for removido, motivo in pipe.removidos:
        avisar("warning", f"O passo **{removido}** também foi removido: {motivo}")


def _alternar(chave: str) -> None:
    st.session_state[chave] = not st.session_state.get(chave, False)


# ---------------------------------------------------------------------------
# Desenho
# ---------------------------------------------------------------------------


def _cartao_bloco(tema: Theme, bloco: Block, motivo: str | None) -> None:
    aplicado = bloco.id in st.session_state.passos
    with st.container(border=True):
        st.markdown(f"**{bloco.id} · {bloco.titulo}**")
        st.write(bloco.explicacao)
        chave_codigo = f"ver_codigo_{bloco.id}"
        c1, c2 = st.columns(2)
        c1.button(
            "Esconder código" if st.session_state.get(chave_codigo) else "Ver código",
            key=f"btn_codigo_{bloco.id}",
            on_click=_alternar,
            args=(chave_codigo,),
            width="stretch",
        )
        c2.button(
            "✓ Aplicado" if aplicado else "Aplicar",
            key=f"aplicar_{bloco.id}",
            type="secondary" if aplicado else "primary",
            disabled=aplicado or motivo is not None,
            on_click=_aplicar,
            args=(tema, bloco.id),
            width="stretch",
        )
        if st.session_state.get(chave_codigo):
            st.code(bloco.codigo, language="python")
        if motivo and not aplicado:
            st.caption(f"🔒 {motivo}")


def _catalogo(tema: Theme) -> None:
    st.subheader("📚 Catálogo de blocos")
    st.caption("Leia a explicação, veja o código se quiser e clique em **Aplicar**. A avaliação aparece depois.")
    original = carregar_base(tema)
    atual = df_atual(tema)
    grupos: dict[str, list[Block]] = {}
    for bloco in tema.blocos:
        grupos.setdefault(bloco.grupo, []).append(bloco)
    for grupo, blocos in grupos.items():
        aplicados = sum(b.id in st.session_state.passos for b in blocos)
        with st.expander(f"{grupo} ({aplicados}/{len(blocos)} aplicados)", expanded=False):
            for bloco in blocos:
                motivo = ex.motivo_desabilitado(tema, bloco, atual, st.session_state.passos, list(original.columns))
                _cartao_bloco(tema, bloco, motivo)


def _metricas_passo(r: StepResult) -> None:
    c = st.columns(3)
    c[0].metric("Linhas", fmt_int(r.linhas_depois), delta=fmt_int(r.linhas_depois - r.linhas_antes) if r.linhas_depois != r.linhas_antes else None)
    c[1].metric("Colunas", fmt_int(r.colunas_depois), delta=fmt_int(r.colunas_depois - r.colunas_antes) if r.colunas_depois != r.colunas_antes else None)
    c[2].metric(
        "Nulos",
        fmt_int(r.nulos_depois),
        delta=fmt_int(r.nulos_depois - r.nulos_antes) if r.nulos_depois != r.nulos_antes else None,
        delta_color="inverse",
        help="Nulo = célula vazia.",
    )
    detalhes = []
    if r.colunas_criadas:
        nomes = ", ".join(f"`{c}`" for c in r.colunas_criadas[:8])
        extra = f" e mais {fmt_int(len(r.colunas_criadas) - 8)}" if len(r.colunas_criadas) > 8 else ""
        detalhes.append(f"➕ Colunas criadas: {nomes}{extra}")
    if r.colunas_removidas:
        nomes = ", ".join(f"`{c}`" for c in r.colunas_removidas[:8])
        extra = f" e mais {fmt_int(len(r.colunas_removidas) - 8)}" if len(r.colunas_removidas) > 8 else ""
        detalhes.append(f"➖ Colunas removidas: {nomes}{extra}")
    if r.tipos_alterados:
        detalhes.append(
            "🔄 Tipo mudou: "
            + ", ".join(
                f"`{c}` ({tipo_amigavel(a)} → {tipo_amigavel(d)})" for c, (a, d) in list(r.tipos_alterados.items())[:8]
            )
        )
    for d in detalhes:
        st.markdown(d)
    removido = ex.pct_linhas_removidas(r)
    if removido > ex.LIMITE_REMOCAO_LINHAS:
        st.error(f"Este passo removeu {fmt_pct(removido)} da base.")


def _pipeline(tema: Theme) -> None:
    st.subheader("🛠️ Meu pipeline")
    passos = st.session_state.passos
    if not passos:
        st.info("Nenhum passo ainda. Aplique um bloco do catálogo para começar.")
        return
    for n, block_id in enumerate(passos, start=1):
        bloco = tema.bloco(block_id)
        r = st.session_state.resultados[block_id]
        with st.container(border=True):
            st.markdown(f"**Passo {n} · {bloco.id} · {bloco.titulo}**")
            selo(bloco.categoria)
            _metricas_passo(r)
            if bloco.categoria == "armadilha":
                sugestao = ""
                if bloco.sugestao:
                    sugestao = f"\n\n👉 Experimente o bloco **{bloco.sugestao}** ({tema.bloco(bloco.sugestao).titulo})."
                st.warning(f"{bloco.feedback}{sugestao}")
            elif bloco.categoria == "depende":
                st.info(bloco.feedback)
            else:
                st.success(bloco.feedback)
            st.markdown(f"🤔 *{bloco.pergunta_reflexao}*")
            st.button(
                "↩️ Desfazer este passo",
                key=f"desfazer_{block_id}",
                on_click=_desfazer,
                args=(tema, block_id),
            )


def _base_atual(tema: Theme) -> None:
    original = carregar_base(tema)
    atual = df_atual(tema)
    st.subheader("📋 Base atual")
    c = st.columns(4)
    c[0].metric("Linhas", fmt_int(len(atual)))
    c[1].metric("Colunas", fmt_int(atual.shape[1]))
    c[2].metric("Nulos", fmt_int(ex.contar_nulos(atual)), help="Total de células vazias.")
    c[3].metric(
        "Linhas mantidas",
        fmt_pct(len(atual) / len(original)),
        help="Quantas linhas da base original continuam na base atual.",
    )
    tabela_amostra(atual)
    if st.session_state.passos:
        st.button(
            "Esconder código completo" if st.session_state.get("ver_pipeline") else "Ver código completo do pipeline",
            on_click=_alternar,
            args=("ver_pipeline",),
        )
        if st.session_state.get("ver_pipeline"):
            st.caption("Este é exatamente o código que o app executou, na ordem dos seus passos.")
            st.code(ex.codigo_completo(tema, st.session_state.passos), language="python")


def render() -> None:
    tema = tema_atual()
    if tema is None:
        st.warning("Escolha um desafio na etapa 1 antes do tratamento.")
        rodape(pode_avancar=False)
        return

    st.header("3. Tratamento em blocos")
    st.caption(
        f"{tema.emoji} {tema.nome} — monte o tratamento clicando em blocos. "
        "Atenção: boas práticas e armadilhas estão misturadas. Você só descobre qual é qual depois de aplicar."
    )
    if not tema.blocos:
        st.info("🚧 Os blocos deste desafio ainda estão em construção.")
        rodape(pode_avancar=False)
        return

    mostrar_avisos()
    esquerda, direita = st.columns(2, gap="large")
    with esquerda:
        _catalogo(tema)
    with direita:
        _pipeline(tema)
    st.divider()
    _base_atual(tema)
    rodape(pode_avancar=bool(st.session_state.passos), motivo="Aplique pelo menos 1 bloco para avançar.")
