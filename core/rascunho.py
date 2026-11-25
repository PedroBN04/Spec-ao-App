"""Salvar e retomar o progresso da equipe em um arquivo .json (proposta P3.1).

O arquivo guarda só dados (textos, listas e números), nunca código. Ao retomar, tudo é validado e a
pipeline é reexecutada a partir da base original, como em qualquer outra mudança do fluxo.
"""

from __future__ import annotations

import json

from core import blocos_livres as bl
from core.themes import REGISTRY

VERSAO = 1
CAMPOS = ("equipe", "tema_id", "notas_diag", "notas_revisao", "revisao_ok", "passos", "prox_uid", "spec",
          "spec_passo", "etapa", "max_etapa", "exportou")
LIMITE_BYTES = 2_000_000


class RascunhoInvalido(ValueError):
    pass


def gerar(estado: dict) -> bytes:
    dados = {"app": "da-spec-ao-app", "versao": VERSAO}
    dados.update({c: estado.get(c) for c in CAMPOS})
    return json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8")


def _texto(v, limite=20_000) -> str:
    if v is None:
        return ""
    if not isinstance(v, str) or len(v) > limite:
        raise RascunhoInvalido("Um dos textos do rascunho está num formato inesperado.")
    return v


def _valor_simples(v) -> bool:
    if isinstance(v, (str, int, float, bool)) or v is None:
        return True
    if isinstance(v, list):
        return all(isinstance(x, (str, int, float)) for x in v)
    return False


def ler(conteudo: bytes) -> dict:
    """Valida o .json e devolve o estado a restaurar. Levanta RascunhoInvalido com mensagem simples."""
    if len(conteudo) > LIMITE_BYTES:
        raise RascunhoInvalido("O arquivo é grande demais para ser um rascunho deste app.")
    try:
        dados = json.loads(conteudo.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as erro:
        raise RascunhoInvalido("Este arquivo não é um rascunho válido (.json deste app).") from erro
    if not isinstance(dados, dict) or dados.get("app") != "da-spec-ao-app":
        raise RascunhoInvalido("Este arquivo não é um rascunho do Da Spec ao App.")
    tema = REGISTRY.get(dados.get("tema_id")) if dados.get("tema_id") else None
    if dados.get("tema_id") and tema is None:
        raise RascunhoInvalido("O rascunho é de uma missão que não existe nesta versão do app.")

    passos = []
    for p in dados.get("passos") or []:
        if not isinstance(p, dict) or not isinstance(p.get("uid"), str):
            raise RascunhoInvalido("A pipeline do rascunho está num formato inesperado.")
        base = {"uid": p["uid"][:20], "nota": _texto(p.get("nota"), 2_000)}
        if p.get("tipo") == "catalogo":
            if tema is None or p.get("id") not in {b.id for b in tema.blocos}:
                raise RascunhoInvalido("A pipeline do rascunho tem um bloco que não existe nesta missão.")
            passos.append({**base, "tipo": "catalogo", "id": p["id"]})
        elif p.get("tipo") == "livre":
            params = p.get("params") or {}
            if p.get("acao") not in bl.ACAO_POR_ID or not isinstance(params, dict) or not all(
                    isinstance(k, str) and _valor_simples(v) for k, v in params.items()):
                raise RascunhoInvalido("A pipeline do rascunho tem um bloco personalizado inválido.")
            passos.append({**base, "tipo": "livre", "acao": p["acao"], "params": params})
        else:
            raise RascunhoInvalido("A pipeline do rascunho tem um passo de tipo desconhecido.")

    spec = dados.get("spec") or {}
    if not isinstance(spec, dict) or not all(isinstance(k, str) for k in spec):
        raise RascunhoInvalido("As respostas da SPEC do rascunho estão num formato inesperado.")
    for k, v in spec.items():
        if k == "significados":
            if not isinstance(v, dict) or not all(isinstance(a, str) and isinstance(b, str) for a, b in v.items()):
                raise RascunhoInvalido("O dicionário de dados do rascunho está num formato inesperado.")
        elif not _valor_simples(v):
            raise RascunhoInvalido("As respostas da SPEC do rascunho estão num formato inesperado.")

    def inteiro(nome, minimo, maximo, padrao):
        v = dados.get(nome, padrao)
        return v if isinstance(v, int) and minimo <= v <= maximo else padrao

    return {
        "equipe": _texto(dados.get("equipe"), 40),
        "tema_id": dados.get("tema_id") if tema else None,
        "notas_diag": _texto(dados.get("notas_diag")),
        "notas_revisao": _texto(dados.get("notas_revisao")),
        "revisao_ok": bool(dados.get("revisao_ok")),
        "passos": passos,
        "prox_uid": inteiro("prox_uid", 1, 100_000, len(passos) + 1),
        "spec": spec,
        "spec_passo": inteiro("spec_passo", 0, 7, 0),
        "etapa": inteiro("etapa", 0, 7, 0),
        "max_etapa": inteiro("max_etapa", 0, 7, 0),
        "exportou": bool(dados.get("exportou")),
    }
