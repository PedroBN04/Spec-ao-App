"""Etapa 3 — Pipeline (v2): montar o tratamento como um fluxo de nós, no estilo n8n.

Nada aqui diz se uma escolha é certa ou errada: o app só mostra o que cada passo faz e o efeito nos dados.
"""

import streamlit as st

from core import blocos_livres as bl
from core import executor as ex
from core.models import Block, StepResult, Theme
from ui.components import avisar, cabecalho, carregar_base, df_atual, fmt_int, fmt_pct, mostrar_avisos, rodape, tabela_amostra, tema_atual

# ---------------------------------------------------------------------------
# Estado do fluxo
# ---------------------------------------------------------------------------


def _novo_uid() -> str:
    n = st.session_state.prox_uid
    st.session_state.prox_uid = n + 1
    return f"P{n}"


def _titulo(passo) -> str:
    bloco = st.session_state.blocos.get(ex.uid(passo))
    return bloco.titulo.replace("`", "") if bloco else ex.uid(passo)


def _rodar(tema: Theme, passos: list) -> None:
    """Reexecuta o fluxo inteiro a partir da base original e avisa (sem julgar) o que saiu."""
    titulos_antes = {ex.uid(p): _titulo(p) for p in st.session_state.passos}
    pipe = ex.reexecutar(carregar_base(tema), tema, passos)
    st.session_state.passos = pipe.passos
    st.session_state.resultados = pipe.resultados
    st.session_state.blocos = pipe.blocos
    st.session_state.df_atual = pipe.df if pipe.passos else None
    for chave, motivo in pipe.removidos:
        avisar("warning", f"O passo \"{titulos_antes.get(chave, chave)}\" saiu do fluxo: {motivo}")


def _anexar(tema: Theme, passo: dict, bloco: Block) -> None:
    atual = df_atual(tema)
    motivo = ex.motivo_desabilitado(tema, bloco, atual, [ex.id_catalogo(p) for p in st.session_state.passos if ex.id_catalogo(p)],
                                    list(carregar_base(tema).columns))
    if motivo:
        avisar("warning", motivo)
        return
    novo, resultado = ex.aplicar(atual, bloco)
    if resultado.erro:
        avisar("error", f"O passo \"{bloco.titulo.replace('`', '')}\" não pôde ser executado nesta base, então nada mudou. "
                "Confira o tipo e os valores da coluna no ponto do fluxo em que ele entraria.", resultado.erro)
        return
    st.session_state.df_atual = novo
    st.session_state.passos = st.session_state.passos + [passo]
    st.session_state.resultados = {**st.session_state.resultados, passo["uid"]: resultado}
    st.session_state.blocos = {**st.session_state.blocos, passo["uid"]: bloco}


def _adicionar_catalogo(tema: Theme, block_id: str) -> None:
    if any(ex.id_catalogo(p) == block_id for p in st.session_state.passos):
        return  # clique duplo
    _anexar(tema, {"uid": _novo_uid(), "tipo": "catalogo", "id": block_id, "nota": ""}, tema.bloco(block_id))


def _adicionar_livre(tema: Theme, acao: str, params: dict) -> None:
    uid = _novo_uid()
    try:
        bloco = bl.gerar_bloco(uid, acao, params, df_atual(tema))
    except bl.ParametroInvalido as erro:
        avisar("warning", str(erro))
        return
    _anexar(tema, {"uid": uid, "tipo": "livre", "acao": acao, "params": dict(params), "nota": ""}, bloco)


def _remover(tema: Theme, chave: str) -> None:
    _rodar(tema, [p for p in st.session_state.passos if ex.uid(p) != chave])


def _mover(tema: Theme, chave: str, desloc: int) -> None:
    _rodar(tema, ex.mover(st.session_state.passos, chave, desloc))


def _salvar_nota(chave: str) -> None:
    texto = st.session_state.get(f"nota_{chave}", "")
    st.session_state.passos = [
        {**p, "nota": texto} if isinstance(p, dict) and p["uid"] == chave else p for p in st.session_state.passos
    ]


# ---------------------------------------------------------------------------
# Biblioteca
# ---------------------------------------------------------------------------


