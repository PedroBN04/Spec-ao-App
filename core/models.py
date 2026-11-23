"""Modelos de dados do app (seção 5 da APP_SPEC).

Acréscimos em relação à spec (ver DECISOES.md):
- Block.sugestao: id do bloco correto sugerido quando o participante aplica uma armadilha.
- Theme.emoji, alvos_aceitos, vazamento_derivado, dicionario_extra, observacoes,
  area_cliente, solicitante, missao (v2).
- Categoria "livre" para blocos personalizados (v2).
"""

from dataclasses import dataclass, field
from typing import Callable, Literal

import pandas as pd

# "livre" = bloco personalizado montado pela pessoa (v2); não tem categoria de gabarito.
Categoria = Literal["boa_pratica", "armadilha", "depende", "livre"]


@dataclass(frozen=True)
class Block:
    id: str  # ex.: "T01"
    titulo: str  # ex.: "Converter TotalCharges para número"
    grupo: str  # ex.: "Tipos", "Valores ausentes", "Outliers", "Variáveis", "Alvo", "Estrutura"
    explicacao: str  # o que o bloco faz, em linguagem simples (mostrado ANTES de aplicar)
    codigo: str  # trecho pandas EXECUTADO e EXIBIDO (fonte única da verdade)
    requer_colunas: tuple[str, ...] = ()  # colunas que precisam existir para o bloco ficar habilitado
    requer_blocos: tuple[str, ...] = ()  # blocos que precisam ter sido aplicados antes
    categoria: Categoria = "boa_pratica"  # NÃO é mostrada antes de aplicar (ver 7.3)
    feedback: str = ""  # explicação da consequência, mostrada DEPOIS de aplicar
    pergunta_reflexao: str = ""  # pergunta curta para o participante pensar
    sugestao: str = ""  # id do bloco correto a sugerir quando este é uma armadilha


@dataclass(frozen=True)
class Check:
    id: str
    titulo: str
    nivel: Literal["erro", "alerta", "info"]
    funcao: Callable[[pd.DataFrame, pd.DataFrame, list[str]], tuple[bool, str]]
    # recebe (df_original, df_tratado, ids_dos_blocos_aplicados) e devolve (passou, mensagem)
    explicacao: str  # "por que isso importa"


@dataclass(frozen=True)
class Theme:
    id: str
    nome: str  # ex.: "Telecom: quem vai cancelar?"
    dominio: str
    arquivo: str  # caminho em data/
    fonte: str  # URL do Kaggle
    licenca: str
    alvo: str  # coluna alvo original
    descricao_base: str
    dicionario: dict[str, str]  # coluna -> significado em português
    problematica: str
    proposta_inicial: list[str]  # escopo mínimo da entrega
    aprofundamentos: list[str]  # opções para quem quiser ir além
    colunas_vazamento: tuple[str, ...]  # colunas que não podem virar entrada de modelo
    blocos: tuple[Block, ...]
    regras_checklist: tuple[Check, ...]
    spec_defaults: dict  # sugestões pré-preenchidas no assistente (seção 9)
    emoji: str = "📊"
    # Nomes aceitos para o alvo depois de tratado (G01). O alvo original sempre conta.
    alvos_aceitos: tuple[str, ...] = ()
    # Colunas derivadas do alvo (nome exato ou prefixo terminado em "_"), além de colunas_vazamento (G02).
    vazamento_derivado: tuple[str, ...] = ()
    # Descrição padrão de colunas criadas ou renomeadas pelos blocos (assistente da SPEC, passo 3).
    dicionario_extra: dict[str, str] = field(default_factory=dict)
    # Observações sobre os dados (v2: usadas só no gabarito do facilitador): (coluna, texto).
    observacoes: tuple[tuple[str, str], ...] = ()
    # Missão (v2): a solicitação da área cliente.
    area_cliente: str = ""
    solicitante: str = ""
    missao: str = ""

    def bloco(self, block_id: str) -> Block:
        for b in self.blocos:
            if b.id == block_id:
                return b
        raise KeyError(block_id)


@dataclass
class StepResult:
    block_id: str
    linhas_antes: int
    linhas_depois: int
    colunas_antes: int
    colunas_depois: int
    nulos_antes: int
    nulos_depois: int
    colunas_criadas: list[str]
    colunas_removidas: list[str]
    tipos_alterados: dict[str, tuple[str, str]]
    erro: str | None = None


@dataclass
class SpecAnswers:
    """Respostas do assistente da SPEC (etapa 5). Preenchido no marco M5."""

    respostas: dict = field(default_factory=dict)
