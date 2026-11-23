import streamlit as st

from core import checklist as ck
from ui.components import carregar_base, df_atual, ir_para, rodape, tema_atual

ICONE_NIVEL = {"erro": "❌", "alerta": "⚠️", "info": "ℹ️"}
ROTULO_NIVEL = {"erro": "Erro", "alerta": "Alerta", "info": "Informação"}
OPCOES = {"corrigir": "Vou corrigir", "manter": "Vou manter"}


def resultados_atuais():
    tema = tema_atual()
    return ck.avaliar(tema, carregar_base(tema), df_atual(tema), st.session_state.passos)


def _salvar_decisao(check_id: str) -> None:
    d = dict(st.session_state.justificativas.get(check_id, {}))
    d["decisao"] = st.session_state.get(f"w_dec_{check_id}")
    d["texto"] = st.session_state.get(f"w_just_{check_id}", d.get("texto", ""))
    st.session_state.justificativas = {**st.session_state.justificativas, check_id: d}


def _decisao(r: ck.ResultadoCheck) -> None:
    cid = r.check.id
    salvo = st.session_state.justificativas.get(cid, {})
    if f"w_dec_{cid}" not in st.session_state:
        st.session_state[f"w_dec_{cid}"] = salvo.get("decisao")
    if f"w_just_{cid}" not in st.session_state:
        st.session_state[f"w_just_{cid}"] = salvo.get("texto", "")
    st.radio(
        "O que você vai fazer?",
        options=list(OPCOES),
        format_func=OPCOES.get,
        key=f"w_dec_{cid}",
        horizontal=True,
        on_change=_salvar_decisao,
        args=(cid,),
    )
    decisao = st.session_state[f"w_dec_{cid}"]
    if decisao == "corrigir":
        st.button(
            "← Voltar ao tratamento para corrigir",
            key=f"corrigir_{cid}",
            on_click=ir_para,
            args=(3,),
        )
    elif decisao == "manter":
        st.text_area(
            "Por que vai manter? (mínimo de 15 caracteres; vai para a SPEC)",
            key=f"w_just_{cid}",
            on_change=_salvar_decisao,
            args=(cid,),
            height=80,
            placeholder="Ex.: o painel precisa mostrar os clientes novos, por isso mantive as linhas. "
            "(Clique fora do campo ou tecle Ctrl+Enter para registrar.)",
        )
        texto = st.session_state[f"w_just_{cid}"]
        if ck.justificativa_valida(texto):
            st.caption("✔️ Justificativa registrada.")
        else:
            faltam = ck.JUSTIFICATIVA_MINIMA - len(texto.strip())
            st.caption(f"✏️ Escreva mais {faltam} caractere(s) para registrar a justificativa.")
    _salvar_decisao(cid)


def render() -> None:
    tema = tema_atual()
    if tema is None:
        st.warning("Escolha um desafio na etapa 1 antes do checklist.")
        rodape(pode_avancar=False)
        return

    resultados = resultados_atuais()
    p = ck.placar(resultados)

    st.header("4. Checklist de qualidade")
    st.caption(
        "O app conferiu a sua base tratada. Para cada erro ou alerta, decida: corrigir no tratamento "
        "ou manter com uma justificativa. As justificativas vão para a SPEC."
    )
    c = st.columns(4)
    c[0].metric("✅ Passou", p["passou"], help="Itens de erro e alerta que passaram (o item informativo não conta).")
    c[1].metric("⚠️ Alertas", p["alertas"])
    c[2].metric("❌ Erros", p["erros"])
    c[3].metric(
        "Nota de qualidade",
        f"{p['nota']}/100",
        help="100 − 25 por erro − 10 por alerta (mínimo 0). Itens justificados continuam contando.",
    )

    ordem = {"erro": 0, "alerta": 1, "info": 2}
    for r in sorted(resultados, key=lambda r: (r.check.nivel == "info", r.passou, ordem[r.check.nivel])):
        with st.container(border=True):
            if r.check.nivel == "info":
                icone, situacao = ICONE_NIVEL["info"], ROTULO_NIVEL["info"]
            else:
                icone = "✅" if r.passou else ICONE_NIVEL[r.check.nivel]
                situacao = "Passou" if r.passou else ROTULO_NIVEL[r.check.nivel]
            st.markdown(f"{icone} **{r.check.titulo}** · {situacao}")
            st.write(r.mensagem)
            st.caption(f"💡 Por que isso importa? {r.check.explicacao}")
            if r.pendente:
                _decisao(r)

    faltando = ck.pendencias(resultados, st.session_state.justificativas)
    motivo = ""
    if faltando:
        motivo = (
            f"Falta resolver {len(faltando)} item(ns): corrija no tratamento ou escolha "
            "\"Vou manter\" e escreva a justificativa."
        )
    rodape(pode_avancar=not faltando, motivo=motivo)