def _catalogo(tema: Theme) -> None:
    original = carregar_base(tema)
    atual = df_atual(tema)
    usados = {ex.id_catalogo(p) for p in st.session_state.passos}
    aplicados = [i for i in usados if i]
    grupos: dict[str, list[Block]] = {}
    for bloco in tema.blocos:
        grupos.setdefault(bloco.grupo, []).append(bloco)
    for grupo, blocos in grupos.items():
        with st.expander(f"{grupo} ({len(blocos)})"):
            for bloco in blocos:
                no_fluxo = bloco.id in usados
                motivo = None if no_fluxo else ex.motivo_desabilitado(tema, bloco, atual, aplicados, list(original.columns))
                with st.container(border=True):
                    st.markdown(f"**{bloco.titulo}**")
                    st.caption(bloco.explicacao)
                    c1, c2 = st.columns(2)
                    with c1.popover("Ver código", icon=":material/code:", width="stretch"):
                        st.code(bloco.codigo, language="python", wrap_lines=True)
                    c2.button(
                        "No fluxo" if no_fluxo else "Adicionar",
                        key=f"aplicar_{bloco.id}",
                        icon=":material/check:" if no_fluxo else ":material/add:",
                        type="secondary" if no_fluxo else "primary",
                        disabled=no_fluxo or motivo is not None,
                        on_click=_adicionar_catalogo,
                        args=(tema, bloco.id),
                        width="stretch",
                    )
                    if motivo:
                        st.caption(f":material/lock: {motivo}")


def _params_livres(acao: str, df) -> dict:
    cols = list(map(str, df.columns))
    numericas = [c for c in cols if df[c].dtype.kind in "iuf"]

    def vazios(c):
        n = int(df[c].isna().sum())
        return f"{c}  ({fmt_int(n)} vazios)" if n else c

    p: dict = {}
    if acao in ("remover_colunas",):
        p["colunas"] = st.multiselect("Colunas", cols, key="nv_colunas")
    elif acao in ("remover_linhas_vazias", "remover_duplicados"):
        p["colunas"] = st.multiselect("Comparar só estas colunas (deixe vazio para usar todas)", cols, key="nv_colunas_opc")
    elif acao == "preencher_vazios":
        p["coluna"] = st.selectbox("Coluna", cols, format_func=vazios, key="nv_coluna_pv")
        p["metodo"] = st.radio("Preencher com", list(bl.METODOS), format_func=bl.METODOS.get, key="nv_metodo", horizontal=True)
        if p["metodo"] == "valor":
            p["valor"] = st.text_input("Valor", key="nv_valor_pv")
    elif acao == "converter_tipo":
        p["coluna"] = st.selectbox("Coluna", cols, key="nv_coluna_ct")
        p["para"] = st.radio("Converter para", list(bl.TIPOS), format_func=bl.TIPOS.get, key="nv_para", horizontal=True)
    elif acao in ("filtrar_linhas", "criar_indicador"):
        p["coluna"] = st.selectbox("Coluna", cols, key="nv_coluna_f")
        a, b = st.columns(2)
        p["operador"] = a.selectbox("Condição", list(bl.OPERADORES), format_func=bl.OPERADORES.get, key="nv_op")
        p["valor"] = b.text_input("Valor", key="nv_valor_f")
        if acao == "criar_indicador":
            p["nome"] = st.text_input("Nome da coluna nova", key="nv_nome_ind")
    elif acao == "substituir_valor":
        p["coluna"] = st.selectbox("Coluna", cols, key="nv_coluna_sv")
        a, b = st.columns(2)
        p["de"] = a.text_input("Trocar o valor", key="nv_de")
        p["para"] = b.text_input("Por", key="nv_para_sv")
    elif acao == "criar_faixas":
        p["coluna"] = st.selectbox("Coluna numérica", numericas, key="nv_coluna_cf")
        p["cortes"] = st.text_input("Limites das faixas, separados por espaço", key="nv_cortes", placeholder="Ex.: 0 12 24 48 72")
        p["nome"] = st.text_input("Nome da coluna nova", key="nv_nome_cf")
    elif acao == "calcular_coluna":
        a, b, c = st.columns([3, 2, 3])
        p["coluna_a"] = a.selectbox("Coluna", numericas, key="nv_ca")
        p["conta"] = b.selectbox("Conta", list(bl.CONTAS), format_func=bl.CONTAS.get, key="nv_conta")
        p["coluna_b"] = c.selectbox("Coluna ", numericas, key="nv_cb")
        p["nome"] = st.text_input("Nome da coluna nova", key="nv_nome_cc")
    elif acao == "renomear_coluna":
        p["coluna"] = st.selectbox("Coluna", cols, key="nv_coluna_rn")
        p["novo"] = st.text_input("Novo nome", key="nv_novo")
    return p


