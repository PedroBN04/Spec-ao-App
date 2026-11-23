import streamlit as st

from core import checklist as ck
from core import spec_builder as sb
from ui.components import carregar_base, df_atual, por_que_importa, rodape, tema_atual

PREFIXO = "w_spec_"


def estado_spec() -> sb.EstadoSpec:
    """Estado completo usado para montar a SPEC (também usado na etapa 6)."""
    tema = tema_atual()
    if not st.session_state.spec:
        st.session_state.spec = sb.respostas_iniciais(tema)
    df = df_atual(tema)
    checks = ck.avaliar(tema, carregar_base(tema), df, st.session_state.passos)
    return sb.EstadoSpec(
        tema=tema,
        equipe=st.session_state.equipe,
        df=df,
        passos=list(st.session_state.passos),
        resultados=st.session_state.resultados,
        checks=checks,
        justificativas=st.session_state.justificativas,
        respostas=st.session_state.spec,
    )


# ---------------------------------------------------------------------------
# Widgets ligados a st.session_state.spec
# ---------------------------------------------------------------------------


def _k(campo: str) -> str:
    chave = PREFIXO + campo
    if chave not in st.session_state:
        st.session_state[chave] = st.session_state.spec.get(campo)
    return chave


def _salvar(campo: str) -> None:
    st.session_state.spec = {**st.session_state.spec, campo: st.session_state[PREFIXO + campo]}


def _texto(campo: str, rotulo: str, area: bool = False, **kw) -> None:
    widget = st.text_area if area else st.text_input
    widget(rotulo, key=_k(campo), on_change=_salvar, args=(campo,), **kw)
    _salvar(campo)


def _checkboxes(campo: str, opcoes: list[str], rotulo: str) -> None:
    st.markdown(rotulo)
    marcados = set(st.session_state.spec.get(campo, []))
    escolhidos = []
    for i, opcao in enumerate(opcoes):
        chave = f"{PREFIXO}{campo}_{i}"
        if chave not in st.session_state:
            st.session_state[chave] = opcao in marcados
        if st.checkbox(opcao, key=chave):
            escolhidos.append(opcao)
    st.session_state.spec = {**st.session_state.spec, campo: escolhidos}


# ---------------------------------------------------------------------------
# Passos
# ---------------------------------------------------------------------------


def _passo_problema(estado: sb.EstadoSpec) -> None:
    _texto(
        "nome_solucao",
        "Nome da solução (opcional)",
        help="Aparece no título da SPEC. Ex.: \"Radar de Cancelamentos\".",
    )
    _texto("problema", "Problema *", area=True, height=110)
    st.radio(
        "Usuário principal *",
        options=list(sb.USUARIOS),
        format_func=sb.USUARIOS.get,
        key=_k("usuario"),
        on_change=_salvar,
        args=("usuario",),
        horizontal=True,
        help="Quem vai usar a aplicação no dia a dia.",
    )
    _salvar("usuario")
    if st.session_state.spec.get("usuario") == "outro":
        _texto("usuario_outro", "Qual usuário? *", placeholder="Ex.: equipe de marketing")


def _passo_escopo(estado: sb.EstadoSpec) -> None:
    _checkboxes("proposta_itens", estado.tema.proposta_inicial, "**Itens da proposta inicial \\*** (desmarque o que não vai entrar)")
    _checkboxes("aprofundamentos", estado.tema.aprofundamentos, "**Aprofundamentos escolhidos** (opcional)")
    _texto(
        "fora_escopo",
        "Fora do escopo (um item por linha)",
        area=True,
        height=90,
        placeholder="Ex.: login de usuários\nprevisão com inteligência artificial",
    )


def _passo_dados(estado: sb.EstadoSpec) -> None:
    st.caption(
        f"Gerado automaticamente da sua base tratada: {len(estado.df):,} linhas e {estado.df.shape[1]} colunas. ".replace(",", ".")
        + "Você só pode editar o **significado**; nome, tipo e valores reais vêm dos dados."
    )
    origem = sb.origem_das_colunas(estado.tema, estado.passos, estado.resultados)
    transformadas = sb.transformacoes(estado.passos, estado.resultados)
    salvos = st.session_state.spec.get("significados", {})
    tabela = sb.tabela_dados(estado.tema, estado.df, salvos, origem, transformadas)
    chave = f"{PREFIXO}dados_{abs(hash(tuple(tabela['Coluna']))) % 10**8}"
    editada = st.data_editor(
        tabela,
        key=chave,
        hide_index=True,
        width="stretch",
        height=min(38 * (len(tabela) + 1), 420),
        disabled=["Coluna", "Tipo", "Valores reais"],
        column_order=["Coluna", "Significado", "Tipo", "Valores reais"],
        column_config={
            "Coluna": st.column_config.TextColumn("Coluna", width="medium"),
            "Tipo": st.column_config.TextColumn("Tipo", width="small"),
            "Valores reais": st.column_config.TextColumn("Valores reais", width="medium"),
            "Significado": st.column_config.TextColumn("Significado (editável)", width="large"),
        },
    )
    # Guarda só o que a equipe mudou; o resto continua vindo do padrão (que acompanha a base).
    padrao = sb.tabela_dados(estado.tema, estado.df, {}, origem, transformadas).set_index("Coluna")["Significado"]
    mudados = {
        col: sig for col, sig in zip(editada["Coluna"], editada["Significado"].fillna("")) if sig != padrao.get(col, "")
    }
    st.session_state.spec = {**st.session_state.spec, "significados": {**salvos, **mudados}}
    vazios = int((editada["Significado"].fillna("").str.strip() == "").sum())
    if vazios:
        st.warning(f"{vazios} coluna(s) sem significado. Preencha para o agente não ter que adivinhar.")


