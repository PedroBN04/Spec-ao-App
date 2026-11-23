"""Assistente da SPEC (etapa 5) e montagem da SPEC.md (seções 9 e 9.1 da APP_SPEC).

Funções puras: recebem o estado como dicionário e não dependem do Streamlit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from core import checklist as ck
from core.diagnostics import tipo_amigavel
from core.models import StepResult, Theme

USUARIOS = {"gestor": "Gestor(a)", "atendente": "Atendente", "analista": "Analista", "outro": "Outro"}

STACK_PADRAO = "Python + Streamlit + pandas + plotly"
RESTRICOES_PADRAO = [
    "Usar só o CSV fornecido (`dados_tratados.csv`)",
    "Não inventar dados",
    "Não usar APIs externas",
    "Não alterar o CSV",
    "Código em um único `app.py`, se possível",
]
FORMATO_PADRAO = "Pitch de 3 minutos"
ROTEIRO_PADRAO = "Problema → dados → decisão de tratamento → demo → impacto"


@dataclass(frozen=True)
class Passo:
    titulo: str
    pergunta: str
    porque: str


PASSOS = (
    Passo(
        "1. Problema",
        "Que problema sua solução resolve, e para quem?",
        "Um agente de código sem problema claro constrói \"qualquer coisa que funcione\". "
        "O problema é a bússola de todas as decisões.",
    ),
    Passo(
        "2. Objetivo e escopo",
        "O que entra na primeira versão?",
        "Escopo explícito evita que o agente gaste tempo em funcionalidades que ninguém pediu. "
        "Dizer o que NÃO fazer é tão importante quanto o que fazer.",
    ),
    Passo(
        "3. Dados",
        "Confirme o dicionário das colunas do seu CSV.",
        "O agente só conhece seus dados pelo que você descreve. Colunas sem significado viram suposições — "
        "e suposições viram alucinações.",
    ),
    Passo(
        "4. Funcionalidades",
        "O que o usuário consegue fazer na aplicação?",
        "Cada funcionalidade vira uma tarefa verificável para o agente.",
    ),
    Passo(
        "5. Regras de negócio",
        "Quais regras a solução deve respeitar?",
        "Regras escritas impedem que o agente invente fórmulas. É aqui que o resultado fica correto, "
        "não só bonito.",
    ),
    Passo(
        "6. Arquitetura e restrições",
        "Como a solução deve ser construída?",
        "Restrições reduzem o espaço de erro do agente. Sem elas, ele pode buscar dados na internet ou criar "
        "uma estrutura complexa demais para 1 hora.",
    ),
    Passo(
        "7. Critérios de aceitação e métricas",
        "Como saberemos que ficou pronto e correto?",
        "Critério verificável é o que permite conferir o trabalho do agente. \"Ficar bonito\" não é "
        "verificável; \"o painel mostra a taxa geral de 26,5% sem filtros\" é.",
    ),
    Passo(
        "8. Apresentação",
        "Como a equipe vai apresentar?",
        "A apresentação é parte da entrega. Planejar o roteiro agora orienta o que a aplicação precisa mostrar.",
    ),
)


# ---------------------------------------------------------------------------
# Respostas
# ---------------------------------------------------------------------------


def respostas_iniciais(tema: Theme) -> dict:
    d = tema.spec_defaults
    return {
        "nome_solucao": f"Painel — {tema.nome}",
        "problema": d.get("problema", ""),
        "usuario": d.get("usuario", "gestor"),
        "usuario_outro": "",
        "proposta_itens": list(tema.proposta_inicial),
        "aprofundamentos": [],
        "fora_escopo": "",
        "significados": {},
        "funcionalidades": "\n".join(d.get("funcionalidades", [])),
        "regras_negocio": "\n".join(d.get("regras_negocio", [])),
        "stack": STACK_PADRAO,
        "restricoes": list(RESTRICOES_PADRAO),
        "criterios_aceitacao": "\n".join(d.get("criterios_aceitacao", [])),
        "metrica_sucesso": d.get("metrica_sucesso", ""),
        "formato": FORMATO_PADRAO,
        "roteiro": ROTEIRO_PADRAO,
    }


def linhas(texto: str | list | None) -> list[str]:
    """Lista a partir de texto com um item por linha (ignora linhas vazias e marcadores)."""
    if isinstance(texto, list):
        itens = texto
    else:
        itens = (texto or "").splitlines()
    limpos = []
    for item in itens:
        item = str(item).strip().lstrip("-*•").strip()
        if item:
            limpos.append(item)
    return limpos


def usuario_texto(r: dict) -> str:
    if r.get("usuario") == "outro":
        return (r.get("usuario_outro") or "").strip()
    return USUARIOS.get(r.get("usuario", ""), "")


def faltando_por_passo(r: dict) -> dict[int, list[str]]:
    """Campos obrigatórios vazios, por índice de passo (0 a 7)."""
    falta: dict[int, list[str]] = {}

    def add(i: int, campo: str) -> None:
        falta.setdefault(i, []).append(campo)

    if not (r.get("problema") or "").strip():
        add(0, "Problema")
    if not usuario_texto(r):
        add(0, "Usuário principal")
    if not r.get("proposta_itens"):
        add(1, "Itens da proposta inicial (marque pelo menos 1)")
    if not linhas(r.get("funcionalidades")):
        add(3, "Funcionalidades (pelo menos 1)")
    if not linhas(r.get("regras_negocio")):
        add(4, "Regras de negócio (pelo menos 1)")
    if not linhas(r.get("criterios_aceitacao")):
        add(6, "Critérios de aceitação (pelo menos 1)")
    return falta


# ---------------------------------------------------------------------------
# Dicionário de dados (sempre do DataFrame final real)
# ---------------------------------------------------------------------------


def origem_das_colunas(tema: Theme, passos: list[str], resultados: dict[str, StepResult]) -> dict[str, str]:
    """Coluna -> id do bloco que a criou (o último que criou vale)."""
    origem: dict[str, str] = {}
    for bid in passos:
        r = resultados.get(bid)
        if r:
            for c in r.colunas_criadas:
                origem[c] = bid
    return origem


def transformacoes(passos: list[str], resultados: dict[str, StepResult]) -> dict[str, list[str]]:
    """Coluna -> blocos que mudaram o tipo dela (ex.: Churn texto -> 0/1 pelo T07)."""
    mudou: dict[str, list[str]] = {}
    for bid in passos:
        r = resultados.get(bid)
        if r:
            for c in r.tipos_alterados:
                mudou.setdefault(c, []).append(bid)
    return mudou


def significado_padrao(
    tema: Theme, coluna: str, origem: dict[str, str], transformadas: dict[str, list[str]] | None = None
) -> str:
    if coluna in tema.dicionario:
        texto = tema.dicionario[coluna]
    elif coluna in tema.dicionario_extra:
        texto = tema.dicionario_extra[coluna]
    elif coluna in origem:
        bloco = tema.bloco(origem[coluna])
        return f"Criada pelo bloco {bloco.id}: {bloco.titulo.replace('`', '')}"
    else:
        return ""
    blocos = (transformadas or {}).get(coluna, [])
    if blocos:
        nomes = "; ".join(f"{b} ({tema.bloco(b).titulo.replace('`', '')})" for b in blocos)
        texto += f". ATENÇÃO: valores convertidos pelo bloco {nomes}"
    return texto


def _fmt_num(v) -> str:
    if pd.isna(v):
        return ""
    if float(v).is_integer():
        return f"{int(v)}"
    return f"{v:.2f}"


def valores_coluna(serie: pd.Series, limite: int = 12) -> str:
    """Resumo dos valores REAIS da coluna, calculado do DataFrame final."""
    nao_vazios = serie.dropna()
    vazios = len(serie) - len(nao_vazios)
    sufixo = f"; {vazios} vazio(s)" if vazios else ""
    if nao_vazios.empty:
        return "todos vazios"
    if pd.api.types.is_bool_dtype(serie):
        return ", ".join(sorted(map(str, nao_vazios.unique()))) + sufixo
    if pd.api.types.is_datetime64_any_dtype(serie):
        return f"{nao_vazios.min():%Y-%m-%d} a {nao_vazios.max():%Y-%m-%d}{sufixo}"
    distintos = nao_vazios.unique()
    if pd.api.types.is_numeric_dtype(serie):
        if len(distintos) <= 2:
            return ", ".join(_fmt_num(v) for v in sorted(distintos)) + sufixo
        return f"{_fmt_num(nao_vazios.min())} a {_fmt_num(nao_vazios.max())}{sufixo}"
    if len(distintos) <= limite:
        return ", ".join(sorted(map(str, distintos))) + sufixo
    exemplos = ", ".join(map(str, nao_vazios.value_counts().index[:3]))
    return f"{len(distintos)} valores distintos (ex.: {exemplos}){sufixo}"


def numeros_de_referencia(tema: Theme, df: pd.DataFrame) -> str:
    """Números calculados do CSV exportado, para o agente conferir os critérios."""
    partes = [f"{len(df)} linhas no total"]
    for alvo in (*tema.alvos_aceitos, tema.alvo):
        if alvo not in df.columns:
            continue
        serie = df[alvo]
        if pd.api.types.is_numeric_dtype(serie) and set(serie.dropna().unique()) <= {0, 1}:
            taxa = serie.mean()
            partes.append(f"média de `{alvo}` (taxa geral) = {taxa:.1%}".replace(".", ","))
        elif set(serie.dropna().astype(str).unique()) <= {"Yes", "No"}:
            taxa = (serie == "Yes").mean()
            partes.append(f"proporção de `{alvo}` = \"Yes\": {taxa:.1%}".replace(".", ","))
        break
    return "Números de referência (calculados do `dados_tratados.csv`, sem filtros): " + "; ".join(partes) + "."


def tabela_dados(
    tema: Theme,
    df: pd.DataFrame,
    significados: dict[str, str],
    origem: dict[str, str],
    transformadas: dict[str, list[str]] | None = None,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Coluna": [str(c) for c in df.columns],
            "Tipo": [tipo_amigavel(df[c].dtype) for c in df.columns],
            "Valores reais": [valores_coluna(df[c]) for c in df.columns],
            "Significado": [
                significados.get(str(c)) or significado_padrao(tema, str(c), origem, transformadas)
                for c in df.columns
            ],
        }
    )


def colunas_citadas_ausentes(texto: str, tema: Theme, df: pd.DataFrame) -> list[str]:
    """Colunas conhecidas do tema que aparecem no texto mas não existem na base final."""
    conhecidas = set(tema.dicionario) | set(tema.dicionario_extra)
    ausentes = []
    for col in sorted(conhecidas - set(map(str, df.columns))):
        if re.search(rf"(?<![\w-]){re.escape(col)}(?![\w-])", texto or ""):
            ausentes.append(col)
    return ausentes


# ---------------------------------------------------------------------------
# Montagem da SPEC.md (template 9.1). Seções vazias não aparecem.
# ---------------------------------------------------------------------------


@dataclass
class EstadoSpec:
    tema: Theme
    equipe: str
    df: pd.DataFrame
    passos: list[str]
    resultados: dict[str, StepResult]
    checks: list[ck.ResultadoCheck]
    justificativas: dict
    respostas: dict
    data: date = field(default_factory=date.today)


def _celula(texto: str) -> str:
    return str(texto).replace("|", "\\|").replace("\n", " ")


def _resumo(feedback: str) -> str:
    """Feedback do bloco sem marcação. Usamos o texto inteiro (são 1 a 3 frases): a primeira frase
    sozinha pode enganar (ex.: N06 começa com "Com N04, ...")."""
    return " ".join(feedback.replace("**", "").split())


def _coluna_alvo(e: EstadoSpec) -> str:
    for nome in (*e.tema.alvos_aceitos, e.tema.alvo):
        if nome in e.df.columns:
            return nome
    return f"{e.tema.alvo} (ausente na base tratada)"


def montar_spec(e: EstadoSpec) -> str:
    r = e.respostas
    t = e.tema
    out: list[str] = []

    def sec(titulo: str, corpo: list[str]) -> None:
        corpo = [c for c in corpo if c is not None]
        if any(c.strip() for c in corpo):
            out.append(titulo)
            out.extend(corpo)
            out.append("")

    nome = (r.get("nome_solucao") or "").strip() or t.nome
    out.append(f"# SPEC — {nome}")
    out.append(f"Equipe: {e.equipe.strip()} · Desafio: {t.nome} · Gerado em {e.data.strftime('%d/%m/%Y')}")
    out.append("")

    # 1
    corpo1 = []
    if (r.get("problema") or "").strip():
        corpo1.append(r["problema"].strip())
    if usuario_texto(r):
        corpo1.append(f"Usuário principal: {usuario_texto(r)}")
    sec("## 1. Contexto e problema", ["  \n".join(corpo1)] if corpo1 else [])

    # 2
    entra = [f"- {i}" for i in r.get("proposta_itens", [])] + [f"- {i}" for i in r.get("aprofundamentos", [])]
    fora = [f"- {i}" for i in linhas(r.get("fora_escopo"))]
    corpo2 = []
    if entra:
        corpo2 += ["### Entra nesta versão", *entra]
    if fora:
        corpo2 += ["### Fora do escopo", *fora]
    sec("## 2. Objetivo e escopo", corpo2)

    # 3 — sempre do DataFrame real
    origem = origem_das_colunas(t, e.passos, e.resultados)
    tabela = tabela_dados(t, e.df, r.get("significados", {}), origem, transformacoes(e.passos, e.resultados))
    out.append("## 3. Dados")
    out.append(
        f"Arquivo: `dados_tratados.csv` — {len(e.df)} linhas, {e.df.shape[1]} colunas. Alvo: `{_coluna_alvo(e)}`."
    )
    out.append("")
    out.append("| Coluna | Tipo | Valores reais | Significado |")
    out.append("| --- | --- | --- | --- |")
    for _, linha in tabela.iterrows():
        out.append(
            f"| `{_celula(linha['Coluna'])}` | {linha['Tipo']} | {_celula(linha['Valores reais'])} "
            f"| {_celula(linha['Significado'])} |"
        )
    out.append("")
    out.append(
        "Os **valores reais** foram calculados do CSV exportado e valem mais que o significado "
        "(que descreve a coluna original)."
    )
    out.append("")

    tratamentos = [
        f"{i}. {t.bloco(b).titulo} — {ck.ROTULO_CATEGORIA[t.bloco(b).categoria]} — {_resumo(t.bloco(b).feedback)}"
        for i, b in enumerate(e.passos, start=1)
    ]
    sec("### 3.1 Tratamentos já aplicados (não refazer)", tratamentos)

    decisoes = []
    for res in e.checks:
        if not res.pendente:
            continue
        d = e.justificativas.get(res.check.id, {})
        if d.get("decisao") == "manter" and ck.justificativa_valida(d.get("texto")):
            nivel = "Erro" if res.check.nivel == "erro" else "Alerta"
            decisoes.append(
                f"- **{nivel} mantido — {res.check.titulo.replace('`', '')}:** {res.mensagem} "
                f"Justificativa da equipe: {d['texto'].strip()}"
            )
    sec("### 3.2 Decisões conscientes e justificativas", decisoes)

    cuidados = []
    vazamento = ck.colunas_vazamento_presentes(t, e.df)
    if vazamento:
        cuidados.append("- Não usar como entrada de previsão: " + ", ".join(f"`{c}`" for c in vazamento))
    cuidados += [f"- {texto}" for coluna, texto in t.observacoes if coluna in e.df.columns]
    sec("### 3.3 Cuidados com os dados", cuidados)

    # 4 a 8
    sec("## 4. Funcionalidades", [f"{i}. {f}" for i, f in enumerate(linhas(r.get("funcionalidades")), start=1)])
    sec("## 5. Regras de negócio", [f"- {x}" for x in linhas(r.get("regras_negocio"))])
    arq = []
    if (r.get("stack") or "").strip():
        arq.append(f"- Stack: {r['stack'].strip()}")
    arq += [f"- {x}" for x in r.get("restricoes", [])]
    sec("## 6. Arquitetura e restrições", arq)
    crit = [f"- [ ] {x}" for x in linhas(r.get("criterios_aceitacao"))]
    if crit:
        crit.append(f"\n{numeros_de_referencia(t, e.df)}")
    if (r.get("metrica_sucesso") or "").strip():
        crit.append(f"\nMétrica de sucesso: {r['metrica_sucesso'].strip()}")
    sec("## 7. Critérios de aceitação", crit)
    apres = []
    if (r.get("formato") or "").strip():
        apres.append(f"Formato: {r['formato'].strip()}")
    if (r.get("roteiro") or "").strip():
        apres.append(f"Roteiro: {r['roteiro'].strip()}")
    sec("## 8. Apresentação", ["  \n".join(apres)] if apres else [])

    out.append("## 9. Instruções para o agente de código")
    out.append("1. Leia esta SPEC inteira antes de escrever código.")
    out.append("2. Use somente `dados_tratados.csv`; não invente, baixe ou gere dados.")
    out.append("3. Implemente primeiro o escopo da seção 2 e confira cada critério da seção 7.")
    out.append("4. Se algo estiver ambíguo, escolha a opção mais simples e registre a suposição no README.")
    out.append("")
    return "\n".join(out)
