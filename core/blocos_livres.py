"""Blocos personalizados (v2): a pessoa escolhe a ação e os parâmetros; o app gera o código pandas.

O código gerado é exibido e executado exatamente como aparece (mesma regra dos blocos do catálogo).
Segurança: nenhum texto digitado vira código. Nomes de coluna vêm de listas; valores digitados entram
como literais Python via `repr()` depois de convertidos para número ou texto.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.models import Block

GRUPO = "Personalizado"


class ParametroInvalido(ValueError):
    """Mensagem em linguagem simples para mostrar ao participante."""


@dataclass(frozen=True)
class Acao:
    id: str
    rotulo: str
    descricao: str  # o que a ação faz, sem julgar se é boa ou ruim


ACOES = (
    Acao("remover_colunas", "Remover colunas", "Apaga uma ou mais colunas da base inteira."),
    Acao("preencher_vazios", "Preencher vazios", "Coloca um valor nas células vazias de uma coluna."),
    Acao("remover_linhas_vazias", "Remover linhas com vazios",
         "Apaga as linhas que têm célula vazia nas colunas escolhidas (ou em qualquer coluna)."),
    Acao("converter_tipo", "Converter tipo", "Muda o tipo de uma coluna (número, número inteiro, texto ou data)."),
    Acao("filtrar_linhas", "Filtrar linhas", "Mantém só as linhas que atendem a uma condição; as demais são apagadas."),
    Acao("substituir_valor", "Substituir valor", "Troca um valor por outro em uma coluna."),
    Acao("criar_faixas", "Criar faixas", "Cria uma coluna nova agrupando números em faixas (ex.: idades em 0-12, 13-18...)."),
    Acao("criar_indicador", "Criar coluna 0/1", "Cria uma coluna nova com 1 quando a condição é verdadeira e 0 quando não é."),
    Acao("calcular_coluna", "Calcular coluna", "Cria uma coluna nova com uma conta entre duas colunas numéricas."),
    Acao("renomear_coluna", "Renomear coluna", "Muda o nome de uma coluna."),
    Acao("remover_duplicados", "Remover linhas repetidas",
         "Apaga linhas repetidas, comparando todas as colunas ou só as escolhidas."),
)
ACAO_POR_ID = {a.id: a for a in ACOES}

OPERADORES = {"==": "igual a", "!=": "diferente de", ">": "maior que", ">=": "maior ou igual a",
              "<": "menor que", "<=": "menor ou igual a"}
CONTAS = {"+": "mais", "-": "menos", "*": "vezes", "/": "dividido por"}
TIPOS = {"numero": "número", "inteiro": "número inteiro", "texto": "texto", "data": "data/hora"}
METODOS = {"valor": "um valor que eu digito", "media": "a média da coluna", "mediana": "a mediana da coluna",
           "moda": "o valor mais frequente"}


# ---------------------------------------------------------------------------
# Conversão segura de valores digitados
# ---------------------------------------------------------------------------


def _numero(texto: str):
    t = str(texto).strip().replace(",", ".")
    try:
        v = float(t)
    except ValueError as erro:
        raise ParametroInvalido(f"\"{texto}\" não é um número.") from erro
    return int(v) if v.is_integer() else v


def literal_para(texto: str, serie: pd.Series | None):
    """Converte o texto digitado no tipo da coluna (número para colunas numéricas, texto para as demais)."""
    if serie is not None and pd.api.types.is_numeric_dtype(serie) and not pd.api.types.is_bool_dtype(serie):
        return _numero(texto)
    if serie is not None and pd.api.types.is_datetime64_any_dtype(serie):
        try:
            pd.Timestamp(str(texto).strip())
        except ValueError as erro:
            raise ParametroInvalido(f"\"{texto}\" não é uma data (use AAAA-MM-DD).") from erro
        return str(texto).strip()
    return str(texto)


def _col(nome: str) -> str:
    return f"df[{nome!r}]"


def _exigir(cond: bool, msg: str) -> None:
    if not cond:
        raise ParametroInvalido(msg)


def _nome_novo(nome: str, df: pd.DataFrame | None) -> str:
    nome = (nome or "").strip()
    _exigir(bool(nome), "Dê um nome para a coluna nova.")
    _exigir(len(nome) <= 60, "O nome da coluna é longo demais (máximo de 60 caracteres).")
    return nome


# ---------------------------------------------------------------------------
# Geração do bloco
# ---------------------------------------------------------------------------


def gerar_bloco(uid: str, acao: str, p: dict, df: pd.DataFrame | None = None) -> Block:
    """Monta o Block (título, código, colunas exigidas) a partir da ação e dos parâmetros.

    `df` é a base no ponto do fluxo; serve para validar e converter valores. Pode ser None ao
    reconstruir um passo já validado.
    """
    if acao not in ACAO_POR_ID:
        raise ParametroInvalido("Ação desconhecida.")
    serie = lambda c: df[c] if df is not None and c in df.columns else None  # noqa: E731

    if acao == "remover_colunas":
        cols = list(p.get("colunas") or [])
        _exigir(bool(cols), "Escolha pelo menos uma coluna.")
        codigo = f"df = df.drop(columns={cols!r})"
        titulo = "Remover " + ", ".join(f"`{c}`" for c in cols)
        requer = tuple(cols)

    elif acao == "preencher_vazios":
        c, metodo = p.get("coluna"), p.get("metodo", "valor")
        _exigir(bool(c), "Escolha a coluna.")
        if metodo == "valor":
            _exigir(str(p.get("valor", "")).strip() != "", "Digite o valor para preencher.")
            v = literal_para(p["valor"], serie(c))
            codigo = f"{_col(c)} = {_col(c)}.fillna({v!r})"
            titulo = f"Preencher vazios de `{c}` com {v!r}"
        elif metodo in ("media", "mediana"):
            fn = "mean" if metodo == "media" else "median"
            codigo = f"{_col(c)} = {_col(c)}.fillna({_col(c)}.{fn}())"
            titulo = f"Preencher vazios de `{c}` com a {METODOS[metodo].removeprefix('a ')}"
        elif metodo == "moda":
            codigo = f"{_col(c)} = {_col(c)}.fillna({_col(c)}.mode().iloc[0])"
            titulo = f"Preencher vazios de `{c}` com o valor mais frequente"
        else:
            raise ParametroInvalido("Escolha como preencher.")
        requer = (c,)

    elif acao == "remover_linhas_vazias":
        cols = list(p.get("colunas") or [])
        if cols:
            codigo = f"df = df.dropna(subset={cols!r})"
            titulo = "Remover linhas com vazios em " + ", ".join(f"`{c}`" for c in cols)
        else:
            codigo = "df = df.dropna()"
            titulo = "Remover linhas com vazios em qualquer coluna"
        requer = tuple(cols)

    elif acao == "converter_tipo":
        c, para = p.get("coluna"), p.get("para")
        _exigir(bool(c), "Escolha a coluna.")
        modelos = {
            "numero": f"{_col(c)} = pd.to_numeric({_col(c)}.astype(str).str.strip(), errors=\"coerce\")",
            "inteiro": f"{_col(c)} = pd.to_numeric({_col(c)}.astype(str).str.strip(), errors=\"coerce\").astype(\"Int64\")",
            "texto": f"{_col(c)} = {_col(c)}.astype(str)",
            "data": f"{_col(c)} = pd.to_datetime({_col(c)}, errors=\"coerce\")",
        }
        _exigir(para in modelos, "Escolha o tipo de destino.")
        codigo = modelos[para]
        titulo = f"Converter `{c}` para {TIPOS[para]}"
        requer = (c,)

    elif acao in ("filtrar_linhas", "criar_indicador"):
        c, op = p.get("coluna"), p.get("operador")
        _exigir(bool(c), "Escolha a coluna.")
        _exigir(op in OPERADORES, "Escolha a comparação.")
        _exigir(str(p.get("valor", "")).strip() != "", "Digite o valor da comparação.")
        v = literal_para(p["valor"], serie(c))
        cond = f"{_col(c)} {op} {v!r}"
        if acao == "filtrar_linhas":
            codigo = f"df = df[{cond}]"
            titulo = f"Manter linhas onde `{c}` {OPERADORES[op]} {v!r}"
        else:
            nome = _nome_novo(p.get("nome", ""), df)
            codigo = f"df[{nome!r}] = ({cond}).astype(int)"
            titulo = f"Criar `{nome}` (1 quando `{c}` {OPERADORES[op]} {v!r})"
        requer = (c,)

    elif acao == "substituir_valor":
        c = p.get("coluna")
        _exigir(bool(c), "Escolha a coluna.")
        _exigir(str(p.get("de", "")) != "", "Digite o valor que será trocado.")
        de, para = literal_para(p["de"], serie(c)), literal_para(p.get("para", ""), serie(c))
        codigo = f"{_col(c)} = {_col(c)}.replace({{{de!r}: {para!r}}})"
        titulo = f"Em `{c}`, trocar {de!r} por {para!r}"
        requer = (c,)

    elif acao == "criar_faixas":
        c = p.get("coluna")
        _exigir(bool(c), "Escolha a coluna numérica.")
        partes = [x for x in str(p.get("cortes", "")).replace(";", " ").replace(",", " ").split() if x]
        cortes = [_numero(x) for x in partes]
        _exigir(len(cortes) >= 2, "Digite pelo menos 2 limites (ex.: 0 12 24 48 72).")
        _exigir(cortes == sorted(set(cortes)), "Os limites precisam estar em ordem crescente e sem repetição.")
        if df is not None and c in df.columns:
            _exigir(pd.api.types.is_numeric_dtype(df[c]), f"`{c}` não é numérica: converta antes de criar faixas.")
        nome = _nome_novo(p.get("nome", ""), df)
        codigo = f"df[{nome!r}] = pd.cut({_col(c)}, bins={cortes!r}, include_lowest=True).astype(str)"
        titulo = f"Criar faixas de `{c}` em `{nome}`"
        requer = (c,)

    elif acao == "calcular_coluna":
        a, op, b = p.get("coluna_a"), p.get("conta"), p.get("coluna_b")
        _exigir(bool(a) and bool(b), "Escolha as duas colunas.")
        _exigir(op in CONTAS, "Escolha a conta.")
        if df is not None:
            for x in (a, b):
                if x in df.columns:
                    _exigir(pd.api.types.is_numeric_dtype(df[x]), f"`{x}` não é numérica.")
        nome = _nome_novo(p.get("nome", ""), df)
        codigo = f"df[{nome!r}] = {_col(a)} {op} {_col(b)}"
        titulo = f"Criar `{nome}` = `{a}` {CONTAS[op]} `{b}`"
        requer = (a, b)

    elif acao == "renomear_coluna":
        c = p.get("coluna")
        _exigir(bool(c), "Escolha a coluna.")
        novo = _nome_novo(p.get("novo", ""), df)
        if df is not None:
            _exigir(novo not in df.columns, f"Já existe uma coluna chamada `{novo}`.")
        codigo = f"df = df.rename(columns={{{c!r}: {novo!r}}})"
        titulo = f"Renomear `{c}` para `{novo}`"
        requer = (c,)

    else:  # remover_duplicados
        cols = list(p.get("colunas") or [])
        if cols:
            codigo = f"df = df.drop_duplicates(subset={cols!r})"
            titulo = "Remover linhas repetidas em " + ", ".join(f"`{c}`" for c in cols)
        else:
            codigo = "df = df.drop_duplicates()"
            titulo = "Remover linhas repetidas (todas as colunas iguais)"
        requer = tuple(cols)

    return Block(
        id=uid,
        titulo=titulo,
        grupo=GRUPO,
        explicacao=ACAO_POR_ID[acao].descricao,
        codigo=codigo,
        requer_colunas=requer,
        categoria="livre",
    )