def _passo_lista(estado: sb.EstadoSpec, campo: str, rotulo: str, exemplo: str) -> None:
    _texto(campo, f"{rotulo} * (um item por linha)", area=True, height=180, placeholder=exemplo)
    n = len(sb.linhas(st.session_state.spec.get(campo)))
    st.caption(f"{n} item(ns). Já vem com sugestões do desafio: edite, apague ou acrescente linhas.")
    ausentes = sb.colunas_citadas_ausentes(st.session_state.spec.get(campo) or "", estado.tema, estado.df)
    if ausentes:
        st.warning(
            "Este texto cita coluna(s) que **não existem** na sua base tratada: "
            + ", ".join(f"`{c}`" for c in ausentes)
            + ". O agente não vai conseguir cumprir. Ajuste o texto ou volte ao tratamento."
        )


def _passo_funcionalidades(estado):
    _passo_lista(estado, "funcionalidades", "Funcionalidades", "Ex.: Filtrar o painel por tipo de contrato")


def _passo_regras(estado):
    _passo_lista(estado, "regras_negocio", "Regras de negócio", "Ex.: Taxa = casos com alvo 1 ÷ total do filtro")


def _passo_arquitetura(estado):
    _texto("stack", "Stack (tecnologias)", help="Padrão: Python + Streamlit + pandas + plotly.")
    _checkboxes("restricoes", sb.RESTRICOES_PADRAO, "**Restrições**")


def _passo_criterios(estado):
    _passo_lista(
        estado,
        "criterios_aceitacao",
        "Critérios de aceitação",
        "Ex.: Dado que nenhum filtro está ativo, quando abro o painel, então vejo a taxa geral",
    )
    _texto("metrica_sucesso", "Métrica de sucesso do negócio", help="Como o negócio vai saber que a solução ajudou.")


def _passo_apresentacao(estado):
    _texto("formato", "Formato")
    _texto("roteiro", "Roteiro", area=True, height=90)


DESENHO = (
    _passo_problema,
    _passo_escopo,
    _passo_dados,
    _passo_funcionalidades,
    _passo_regras,
    _passo_arquitetura,
    _passo_criterios,
    _passo_apresentacao,
)


def _ir_passo(i: int) -> None:
    st.session_state.spec_passo = max(0, min(i, len(sb.PASSOS) - 1))


def _alternar_texto() -> None:
    st.session_state.spec_como_texto = not st.session_state.get("spec_como_texto", False)


def render() -> None:
    tema = tema_atual()
    if tema is None:
        st.warning("Escolha um desafio na etapa 1 antes de escrever a SPEC.")
        rodape(pode_avancar=False)
        return

    estado = estado_spec()
    st.header("5. Assistente da SPEC")
    st.caption(
        "Responda os 8 passos. As sugestões já vêm preenchidas a partir do desafio: leia, ajuste e complete. "
        "À direita você vê a SPEC.md sendo montada. Depois de digitar, clique fora do campo "
        "(ou tecle Ctrl+Enter) para a prévia atualizar."
    )

    i = st.session_state.spec_passo
    passo = sb.PASSOS[i]
    esquerda, direita = st.columns([11, 9], gap="large")
    with esquerda:
        faltando = sb.faltando_por_passo(st.session_state.spec)
        marcas = " · ".join(
            (f"**:blue[{n + 1}]**" if n == i else (f"{n + 1}⚠️" if n in faltando else f"{n + 1}✓"))
            for n in range(len(sb.PASSOS))
        )
        st.markdown(f"Passo {i + 1} de {len(sb.PASSOS)} — {marcas}")
        with st.container(border=True):
            st.subheader(passo.titulo)
            st.markdown(f"**{passo.pergunta}**")
            DESENHO[i](estado)
        por_que_importa(passo.porque)
        a, b = st.columns(2)
        a.button("◀ Passo anterior", on_click=_ir_passo, args=(i - 1,), disabled=i == 0, width="stretch")
        b.button(
            "Próximo passo ▶",
            on_click=_ir_passo,
            args=(i + 1,),
            disabled=i == len(sb.PASSOS) - 1,
            type="primary",
            width="stretch",
        )

    estado = estado_spec()  # respostas atualizadas pelos widgets acima
    texto = sb.montar_spec(estado)
    with direita:
        topo, botao = st.columns([3, 2])
        topo.markdown("**👀 Prévia da SPEC.md**")
        como_texto = st.session_state.get("spec_como_texto", False)
        botao.button("Ver formatado" if como_texto else "Ver como texto", on_click=_alternar_texto, width="stretch")
        with st.container(height=640, border=True):
            if como_texto:
                st.code(texto, language="markdown")
            else:
                st.markdown(texto)

    faltando = sb.faltando_por_passo(st.session_state.spec)
    motivo = ""
    if faltando:
        itens = "; ".join(f"passo {n + 1}: {', '.join(c)}" for n, c in sorted(faltando.items()))
        motivo = f"Preencha os campos obrigatórios (*) — {itens}."
    rodape(pode_avancar=not faltando, motivo=motivo)
