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
    return StepResult(
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
    faltando_blocos = [b for b in bloco.requer_blocos if b not in aplicados]
    if faltando_blocos:
        lista = " e ".join(faltando_blocos)
        return f"Este bloco precisa que o bloco {lista} seja aplicado antes."
    for coluna in bloco.requer_colunas:
        if coluna in df.columns:
            continue
        if colunas_originais is not None and coluna in colunas_originais:
            return (
                f"Este bloco precisa da coluna `{coluna}`, que não existe mais na base atual "
                "(um passo anterior removeu ou renomeou essa coluna)."
            )
        criadores = blocos_que_criam(tema, coluna)
        dica = f" Aplique antes o bloco {' ou '.join(criadores)}." if criadores else ""
        return f"Este bloco precisa da coluna `{coluna}`.{dica}"
    return None


# ---------------------------------------------------------------------------
# Pipeline (reexecução a partir da base original)
# ---------------------------------------------------------------------------


@dataclass
class Pipeline:
    df: pd.DataFrame
    passos: list[str] = field(default_factory=list)
    resultados: dict[str, StepResult] = field(default_factory=dict)
    removidos: list[tuple[str, str]] = field(default_factory=list)  # (id, motivo)


def reexecutar(df_original: pd.DataFrame, tema: Theme, ids: list[str]) -> Pipeline:
    """Reaplica os passos, em ordem, a partir da base original.

    Passos que ficaram inválidos (faltou coluna ou bloco pré-requisito) ou que deram erro
    são removidos e listados em `removidos`.
    """
    colunas_originais = list(df_original.columns)
    pipe = Pipeline(df=df_original)
    for block_id in ids:
        bloco = tema.bloco(block_id)
        motivo = motivo_desabilitado(tema, bloco, pipe.df, pipe.passos, colunas_originais)
        if motivo:
            pipe.removidos.append((block_id, motivo))
            continue
        novo, resultado = aplicar(pipe.df, bloco)
        if resultado.erro:
            pipe.removidos.append((block_id, f"O bloco deu erro ao ser reaplicado ({resultado.erro})."))
            continue
        pipe.df = novo
        pipe.passos.append(block_id)
        pipe.resultados[block_id] = resultado
    if not pipe.passos:
        pipe.df = df_original.copy()
    return pipe


def desfazer(df_original: pd.DataFrame, tema: Theme, ids: list[str], block_id: str) -> Pipeline:
    """Remove o passo e reexecuta os demais a partir da base original (seção 7.2)."""
    return reexecutar(df_original, tema, [i for i in ids if i != block_id])


def codigo_completo(tema: Theme, ids: list[str]) -> str:
    partes = [f"# {i}. {tema.bloco(b).id} — {tema.bloco(b).titulo.replace('`', '')}\n{tema.bloco(b).codigo}"
              for i, b in enumerate(ids, start=1)]
    return "\n\n".join(partes)