def _personalizado(tema: Theme) -> None:
    st.caption("Monte um passo do seu jeito: escolha a ação e as colunas. O app gera o código pandas para você.")
    acao = st.selectbox("Ação", [a.id for a in bl.ACOES], format_func=lambda a: bl.ACAO_POR_ID[a].rotulo, key="nv_acao")
    st.caption(bl.ACAO_POR_ID[acao].descricao)
    atual = df_atual(tema)
    params = _params_livres(acao, atual)
    try:
        previa = bl.gerar_bloco("previa", acao, params, atual)
        st.code(previa.codigo, language="python", wrap_lines=True)
        valido = True
    except bl.ParametroInvalido as erro:
        st.caption(f":material/edit: {erro}")
        valido = False
    st.button("Adicionar ao fluxo", icon=":material/add:", type="primary", disabled=not valido,
              on_click=_adicionar_livre, args=(tema, acao, params), key="nv_adicionar", width="stretch")


# ---------------------------------------------------------------------------
# Fluxo
# ---------------------------------------------------------------------------


def _efeito(r: StepResult) -> str:
    partes = []
    if r.linhas_antes != r.linhas_depois:
        dif = r.linhas_antes - r.linhas_depois
        partes.append(f"{fmt_int(abs(dif))} linhas {'a menos' if dif > 0 else 'a mais'} "
                      f"({fmt_pct(abs(dif) / r.linhas_antes) if r.linhas_antes else '—'})")
    if r.colunas_criadas:
        partes.append(f"{fmt_int(len(r.colunas_criadas))} coluna(s) nova(s)")
    if r.colunas_removidas:
        partes.append(f"{fmt_int(len(r.colunas_removidas))} coluna(s) a menos")
    if r.nulos_antes != r.nulos_depois:
        partes.append(f"vazios: {fmt_int(r.nulos_antes)} → {fmt_int(r.nulos_depois)}")
    if r.tipos_alterados:
        partes.append("tipo alterado: " + ", ".join(f"`{c}`" for c in list(r.tipos_alterados)[:3]))
    return " · ".join(partes) if partes else "Nenhuma mudança visível em linhas, colunas, vazios ou tipos."


def _no(tema: Theme, n: int, passo, total: int) -> None:
    chave = ex.uid(passo)
    bloco = st.session_state.blocos[chave]
    r = st.session_state.resultados[chave]
    st.html("<div class='conector'></div>")
    with st.container(border=True, key=f"no_{chave}"):
        topo, b1, b2, b3 = st.columns([10, 1, 1, 1], vertical_alignment="center")
        tipo = "Pronto" if ex.eh_catalogo(passo) else "Personalizado"
        topo.markdown(f"**{n}. {bloco.titulo}** &nbsp;<span class='pill cinza'>{tipo}</span>", unsafe_allow_html=True)
        b1.button("", icon=":material/arrow_upward:", key=f"subir_{chave}", help="Mover para cima",
                  disabled=n == 1, on_click=_mover, args=(tema, chave, -1), type="tertiary")
        b2.button("", icon=":material/arrow_downward:", key=f"descer_{chave}", help="Mover para baixo",
                  disabled=n == total, on_click=_mover, args=(tema, chave, 1), type="tertiary")
        b3.button("", icon=":material/delete:", key=f"desfazer_{chave}", help="Remover do fluxo",
                  on_click=_remover, args=(tema, chave), type="tertiary")
        st.caption(_efeito(r))
        c1, c2 = st.columns([1, 3], vertical_alignment="bottom")
        with c1.popover("Código", icon=":material/code:", width="stretch"):
            st.code(bloco.codigo, language="python", wrap_lines=True)
        if f"nota_{chave}" not in st.session_state:
            st.session_state[f"nota_{chave}"] = passo.get("nota", "") if isinstance(passo, dict) else ""
        c2.text_input("Por que este passo?", key=f"nota_{chave}", on_change=_salvar_nota, args=(chave,),
                      placeholder="Por que este passo? (vai para a SPEC)", label_visibility="collapsed")


