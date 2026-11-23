"""Checklist de qualidade (etapa 4 e seção 8.4 da APP_SPEC).

Junta as regras genéricas (G01–G07) com as regras do tema e calcula a nota.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

from core import diagnostics as dg
from core.models import Check, Theme

ROTULO_CATEGORIA = {"boa_pratica": "Boa prática", "armadilha": "Armadilha", "depende": "Depende do objetivo"}
ICONE_CATEGORIA = {"boa_pratica": "✅", "armadilha": "⚠️", "depende": "🤔"}


@dataclass
class ResultadoCheck:
    check: Check
    passou: bool
    mensagem: str

    @property
    def pendente(self) -> bool:
        """Erro ou alerta que não passou: precisa ser corrigido ou justificado."""
        return not self.passou and self.check.nivel in ("erro", "alerta")


_IDENTIFICADOR = re.compile(r"(^id_|_id$|Id$|ID$|^id$)")


def eh_identificador(coluna) -> bool:
    return bool(_IDENTIFICADOR.search(str(coluna)))


def colunas_vazamento_presentes(tema: Theme, df: pd.DataFrame) -> list[str]:
    presentes = [c for c in tema.colunas_vazamento if c in df.columns]
    for padrao in tema.vazamento_derivado:
        if padrao.endswith("_"):
            presentes += [c for c in df.columns if str(c).startswith(padrao) and c not in presentes]
        elif padrao in df.columns and padrao not in presentes:
            presentes.append(padrao)
    return presentes


def regras_genericas(tema: Theme) -> tuple[Check, ...]:
    alvos = (tema.alvo, *tema.alvos_aceitos)

    def g01(orig, df, ids):
        achados = [a for a in alvos if a in df.columns]
        if achados:
            return True, f"Coluna de resultado presente: `{achados[0]}`."
        return False, f"Nenhuma coluna de resultado encontrada (esperado: {', '.join(f'`{a}`' for a in alvos)})."

    def g02(orig, df, ids):
        achadas = colunas_vazamento_presentes(tema, df)
        if achadas:
            lista = ", ".join(f"`{c}`" for c in achadas[:5]) + (" ..." if len(achadas) > 5 else "")
            return False, f"Colunas que revelam o resultado ainda estão na base: {lista}."
        return True, "Nenhuma coluna de vazamento na base."

    def g03(orig, df, ids):
        pct = len(df) / len(orig) if len(orig) else 1.0
        texto = f"{pct:.1%}".replace(".", ",")
        if pct >= 0.8:
            return True, f"{texto} das linhas originais foram mantidas."
        return False, f"Só {texto} das linhas originais foram mantidas (o mínimo recomendado é 80%)."

    def g04(orig, df, ids):
        nulos = df.isna().sum()
        nulos = nulos[nulos > 0]
        if nulos.empty:
            return True, "Nenhuma célula vazia."
        lista = ", ".join(f"`{c}` ({n})" for c, n in nulos.head(5).items())
        extra = f" e mais {len(nulos) - 5} coluna(s)" if len(nulos) > 5 else ""
        return False, f"Ainda há {int(nulos.sum())} célula(s) vazia(s): {lista}{extra}."

    def g05(orig, df, ids):
        # Identificadores (PatientId, id_paciente...) DEVEM ser texto: não contam (DECISOES.md).
        cols = [c for c in df.columns if dg.parece_numero(df[c]) and not eh_identificador(c)]
        if cols:
            return False, "Colunas de texto que parecem números: " + ", ".join(f"`{c}`" for c in cols) + "."
        return True, "Nenhuma coluna de número guardada como texto."

    def g06(orig, df, ids):
        n = df.shape[1]
        if n <= 60:
            return True, f"A base tem {n} colunas."
        return False, f"A base tem {n} colunas (o máximo recomendado é 60)."

    def g07(orig, df, ids):
        if not ids:
            return True, "Nenhum bloco aplicado."
        contagem: dict[str, list[str]] = {}
        for bid in ids:
            contagem.setdefault(tema.bloco(bid).categoria, []).append(bid)
        partes = [
            f"{ICONE_CATEGORIA[cat]} {ROTULO_CATEGORIA[cat]}: {len(contagem[cat])} ({', '.join(contagem[cat])})"
            for cat in ("boa_pratica", "armadilha", "depende")
            if cat in contagem
        ]
        return True, " · ".join(partes)

    return (
        Check("G01", "O resultado (alvo) continua na base", "erro", g01,
              "Sem a coluna de resultado, o app final não calcula taxas."),
        Check("G02", "Nenhuma coluna que revela o resultado", "erro", g02,
              "Vazamento faz qualquer análise preditiva parecer perfeita e falhar na prática."),
        Check("G03", "Pelo menos 80% das linhas mantidas", "alerta", g03,
              "Remover muitas linhas pode enviesar o resultado."),
        Check("G04", "Nenhuma célula vazia", "alerta", g04,
              "Nulos geram erros e gráficos incompletos no app final."),
        Check("G05", "Nenhum número guardado como texto", "alerta", g05,
              "Números como texto não somam nem fazem média."),
        Check("G06", "No máximo 60 colunas", "alerta", g06,
              "Bases muito largas confundem o agente e quem lê o painel."),
        Check("G07", "Blocos aplicados por categoria", "info", g07,
              "Registro das decisões para a avaliação."),
    )


def todas_as_regras(tema: Theme) -> tuple[Check, ...]:
    return regras_genericas(tema) + tuple(tema.regras_checklist)


def avaliar(tema: Theme, df_original: pd.DataFrame, df: pd.DataFrame, ids: list[str]) -> list[ResultadoCheck]:
    resultados = []
    for check in todas_as_regras(tema):
        try:
            passou, mensagem = check.funcao(df_original, df, list(ids))
        except Exception as erro:  # uma regra com defeito não pode derrubar a tela
            passou, mensagem = False, f"Não foi possível verificar esta regra ({type(erro).__name__})."
        resultados.append(ResultadoCheck(check, bool(passou), mensagem))
    return resultados


def placar(resultados: list[ResultadoCheck]) -> dict:
    erros = sum(1 for r in resultados if not r.passou and r.check.nivel == "erro")
    alertas = sum(1 for r in resultados if not r.passou and r.check.nivel == "alerta")
    passou = sum(1 for r in resultados if r.passou and r.check.nivel != "info")
    return {"passou": passou, "alertas": alertas, "erros": erros, "nota": max(0, 100 - 25 * erros - 10 * alertas)}


JUSTIFICATIVA_MINIMA = 15


def justificativa_valida(texto: str | None) -> bool:
    return len((texto or "").strip()) >= JUSTIFICATIVA_MINIMA


def pendencias(resultados: list[ResultadoCheck], decisoes: dict) -> list[ResultadoCheck]:
    """Erros/alertas ainda não resolvidos: nem corrigidos (passaram) nem justificados."""
    faltando = []
    for r in resultados:
        if not r.pendente:
            continue
        d = decisoes.get(r.check.id, {})
        if d.get("decisao") == "manter" and justificativa_valida(d.get("texto")):
            continue
        faltando.append(r)
    return faltando
