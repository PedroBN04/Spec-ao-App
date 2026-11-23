"""Assistente da SPEC (etapa 5) e montagem da SPEC.md — versão 2.

v2: a equipe escreve a SPEC por conta própria. Os campos começam vazios; cada passo traz perguntas-guia
e um exemplo de OUTRO domínio (uma biblioteca municipal) para quem travar. Só o que é fato dos dados
(nomes, tipos, valores reais, números de referência e os passos aplicados) é gerado automaticamente.

Funções puras: recebem o estado como dicionário/dataclass e não dependem do Streamlit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from core.diagnostics import tipo_amigavel
from core.models import Block, StepResult, Theme

USUARIOS = {"gestor": "Gestor(a)", "atendente": "Atendente", "analista": "Analista", "outro": "Outro"}

STACK_EXEMPLO = "Python + Streamlit + pandas + plotly"
RESTRICOES = [
    "Usar só o CSV fornecido (`dados_tratados.csv`)",
    "Não inventar dados",
    "Não usar APIs externas",
    "Não alterar o CSV",
    "Código em um único `app.py`, se possível",
]


@dataclass(frozen=True)
class PassoSpec:
    titulo: str
    pergunta: str
    porque: str
    guia: tuple[str, ...]  # perguntas para orientar o raciocínio
    exemplo: str  # exemplo de outro domínio (biblioteca), mostrado só se a pessoa pedir


PASSOS = (
    PassoSpec(
        "1. Problema",
        "Que problema sua solução resolve, e para quem?",
        "Um agente de código sem problema claro constrói \"qualquer coisa que funcione\". "
        "O problema é a bússola de todas as decisões.",
        (
            "Quem sente esse problema no dia a dia?",
            "O que essa pessoa não consegue saber ou decidir hoje?",
            "O que se perde (dinheiro, tempo, pessoas atendidas) por causa disso?",
        ),
        "Problema: a coordenação da Biblioteca Municipal não sabe quais leitores costumam atrasar a "
        "devolução, e os livros mais procurados ficam semanas indisponíveis.\n"
        "Usuário principal: coordenação da biblioteca.",
    ),
    PassoSpec(
        "2. Objetivo e escopo",
        "O que entra na primeira versão e o que fica de fora?",
        "Escopo explícito evita que o agente gaste tempo em funcionalidades que ninguém pediu. "
        "Dizer o que NÃO fazer é tão importante quanto o que fazer.",
        (
            "Dos pedidos da área cliente, quais você vai atender nesta versão?",
            "Você vai além do pedido? Com o quê?",
            "O que fica explicitamente de fora (para o agente não inventar)?",
        ),
        "Entra: painel com a taxa de atraso por tipo de livro e por bairro do leitor.\n"
        "Fora do escopo: envio de mensagens aos leitores; cadastro de livros.",
    ),
    PassoSpec(
        "3. Dados",
        "Confira o dicionário das colunas e diga que cuidados o agente precisa ter.",
        "O agente só conhece seus dados pelo que você descreve. Colunas sem significado viram suposições — "
        "e suposições viram alucinações.",
        (
            "O significado de cada coluna ainda vale depois dos seus tratamentos?",
            "Alguma coluna tem uma leitura que confunde (ex.: \"sim\" quer dizer o contrário do que parece)?",
            "Alguma coluna não deve ser usada para prever o resultado? Por quê?",
            "Que valores parecem estranhos mas são válidos?",
        ),
        "Cuidados: `dias_atraso` = 0 significa devolução no prazo; leitores com menos de 12 anos usam o "
        "cadastro do responsável, então a coluna `idade` pode estar vazia para eles.",
    ),
    PassoSpec(
        "4. Funcionalidades",
        "O que o usuário consegue fazer na aplicação?",
        "Cada funcionalidade vira uma tarefa verificável para o agente.",
        (
            "O que o usuário precisa ver assim que abre o app?",
            "Que filtros ou comparações ele vai querer fazer?",
            "Ele precisa de uma lista (de clientes, reservas, consultas...) para agir?",
        ),
        "1. Ver a taxa de atraso geral.\n2. Ver a taxa de atraso por tipo de livro.\n"
        "3. Filtrar por bairro do leitor.\n4. Ver a lista dos leitores com mais atrasos no ano.",
    ),
    PassoSpec(
        "5. Regras de negócio",
        "Quais regras e fórmulas a solução deve respeitar?",
        "Regras escritas impedem que o agente invente fórmulas. É aqui que o resultado fica correto, "
        "não só bonito.",
        (
            "Como se calcula cada taxa ou número que aparece no app (usando quais colunas)?",
            "Como você define o grupo \"de risco\" ou \"prioritário\"?",
            "Como os números devem ser exibidos (porcentagem, casas decimais, ordem)?",
        ),
        "Taxa de atraso = empréstimos com `dias_atraso` > 0 ÷ total de empréstimos do filtro.\n"
        "Leitor recorrente = 3 ou mais atrasos no ano.\nTaxas em % com 1 casa decimal.",
    ),
    PassoSpec(
        "6. Arquitetura e restrições",
        "Como a solução deve ser construída e o que o agente NÃO pode fazer?",
        "Restrições reduzem o espaço de erro do agente. Sem elas, ele pode buscar dados na internet ou criar "
        "uma estrutura complexa demais para 1 hora.",
        (
            "Com quais tecnologias a solução deve ser feita?",
            "O agente pode buscar ou gerar dados novos?",
            "A solução precisa ser simples a ponto de rodar com um único comando?",
        ),
        "Stack: Python + Streamlit + pandas.\nRestrições: usar só o CSV fornecido; não inventar dados.",
    ),
    PassoSpec(
        "7. Critérios de aceitação e métricas",
        "Como saberemos que ficou pronto e correto?",
        "Critério verificável é o que permite conferir o trabalho do agente. \"Ficar bonito\" não é "
        "verificável; \"o painel mostra a taxa geral de 12,3% sem filtros\" é.",
        (
            "Que número o app deve mostrar sem nenhum filtro (veja os números de referência na prévia)?",
            "O que deve acontecer quando o usuário usa cada filtro?",
            "Como você confere a lista/ranking (quais colunas, qual ordem)?",
        ),
        "- Sem filtros, o painel mostra a taxa de atraso geral calculada do CSV.\n"
        "- Ao filtrar por bairro, todos os gráficos se atualizam.\n"
        "Métrica de sucesso: reduzir em 20% os atrasos dos leitores recorrentes em 3 meses.",
    ),
    PassoSpec(
        "8. Apresentação",
        "Como a equipe vai apresentar?",
        "A apresentação é parte da entrega. Planejar o roteiro agora orienta o que a aplicação precisa mostrar.",
        (
            "Quanto tempo vocês têm para apresentar?",
            "Em que ordem vão contar a história (problema, dados, decisões, demonstração, impacto)?",
        ),
        "Formato: pitch de 3 minutos.\nRoteiro: problema → o que descobrimos nos dados → como tratamos → "
        "demonstração → impacto esperado.",
    ),
)


# ---------------------------------------------------------------------------
# Respostas
# ---------------------------------------------------------------------------


def respostas_iniciais(tema: Theme) -> dict:
    """v2: tudo começa vazio — a equipe escreve a SPEC."""
    return {
        "nome_solucao": "",
        "problema": "",
        "usuario": None,
        "usuario_outro": "",
        "escopo_pedido": [],
        "escopo_proprio": "",
        "fora_escopo": "",
        "significados": {},
        "cuidados": "",
        "funcionalidades": "",
        "regras_negocio": "",
        "stack": "",
        "restricoes": [],
        "criterios_aceitacao": "",
        "metrica_sucesso": "",
        "formato": "",
        "roteiro": "",
    }


def linhas(texto: str | list | None) -> list[str]:
    """Lista a partir de texto com um item por linha (ignora linhas vazias e marcadores)."""
    itens = texto if isinstance(texto, list) else (texto or "").splitlines()
    limpos = []
    for item in itens:
        item = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", str(item)).strip()
        if item:
            limpos.append(item)
    return limpos


def usuario_texto(r: dict) -> str:
    if r.get("usuario") == "outro":
        return (r.get("usuario_outro") or "").strip()
    return USUARIOS.get(r.get("usuario") or "", "")


def itens_escopo(r: dict) -> list[str]:
    return list(r.get("escopo_pedido") or []) + linhas(r.get("escopo_proprio"))


def faltando_por_passo(r: dict) -> dict[int, list[str]]:
    """Campos obrigatórios vazios, por índice de passo (0 a 7)."""
    falta: dict[int, list[str]] = {}

    def add(i: int, campo: str) -> None:
        falta.setdefault(i, []).append(campo)

    if not (r.get("problema") or "").strip():
        add(0, "Problema")
    if not usuario_texto(r):
        add(0, "Usuário principal")
    if not itens_escopo(r):
        add(1, "O que entra nesta versão (pelo menos 1 item)")
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


def origem_das_colunas(passos_uid: list[str], resultados: dict[str, StepResult]) -> dict[str, str]:
    """Coluna -> uid do passo que a criou (o último que criou vale)."""
    origem: dict[str, str] = {}
    for chave in passos_uid:
        r = resultados.get(chave)
        if r:
            for c in r.colunas_criadas:
                origem[c] = chave
    return origem


def transformacoes(passos_uid: list[str], resultados: dict[str, StepResult]) -> dict[str, list[str]]:
    """Coluna -> uids dos passos que mudaram o tipo dela."""
    mudou: dict[str, list[str]] = {}
    for chave in passos_uid:
        r = resultados.get(chave)
        if r:
            for c in r.tipos_alterados:
                mudou.setdefault(c, []).append(chave)
    return mudou


def _titulo_limpo(bloco: Block) -> str:
    return bloco.titulo.replace("`", "")


def significado_padrao(
    tema: Theme,
    coluna: str,
    origem: dict[str, str],
    transformadas: dict[str, list[str]] | None = None,
    blocos: dict[str, Block] | None = None,
) -> str:
    """Significado vindo da documentação da base (dicionário do Kaggle) ou do passo que criou a coluna."""
    blocos = blocos or {}
    if coluna in tema.dicionario:
        texto = tema.dicionario[coluna]
    elif coluna in tema.dicionario_extra:
        texto = tema.dicionario_extra[coluna]
    elif coluna in origem and origem[coluna] in blocos:
        return f"Criada pelo passo \"{_titulo_limpo(blocos[origem[coluna]])}\""
    else:
        return ""
    chaves = [c for c in (transformadas or {}).get(coluna, []) if c in blocos]
    if chaves:
        texto += ". Tipo alterado no passo " + "; ".join(f"\"{_titulo_limpo(blocos[c])}\"" for c in chaves)
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
            partes.append(f"média de `{alvo}` = {serie.mean():.1%}".replace(".", ","))
        elif set(serie.dropna().astype(str).unique()) <= {"Yes", "No"}:
            partes.append(f"proporção de `{alvo}` = \"Yes\": {(serie == 'Yes').mean():.1%}".replace(".", ","))
        break
    return "Números de referência (calculados do `dados_tratados.csv`, sem filtros): " + "; ".join(partes) + "."


def tabela_dados(
    tema: Theme,
    df: pd.DataFrame,
    significados: dict[str, str],
    origem: dict[str, str],
    transformadas: dict[str, list[str]] | None = None,
    blocos: dict[str, Block] | None = None,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Coluna": [str(c) for c in df.columns],
            "Tipo": [tipo_amigavel(df[c].dtype) for c in df.columns],
            "Valores reais": [valores_coluna(df[c]) for c in df.columns],
            "Significado": [
                significados.get(str(c)) or significado_padrao(tema, str(c), origem, transformadas, blocos)
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
# Montagem da SPEC.md (template 9.1 da APP_SPEC, com os ajustes da v2). Seções vazias não aparecem.
# ---------------------------------------------------------------------------


@dataclass
class EstadoSpec:
    tema: Theme
    equipe: str
    df: pd.DataFrame
    passos: list  # passos do fluxo (texto ou dicionário), na ordem
    blocos: dict[str, Block]  # uid -> bloco executado
    resultados: dict[str, StepResult]
    respostas: dict
    notas_revisao: str = ""
    data: date = field(default_factory=date.today)


def _uid(passo) -> str:
    return passo if isinstance(passo, str) else passo["uid"]


def _nota(passo) -> str:
    return "" if isinstance(passo, str) else (passo.get("nota") or "").strip()


def _celula(texto: str) -> str:
    return str(texto).replace("|", "\\|").replace("\n", " ")


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

    nome = (r.get("nome_solucao") or "").strip() or f"Solução — {e.equipe.strip()}"
    out.append(f"# SPEC — {nome}")
    out.append(f"Equipe: {e.equipe.strip()} · Desafio: {t.nome} · Gerado em {e.data.strftime('%d/%m/%Y')}")
    out.append("")

    corpo1 = []
    if (r.get("problema") or "").strip():
        corpo1.append(r["problema"].strip())
    if usuario_texto(r):
        corpo1.append(f"Usuário principal: {usuario_texto(r)}")
    sec("## 1. Contexto e problema", ["  \n".join(corpo1)] if corpo1 else [])

    entra = [f"- {i}" for i in itens_escopo(r)]
    fora = [f"- {i}" for i in linhas(r.get("fora_escopo"))]
    corpo2 = []
    if entra:
        corpo2 += ["### Entra nesta versão", *entra]
    if fora:
        corpo2 += ["### Fora do escopo", *fora]
    sec("## 2. Objetivo e escopo", corpo2)

    # 3 — sempre do DataFrame real
    uids = [_uid(p) for p in e.passos]
    origem = origem_das_colunas(uids, e.resultados)
    tabela = tabela_dados(t, e.df, r.get("significados", {}), origem, transformacoes(uids, e.resultados), e.blocos)
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

    tratamentos = []
    for n, passo in enumerate(e.passos, start=1):
        bloco = e.blocos.get(_uid(passo))
        if bloco is None:
            continue
        linha = f"{n}. {bloco.titulo}"
        if _nota(passo):
            linha += f" — motivo da equipe: {_nota(passo)}"
        tratamentos.append(linha)
    sec("### 3.1 Tratamentos já aplicados (não refazer)", tratamentos)
    sec("### 3.2 Decisões e observações da revisão", [f"- {x}" for x in linhas(e.notas_revisao)])
    sec("### 3.3 Cuidados com os dados", [f"- {x}" for x in linhas(r.get("cuidados"))])

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
