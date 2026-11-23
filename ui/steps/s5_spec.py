"""Etapa 5 — SPEC (v2): a equipe escreve a especificação; o app só guia e monta o documento."""

import streamlit as st

from core import spec_builder as sb
from ui.components import cabecalho, df_atual, dica, rodape, tema_atual

PREFIXO = "w_spec_"


def estado_spec() -> sb.EstadoSpec:
    """Estado completo usado para montar a SPEC (também usado na etapa 6)."""
    tema = tema_atual()
    if not st.session_state.spec:
        st.session_state.spec = sb.respostas_iniciais(tema)
    return sb.EstadoSpec(
        tema=tema,
        equipe=st.session_state.equipe,
        df=df_atual(tema),
        passos=list(st.session_state.passos),
        blocos=st.session_state.blocos,
        resultados=st.session_state.resultados,
        respostas=st.session_state.spec,
        notas_revisao=st.session_state.get("notas_revisao", ""),
    )


# ---------------------------------------------------------------------------
# Widgets ligados a st.session_state.spec
# ---------------------------------------------------------------------------


def _guardar(campo: str, valor) -> None:
    st.session_state.spec = {**st.session_state.spec, campo: valor}


def _texto(campo: str, rotulo: str, area: bool = False, **kw) -> None:
    chave = PREFIXO + campo
    if chave not in st.session_state:
        st.session_state[chave] = st.session_state.spec.get(campo) or ""
    (st.text_area if area else st.text_input)(rotulo, key=chave, **kw)
    _guardar(campo, st.session_state[chave])


def _checkboxes(campo: str, opcoes: list[str], rotulo: str) -> None:
    st.markdown(rotulo)
    marcados = set(st.session_state.spec.get(campo) or [])
    escolhidos = [op for i, op in enumerate(opcoes)
                  if st.checkbox(op, value=op in marcados, key=f"{PREFIXO}{campo}_{i}")]
    _guardar(campo, escolhidos)


def _aviso_colunas(estado: sb.EstadoSpec, campo: str) -> None:
    ausentes = sb.colunas_citadas_ausentes(st.session_state.spec.get(campo) or "", estado.tema, estado.df)
    if ausentes:
        st.warning(
            "Este texto cita coluna(s) que não existem na sua base tratada: "
            + ", ".join(f"`{c}`" for c in ausentes) + ". Ajuste o texto ou o fluxo.",
            icon=":material/warning:",
        )


# ---------------------------------------------------------------------------
# Passos
# ---------------------------------------------------------------------------


def _p_problema(estado):
    _texto("nome_solucao", "Nome da solução (opcional)", placeholder="Ex.: Radar de Cancelamentos")
    _texto("problema", "Problema *", area=True, height=120)
    atual = st.session_state.spec.get("usuario")
    opcoes = list(sb.USUARIOS)
    escolha = st.radio("Usuário principal *", opcoes, format_func=sb.USUARIOS.get, horizontal=True,
                       index=opcoes.index(atual) if atual in opcoes else None, key=f"{PREFIXO}usuario")
    _guardar("usuario", escolha)
    if escolha == "outro":
        _texto("usuario_outro", "Qual usuário? *", placeholder="Ex.: equipe de marketing")


def _p_escopo(estado):
    pedidos = list(estado.tema.proposta_inicial) + list(estado.tema.aprofundamentos)
    _checkboxes("escopo_pedido", pedidos, "**Dos pedidos da área cliente, o que entra?** (marque o que você vai atender)")
    _texto("escopo_proprio", "Itens seus, além do pedido (um por linha)", area=True, height=90)
    _texto("fora_escopo", "Fora do escopo (um por linha)", area=True, height=90)


def _p_dados(estado):
    st.caption(
        f"Gerado da sua base tratada: {len(estado.df):,} linhas e {estado.df.shape[1]} colunas. ".replace(",", ".")
        + "Nome, tipo e valores reais vêm dos dados; o significado vem da documentação da base e pode ser editado."
    )
    uids = [p if isinstance(p, str) else p["uid"] for p in estado.passos]
    origem = sb.origem_das_colunas(uids, estado.resultados)
    transf = sb.transformacoes(uids, estado.resultados)
    salvos = st.session_state.spec.get("significados", {})
    tabela = sb.tabela_dados(estado.tema, estado.df, salvos, origem, transf, estado.blocos)
    editada = st.data_editor(
        tabela,
        key=f"{PREFIXO}dados_{abs(hash(tuple(tabela['Coluna']))) % 10**8}",
        hide_index=True, width="stretch", height=min(38 * (len(tabela) + 1), 380),
        disabled=["Coluna", "Tipo", "Valores reais"],
        column_order=["Coluna", "Significado", "Tipo", "Valores reais"],
        column_config={"Significado": st.column_config.TextColumn("Significado (editável)", width="large")},
    )
    padrao = sb.tabela_dados(estado.tema, estado.df, {}, origem, transf, estado.blocos).set_index("Coluna")["Significado"]
    mudados = {c: s for c, s in zip(editada["Coluna"], editada["Significado"].fillna("")) if s != padrao.get(c, "")}
    _guardar("significados", {**salvos, **mudados})
    if (st.session_state.notas_diag or "").strip():
        with st.expander("Suas anotações do diagnóstico", icon=":material/edit_note:"):
            st.text(st.session_state.notas_diag)
    _texto("cuidados", "Cuidados com os dados (um por linha)", area=True, height=110)