def _fluxo(tema: Theme) -> None:
    original = carregar_base(tema)
    atual = df_atual(tema)
    st.html(f"<div class='no-extremo'><b>Entrada</b> · base original · {fmt_int(len(original))} linhas × "
            f"{original.shape[1]} colunas</div>")
    passos = st.session_state.passos
    if not passos:
        st.html("<div class='conector'></div>")
        st.caption("Seu fluxo está vazio. Adicione nós a partir da biblioteca ao lado.")
    for n, passo in enumerate(passos, start=1):
        _no(tema, n, passo, len(passos))
    st.html("<div class='conector'></div>")
    pct = fmt_pct(len(atual) / len(original)) if len(original) else "—"
    st.html(f"<div class='no-extremo'><b>Saída</b> · base tratada · {fmt_int(len(atual))} linhas "
            f"({pct} da original) × {fmt_int(atual.shape[1])} colunas · "
            f"{fmt_int(int(atual.isna().sum().sum()))} células vazias</div>")


# ---------------------------------------------------------------------------
# Tela
# ---------------------------------------------------------------------------


def render() -> None:
    tema = tema_atual()
    if tema is None:
        st.warning("Escolha uma missão antes de montar a pipeline.")
        rodape(pode_avancar=False)
        return

    cabecalho(
        "Monte sua pipeline",
        "Escolha, configure e ordene os passos que vão transformar a base original na base que o painel vai usar.",
    )
    with st.expander("O que é uma pipeline?", icon=":material/account_tree:", expanded=not st.session_state.passos):
        st.markdown(
            "Uma **pipeline** é uma sequência de passos (nós) que a base percorre, da **entrada** até a "
            "**saída**. Cada nó recebe a tabela do nó anterior, faz **uma** coisa (converter um tipo, preencher "
            "vazios, remover linhas, criar uma coluna...) e entrega a tabela para o próximo — como um fluxo no "
            "n8n.\n\n"
            "- **A ordem importa:** um nó só enxerga o que os anteriores deixaram. Use as setas para reordenar.\n"
            "- **Nada é definitivo:** remova ou reordene nós quando quiser; o app refaz tudo a partir da base original.\n"
            "- **Você decide:** o app mostra o efeito de cada nó nos números, mas não diz se a decisão é certa. "
            "Compare com o que você anotou no diagnóstico e com o que a missão pede.\n"
            "- **Blocos prontos** resolvem situações comuns desta base; **blocos personalizados** deixam você "
            "montar qualquer passo simples. Todos mostram o código pandas executado."
        )
    if (st.session_state.notas_diag or "").strip():
        with st.expander("Suas anotações do diagnóstico", icon=":material/edit_note:"):
            st.text(st.session_state.notas_diag)
    mostrar_avisos()

    esquerda, direita = st.columns([5, 7], gap="large")
    with esquerda:
        st.subheader("Biblioteca de nós", anchor=False)
        aba1, aba2 = st.tabs(["Blocos prontos", "Bloco personalizado"])
        with aba1:
            _catalogo(tema)
        with aba2:
            _personalizado(tema)
    with direita:
        st.subheader("Seu fluxo", anchor=False)
        _fluxo(tema)

    st.subheader("Base tratada (saída do fluxo)", anchor=False)
    tabela_amostra(df_atual(tema), altura=320)
    if st.session_state.passos:
        with st.expander("Código completo da pipeline", icon=":material/code:"):
            st.caption("Exatamente o código que o app executou, na ordem do fluxo.")
            st.code(ex.codigo_completo(tema, st.session_state.passos, st.session_state.blocos), language="python", wrap_lines=True)

    rodape(pode_avancar=bool(st.session_state.passos), motivo="Adicione pelo menos um nó ao fluxo para avançar.")
