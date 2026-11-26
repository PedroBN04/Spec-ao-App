"""Executa blocos, mede o impacto e desfaz passos (seções 5.1, 7.1 e 7.2 da APP_SPEC).

Regra crítica: o texto de `Block.codigo` é executado exatamente como é exibido, com
    exec(block.codigo, {"pd": pd, "np": np}, ns)   onde ns = {"df": df.copy()}
O DataFrame recebido nunca é alterado.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from core.models import Block, StepResult, Theme

LIMITE_REMOCAO_LINHAS = 0.20  # acima disso, a etapa 3 mostra st.error (seção 7.1)
LIMITE_COLUNAS_REPETIDAS = 200  # acima disso não contamos linhas repetidas (lento demais, ex.: depois do T11)


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------


def executar_codigo(codigo: str, df: pd.DataFrame) -> pd.DataFrame:
    ns = {"df": df.copy()}
    exec(codigo, {"pd": pd, "np": np}, ns)
    resultado = ns["df"]
    if not isinstance(resultado, pd.DataFrame):
        raise TypeError("O bloco não devolveu uma tabela (DataFrame) em `df`.")
    return resultado


def contar_nulos(df: pd.DataFrame) -> int:
    return int(df.isna().sum().sum())


def medir(block_id: str, antes: pd.DataFrame, depois: pd.DataFrame) -> StepResult:
    colunas_antes = list(antes.columns)
    colunas_depois = list(depois.columns)
    conjunto_antes, conjunto_depois = set(colunas_antes), set(colunas_depois)
    tipos = {
        c: (str(antes[c].dtype), str(depois[c].dtype))
        for c in colunas_antes
        if c in conjunto_depois and antes[c].dtype != depois[c].dtype
    }
    contar = antes.shape[1] <= LIMITE_COLUNAS_REPETIDAS and depois.shape[1] <= LIMITE_COLUNAS_REPETIDAS
    return StepResult(
        repetidas_antes=int(antes.duplicated().sum()) if contar else None,
        repetidas_depois=int(depois.duplicated().sum()) if contar else None,
        block_id=block_id,
        linhas_antes=len(antes),
        linhas_depois=len(depois),
        colunas_antes=antes.shape[1],
        colunas_depois=depois.shape[1],
        nulos_antes=contar_nulos(antes),
        nulos_depois=contar_nulos(depois),
        colunas_criadas=[c for c in colunas_depois if c not in conjunto_antes],
        colunas_removidas=[c for c in colunas_antes if c not in conjunto_depois],
        tipos_alterados=tipos,
    )


def aplicar(df: pd.DataFrame, bloco: Block) -> tuple[pd.DataFrame, StepResult]:
    """Aplica o bloco. Em caso de erro, devolve o MESMO df (sem mudanças) e o erro no StepResult."""
    try:
        novo = executar_codigo(bloco.codigo, df)
    except Exception as erro:  # o participante vê uma mensagem simples; o detalhe vai num expander
        resultado = medir(bloco.id, df, df)
        resultado.erro = f"{type(erro).__name__}: {erro}"
        return df, resultado
    return novo, medir(bloco.id, df, novo)


def pct_linhas_removidas(r: StepResult) -> float:
    if not r.linhas_antes:
        return 0.0
    return (r.linhas_antes - r.linhas_depois) / r.linhas_antes


# ---------------------------------------------------------------------------
# Pré-requisitos
# ---------------------------------------------------------------------------

_ATRIBUICAO = re.compile(r'df\["([^"]+)"\]\s*=')


def blocos_que_criam(tema: Theme, coluna: str) -> list[str]:
    """Blocos do tema cujo código cria (atribui) a coluna."""
    return [b.id for b in tema.blocos if coluna in _ATRIBUICAO.findall(b.codigo)]


def motivo_desabilitado(
    tema: Theme,
    bloco: Block,
    df: pd.DataFrame,
    aplicados: list[str],
    colunas_originais: list[str] | None = None,
) -> str | None:
    """Explica por que o bloco não pode ser aplicado agora, ou None se pode."""
    def nome(block_id: str) -> str:
        return f"\"{tema.bloco(block_id).titulo}\""

    faltando_blocos = [b for b in bloco.requer_blocos if b not in aplicados]
    if faltando_blocos:
        lista = " e ".join(nome(b) for b in faltando_blocos)
        return f"Este bloco precisa que {lista} seja aplicado antes."
    for coluna in bloco.requer_colunas:
        if coluna in df.columns:
            continue
        if colunas_originais is not None and coluna in colunas_originais:
            return (
                f"Este bloco precisa da coluna `{coluna}`, que não existe mais na base atual "
                "(um passo anterior removeu ou renomeou essa coluna)."
            )
        criadores = blocos_que_criam(tema, coluna)
        dica = f" Aplique antes {' ou '.join(nome(b) for b in criadores)}." if criadores else ""
        return f"Este bloco precisa da coluna `{coluna}`.{dica}"
    return None


# ---------------------------------------------------------------------------
# Pipeline (reexecução a partir da base original)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Passos do fluxo (v2)
#
# Um passo é o id de um bloco do catálogo (texto, ex.: "T01") ou um dicionário:
#   {"uid": "P3", "tipo": "catalogo", "id": "T01", "nota": "..."}
#   {"uid": "P4", "tipo": "livre", "acao": "preencher_vazios", "params": {...}, "nota": "..."}
# ---------------------------------------------------------------------------

Passo = str | dict


def uid(passo: Passo) -> str:
    return passo if isinstance(passo, str) else passo["uid"]


def eh_catalogo(passo: Passo) -> bool:
    return isinstance(passo, str) or passo.get("tipo") == "catalogo"


def id_catalogo(passo: Passo) -> str | None:
    if isinstance(passo, str):
        return passo
    return passo.get("id") if passo.get("tipo") == "catalogo" else None


def bloco_do_passo(tema: Theme, passo: Passo, df: pd.DataFrame | None = None) -> Block:
    """Block do catálogo ou bloco personalizado gerado a partir dos parâmetros."""
    if eh_catalogo(passo):
        return tema.bloco(id_catalogo(passo))
    from core.blocos_livres import gerar_bloco

    return gerar_bloco(passo["uid"], passo["acao"], passo.get("params", {}), df)


@dataclass
class Pipeline:
    df: pd.DataFrame
    passos: list = field(default_factory=list)  # mesmos objetos recebidos (texto ou dicionário)
    resultados: dict[str, StepResult] = field(default_factory=dict)  # uid -> resultado
    blocos: dict[str, Block] = field(default_factory=dict)  # uid -> bloco efetivamente executado
    removidos: list[tuple[str, str]] = field(default_factory=list)  # (uid, motivo)

    def ids_catalogo(self) -> list[str]:
        return [i for i in (id_catalogo(p) for p in self.passos) if i]


def reexecutar(df_original: pd.DataFrame, tema: Theme, passos: list[Passo]) -> Pipeline:
    """Reaplica os passos, em ordem, a partir da base original.

    Passos que ficaram inválidos (faltou coluna ou bloco pré-requisito, parâmetro que não serve mais)
    ou que deram erro são removidos e listados em `removidos`.
    """
    from core.blocos_livres import ParametroInvalido

    colunas_originais = list(df_original.columns)
    pipe = Pipeline(df=df_original)
    for passo in passos:
        chave = uid(passo)
        try:
            bloco = bloco_do_passo(tema, passo, pipe.df)
        except ParametroInvalido as erro:
            pipe.removidos.append((chave, f"Os parâmetros não servem mais para a base neste ponto: {erro}"))
            continue
        motivo = motivo_desabilitado(tema, bloco, pipe.df, pipe.ids_catalogo(), colunas_originais)
        if motivo:
            pipe.removidos.append((chave, motivo))
            continue
        novo, resultado = aplicar(pipe.df, bloco)
        if resultado.erro:
            pipe.removidos.append((chave, f"O bloco deu erro ao ser reaplicado ({resultado.erro})."))
            continue
        pipe.df = novo
        pipe.passos.append(passo)
        pipe.resultados[chave] = resultado
        pipe.blocos[chave] = bloco
    if not pipe.passos:
        pipe.df = df_original.copy()
    return pipe


def desfazer(df_original: pd.DataFrame, tema: Theme, passos: list[Passo], chave: str) -> Pipeline:
    """Remove o passo e reexecuta os demais a partir da base original (seção 7.2)."""
    return reexecutar(df_original, tema, [p for p in passos if uid(p) != chave])


def mover(passos: list[Passo], chave: str, deslocamento: int) -> list[Passo]:
    """Nova lista com o passo deslocado (−1 sobe, +1 desce). Não reexecuta."""
    lista = list(passos)
    i = next(n for n, p in enumerate(lista) if uid(p) == chave)
    j = max(0, min(len(lista) - 1, i + deslocamento))
    lista.insert(j, lista.pop(i))
    return lista


def codigo_completo(tema: Theme, passos: list[Passo], blocos: dict[str, Block] | None = None) -> str:
    partes = []
    for n, passo in enumerate(passos, start=1):
        bloco = (blocos or {}).get(uid(passo)) or bloco_do_passo(tema, passo)
        partes.append(f"# {n}. {bloco.titulo.replace('`', '')}\n{bloco.codigo}")
    return "\n\n".join(partes)