def _p_lista(estado, campo, rotulo):
    _texto(campo, f"{rotulo} * (um item por linha)", area=True, height=170)
    st.caption(f"{len(sb.linhas(st.session_state.spec.get(campo)))} item(ns).")
    _aviso_colunas(estado, campo)


def _p_funcionalidades(estado):
    _p_lista(estado, "funcionalidades", "Funcionalidades")


def _p_regras(estado):
    _p_lista(estado, "regras_negocio", "Regras de negócio")


def _p_arquitetura(estado):
    _texto("stack", "Stack (tecnologias)", placeholder=f"Ex.: {sb.STACK_EXEMPLO}")
    _checkboxes("restricoes", sb.RESTRICOES, "**Restrições para o agente** (marque as que valem)")


def _p_criterios(estado):
    _p_lista(estado, "criterios_aceitacao", "Critérios de aceitação")
    st.caption(sb.numeros_de_referencia(estado.tema, estado.df))
    _texto("metrica_sucesso", "Métrica de sucesso do negócio")


def _p_apresentacao(estado):
    _texto("formato", "Formato", placeholder="Ex.: pitch de 3 minutos")
    _texto("roteiro", "Roteiro", area=True, height=90)


DESENHO = (_p_problema, _p_escopo, _p_dados, _p_funcionalidades, _p_regras, _p_arquitetura, _p_criterios,
           _p_apresentacao)


def _ir_passo(i: int) -> None:
    st.session_state.spec_passo = max(0, min(i, len(sb.PASSOS) - 1))


CAMPOS_TEXTO = ("nome_solucao", "problema", "usuario_outro", "escopo_proprio", "fora_escopo", "cuidados",
                "funcionalidades", "regras_negocio", "stack", "criterios_aceitacao", "metrica_sucesso", "formato",
                "roteiro", "usuario")


def _sincronizar() -> None:
    """Leva para as respostas o que já foi digitado, antes de desenhar a navegação (marcadores em dia)."""
    novos = {c: st.session_state[PREFIXO + c] for c in CAMPOS_TEXTO if PREFIXO + c in st.session_state}
    if novos:
        st.session_state.spec = {**st.session_state.spec, **novos}


def _navegar(chave: str) -> None:
    escolhido = st.session_state.get(chave)
    if escolhido is not None:
        _ir_passo(escolhido)


def _alternar_texto() -> None:
    st.session_state.spec_como_texto = not st.session_state.get("spec_como_texto", False)


def render() -> None:
    tema = tema_atual()
    if tema is None:
        st.warning("Escolha uma missão antes de escrever a SPEC.")
        rodape(pode_avancar=False)
        return

    estado = estado_spec()
    _sincronizar()
    cabecalho(
        "Escreva a SPEC",
        "A especificação é sua: em cada passo há perguntas para guiar o raciocínio. Os campos começam vazios. "
        "À direita, o documento vai sendo montado.",
    )
    i = st.session_state.spec_passo
    passo = sb.PASSOS[i]
    esquerda, direita = st.columns([11, 9], gap="large")
    with esquerda:
        faltando = sb.faltando_por_passo(st.session_state.spec)
        nomes = [p.titulo.split(". ", 1)[1] for p in sb.PASSOS]
        st.segmented_control(
            "Passos da SPEC", options=list(range(len(sb.PASSOS))), default=i, key=f"spec_nav_{i}",
            format_func=lambda n: f"{n + 1}" + (" •" if n in faltando else ""), label_visibility="collapsed",
            on_change=_navegar, args=(f"spec_nav_{i}",),
        )
        st.caption("• = campo obrigatório ainda vazio")
        with st.container(border=True):
            st.subheader(passo.titulo, anchor=False)
            st.markdown(f"**{passo.pergunta}**")
            st.markdown("\n".join(f"- {g}" for g in passo.guia))
            DESENHO[i](estado)
            with st.expander("Travou? Veja um exemplo de outro contexto (biblioteca municipal)", icon=":material/lightbulb:"):
                st.text(passo.exemplo)
        dica(passo.porque)
        a, b = st.columns(2)
        a.button(f"Anterior: {nomes[i - 1]}" if i else "Anterior", icon=":material/chevron_left:",
                 on_click=_ir_passo, args=(i - 1,), disabled=i == 0, width="stretch")
        b.button(f"Próximo: {nomes[i + 1]}" if i < len(nomes) - 1 else "Próximo", icon=":material/chevron_right:",
                 icon_position="right", on_click=_ir_passo, args=(i + 1,), disabled=i == len(sb.PASSOS) - 1,
                 type="primary", width="stretch")

    texto = sb.montar_spec(estado_spec())
    with direita:
        topo, botao = st.columns([3, 2], vertical_alignment="center")
        topo.markdown("**Prévia da SPEC.md**")
        como_texto = st.session_state.get("spec_como_texto", False)
        botao.button("Ver formatado" if como_texto else "Ver como texto", on_click=_alternar_texto, width="stretch",
                     icon=":material/article:" if como_texto else ":material/code:")
        with st.container(height=680, border=True, key="previa"):
            if como_texto:
                st.code(texto, language="markdown")
            else:
                st.markdown(texto)

    faltando = sb.faltando_por_passo(st.session_state.spec)
    motivo = ""
    if faltando:
        motivo = "Campos obrigatórios vazios — " + "; ".join(
            f"passo {n + 1}: {', '.join(c)}" for n, c in sorted(faltando.items()))
    rodape(pode_avancar=not faltando, motivo=motivo)
