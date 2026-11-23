# APP_SPEC — "Da Spec ao App": laboratório guiado de dados e especificação

> Documento de especificação para o Claude Code implementar a aplicação.
> Leia inteiro antes de começar. Implemente na ordem dos **Marcos** (seção 13).
> Quando esta spec não disser algo, escolha a opção mais simples e registre a decisão em `DECISOES.md`.

---

## 1. Visão geral

Aplicação web **didática** usada em um minicurso + hackathon de 3h30 (24/11/2026, até 25 participantes, maioria **sem experiência em programação**).

O participante:
1. escolhe um desafio (tema + base de dados real);
2. entende a base por um diagnóstico visual;
3. monta um pipeline de tratamento **clicando em blocos** — alguns são boas práticas, outros são **armadilhas** — e vê o impacto real de cada escolha;
4. passa por um checklist de qualidade que aponta as consequências das suas decisões;
5. responde a um assistente passo a passo que monta uma `SPEC.md`;
6. exporta **dois arquivos**: `dados_tratados.csv` e `SPEC.md`, que serão entregues a um agente de código (Claude Code) para construir a solução final do hackathon.

O objetivo central é **aprender**: cada tela deve responder *o que estou fazendo*, *por que* e *qual a consequência*.

### 1.1 Fora de escopo
- Login, contas, banco de dados, persistência no servidor.
- Treinar modelos de machine learning dentro do app.
- Usuário escrever código livre (o app só executa os blocos do catálogo).
- Upload de bases próprias.
- Internacionalização (o app é todo em **português do Brasil**).

---

## 2. Público e princípios de UX

- Público: estudantes de Gestão da Informação e iniciantes do UberHub Code Club. Sabem usar planilha; muitos nunca programaram.
- **Linguagem simples**, frases curtas, sem jargão sem explicação. Todo termo técnico tem uma dica (tooltip ou `st.caption`) na primeira vez que aparece.
- **Mostrar antes de explicar**: toda ação exibe o "antes × depois" (linhas, colunas, nulos, tipos, amostra).
- **O app não impede o erro**: blocos de armadilha executam normalmente. O aprendizado vem do feedback depois da execução.
- **Sempre há volta**: qualquer passo do pipeline pode ser desfeito.
- Fluxo linear com barra de progresso, mas o participante pode voltar a etapas anteriores.

---

## 3. Stack e restrições técnicas

| Item | Escolha |
| --- | --- |
| Linguagem | Python 3.11+ |
| Interface | Streamlit ≥ 1.40 |
| Dados | pandas ≥ 2.2, numpy |
| Gráficos | plotly (via `st.plotly_chart`) |
| Testes | pytest |
| Deploy | Streamlit Community Cloud a partir do repositório GitHub (plano B: `streamlit run app.py` local) |

Restrições:
- **Sem chamadas a APIs externas** e sem chaves de API.
- Cada sessão de usuário guarda seu estado em `st.session_state`; a base original é carregada uma vez com `@st.cache_data` e **nunca é alterada** (sempre trabalhar sobre cópia).
- Memória: o deploy gratuito tem ~1 GB para todos os usuários. Por isso as bases do repositório são **amostras de até 30 mil linhas** (ver `scripts/preparar_dados.py`, seção 12) e cada sessão guarda **apenas o DataFrame atual + o DataFrame original em cache**, não uma cópia por passo. O "desfazer" reexecuta o pipeline a partir da base original.
- Tempo de resposta: aplicar um bloco deve levar < 2 s nas bases do repositório.

---

## 4. Estrutura de pastas

```
.
├── app.py                      # ponto de entrada: roteia as etapas
├── requirements.txt
├── README.md                   # como rodar, créditos e licenças das bases
├── DECISOES.md                 # decisões tomadas durante a implementação
├── data/
│   ├── telco_churn.csv
│   ├── hotel_bookings.csv      # amostra
│   └── noshow_consultas.csv    # amostra
├── scripts/
│   └── preparar_dados.py       # gera as amostras a partir dos CSV originais do Kaggle
├── core/
│   ├── models.py               # dataclasses: Theme, Block, StepResult, Check, SpecAnswers
│   ├── themes/
│   │   ├── __init__.py         # REGISTRY = {"telco": THEME, "hotel": THEME, "noshow": THEME}
│   │   ├── telco.py            # tema + catálogo de blocos + regras de checklist + defaults da spec
│   │   ├── hotel.py
│   │   └── noshow.py
│   ├── diagnostics.py          # perfil da base e alertas automáticos
│   ├── executor.py             # aplica blocos, mede impacto, desfaz
│   ├── checklist.py            # regras genéricas + regras do tema
│   ├── spec_builder.py         # perguntas do assistente e montagem da SPEC.md
│   └── exporter.py             # gera CSV e SPEC.md
├── ui/
│   ├── components.py           # cartões, métricas antes×depois, badges, caixas "Por que isso importa?"
│   └── steps/
│       ├── s0_boas_vindas.py
│       ├── s1_desafio.py
│       ├── s2_diagnostico.py
│       ├── s3_tratamento.py
│       ├── s4_checklist.py
│       ├── s5_spec.py
│       └── s6_exportar.py
└── tests/
    ├── test_blocks.py
    ├── test_executor.py
    ├── test_checklist.py
    └── test_spec_builder.py
```

---

## 5. Modelo de dados (core/models.py)

```python
from dataclasses import dataclass, field
from typing import Literal, Callable
import pandas as pd

Categoria = Literal["boa_pratica", "armadilha", "depende"]

@dataclass(frozen=True)
class Block:
    id: str                    # ex.: "T01"
    titulo: str                # ex.: "Converter TotalCharges para número"
    grupo: str                 # ex.: "Tipos", "Valores ausentes", "Outliers", "Variáveis", "Alvo", "Estrutura"
    explicacao: str            # o que o bloco faz, em linguagem simples (mostrado ANTES de aplicar)
    codigo: str                # trecho pandas EXECUTADO e EXIBIDO (fonte única da verdade)
    requer_colunas: tuple[str, ...] = ()   # colunas que precisam existir para o bloco ficar habilitado
    requer_blocos: tuple[str, ...] = ()    # blocos que precisam ter sido aplicados antes
    categoria: Categoria = "boa_pratica"   # NÃO é mostrada antes de aplicar (ver 7.3)
    feedback: str = ""         # explicação da consequência, mostrada DEPOIS de aplicar
    pergunta_reflexao: str = ""  # pergunta curta para o participante pensar

@dataclass(frozen=True)
class Theme:
    id: str
    nome: str                  # ex.: "Telecom: quem vai cancelar?"
    dominio: str
    arquivo: str               # caminho em data/
    fonte: str                 # URL do Kaggle
    licenca: str
    alvo: str                  # coluna alvo original
    descricao_base: str
    dicionario: dict[str, str] # coluna -> significado em português
    problematica: str
    proposta_inicial: list[str]        # escopo mínimo da entrega
    aprofundamentos: list[str]         # opções para quem quiser ir além
    colunas_vazamento: tuple[str, ...] # colunas que não podem virar entrada de modelo
    blocos: tuple[Block, ...]
    regras_checklist: tuple["Check", ...]
    spec_defaults: dict                # sugestões pré-preenchidas no assistente (seção 9)

@dataclass
class StepResult:
    block_id: str
    linhas_antes: int; linhas_depois: int
    colunas_antes: int; colunas_depois: int
    nulos_antes: int; nulos_depois: int
    colunas_criadas: list[str]; colunas_removidas: list[str]
    tipos_alterados: dict[str, tuple[str, str]]
    erro: str | None = None

@dataclass(frozen=True)
class Check:
    id: str
    titulo: str
    nivel: Literal["erro", "alerta", "info"]
    funcao: Callable[[pd.DataFrame, pd.DataFrame, list[str]], tuple[bool, str]]
    # recebe (df_original, df_tratado, ids_dos_blocos_aplicados) e devolve (passou, mensagem)
    explicacao: str            # "por que isso importa"
```

### 5.1 Execução dos blocos (regra crítica)
- O campo `codigo` é **a única fonte da verdade**: o executor roda exatamente o texto exibido, com
  `exec(block.codigo, {"pd": pd, "np": np}, ns)` onde `ns = {"df": df.copy()}`, e lê `ns["df"]` no fim.
- O código dos blocos é escrito por nós (nunca pelo usuário), então o `exec` é aceitável. Não exponha nenhum campo de texto que seja executado.
- Todo bloco deve funcionar sobre um `df` que contenha as colunas de `requer_colunas`. Se faltar coluna ou bloco pré-requisito, o bloco aparece **desabilitado** com o motivo ("Este bloco precisa da coluna `dias_espera`. Aplique antes o bloco N05.") — isso ensina ordem de operações.
- Se o `exec` levantar exceção, o passo **não** é adicionado, o DataFrame não muda e a mensagem é mostrada em linguagem simples, com o erro técnico num `st.expander`.

---

## 6. Fluxo da aplicação (etapas)

Barra de progresso fixa no topo com as etapas:
`0 Boas-vindas → 1 Desafio → 2 Diagnóstico → 3 Tratamento → 4 Checklist → 5 Spec → 6 Exportar`.

Navegação: botões "Voltar" e "Avançar" no rodapé de cada etapa. "Avançar" só é liberado quando a etapa tem o mínimo (ver cada etapa). Trocar de desafio na etapa 1 depois de já ter tratado dados pede confirmação e zera o pipeline e a spec.

### Etapa 0 — Boas-vindas (1 tela)
- Título, objetivo da jornada em 3 linhas, os 2 arquivos que serão gerados, tempo estimado (≈ 60 min).
- Campo "Nome da equipe" (obrigatório; usado no nome dos arquivos e na SPEC).
- Caixa "Como funciona": blocos certos e **armadilhas** estão misturados de propósito; o app vai executar o que você escolher.

### Etapa 1 — Escolha do desafio
- 3 cartões lado a lado (um por tema): nome, domínio, frase da problemática, tamanho da base, ícone/emoji.
- Ao escolher: mostra **Problemática**, **Proposta inicial de entrega** (lista), **Aprofundamentos opcionais** e link da fonte.
- Mínimo para avançar: um tema escolhido.

### Etapa 2 — Diagnóstico (EDA visual)
Gerado por `core/diagnostics.py` para qualquer tema:
- Métricas: nº de linhas, nº de colunas, % de células nulas, nº de linhas duplicadas, colunas numéricas vs texto.
- Tabela "Raio-X das colunas": coluna, significado (do `dicionario`), tipo pandas, % nulos, nº de valores distintos, exemplo de valor, alerta.
- Alertas automáticos (cada um com ícone e uma frase em linguagem simples):
  - coluna de texto cujos valores parecem números (≥ 90% convertíveis com `pd.to_numeric(errors="coerce")` após `str.strip()`);
  - coluna com > 50% de nulos;
  - linhas totalmente duplicadas;
  - valores negativos em colunas numéricas;
  - coluna de texto que parece data;
  - coluna com 1 valor só;
  - coluna em `colunas_vazamento` → "⚠️ Esta coluna revela o resultado. Ela pode existir no CSV, mas não pode ser usada para prever o alvo."
- Gráficos: distribuição do alvo (barras com %), e um seletor de coluna que mostra histograma (numérica) ou barras dos 15 valores mais frequentes (texto).
- Amostra: `st.dataframe(df.head(20))`.
- Caixa "Por que diagnosticar antes de tratar?" (3 linhas).
- Mínimo para avançar: marcar o checkbox "Li o diagnóstico e anotei os problemas que encontrei" (obrigatório, para criar o hábito).

### Etapa 3 — Tratamento em blocos (low-code)
Layout em duas colunas:
- **Esquerda — Catálogo**: blocos agrupados por `grupo` em `st.expander`. Cada bloco mostra título, explicação, botão "Ver código" (mostra `codigo` com `st.code(language="python")`) e botão "Aplicar". A **categoria não aparece** antes de aplicar.
- **Direita — Meu pipeline**: lista ordenada dos passos aplicados; cada passo tem: título, selo da categoria (revelado), métricas antes×depois, `feedback`, `pergunta_reflexao` e botão "Desfazer este passo" (remove o passo e reexecuta os seguintes a partir da base original; se algum seguinte ficar inválido por falta de coluna, ele também é removido e isso é avisado).
- Abaixo: "Base atual" com métricas (linhas, colunas, nulos, % de linhas mantidas em relação à original) e `st.dataframe` com as 20 primeiras linhas; botão "Ver código completo do pipeline" com a concatenação dos `codigo` aplicados, na ordem.
- Selos após aplicar: ✅ Boa prática (verde) · ⚠️ Armadilha (vermelho) · 🤔 Depende do objetivo (amarelo).
- Ao aplicar uma armadilha: `st.warning` com o `feedback` e sugestão do bloco correto ("Experimente o bloco T02").
- Um bloco não pode ser aplicado duas vezes (botão vira "Aplicado").
- Mínimo para avançar: pelo menos 1 bloco aplicado.

### Etapa 4 — Checklist de qualidade
- Executa `core/checklist.py` sobre (df_original, df_atual, blocos_aplicados).
- Mostra um placar: nº de ✅ passou, ⚠️ alertas, ❌ erros, e uma "nota de qualidade" 0–100 (100 − 25×erros − 10×alertas, mínimo 0).
- Cada item: título, resultado, mensagem calculada e "Por que isso importa?".
- Para cada **erro** ou **alerta**, o participante escolhe: "Vou corrigir" (botão leva de volta à etapa 3) ou "Vou manter" + campo de justificativa (mínimo 15 caracteres). As justificativas vão para a SPEC.md.
- Mínimo para avançar: todo erro/alerta corrigido ou justificado.

### Etapa 5 — Assistente da SPEC (wizard)
- Passos descritos na seção 9. Cada passo: pergunta, campos, sugestões pré-preenchidas do tema (editáveis), caixa "💡 Por que isso importa?" e, à direita, **preview da SPEC.md atualizado em tempo real** (`st.markdown` dentro de um container com rolagem; alternar para "ver como texto" com `st.code(language="markdown")`).
- Mínimo para avançar: campos obrigatórios de todos os passos preenchidos.

### Etapa 6 — Exportar
- Resumo final: tema, nº de blocos aplicados (por categoria), nota do checklist, linhas mantidas.
- Dois `st.download_button`:
  - `dados_tratados.csv` (UTF-8 com BOM `utf-8-sig`, separador vírgula, sem índice);
  - `SPEC.md` (UTF-8).
- Nomes: `<equipe>_dados_tratados.csv` e `<equipe>_SPEC.md` (equipe em minúsculas, sem acentos, espaços → `_`).
- Instruções de próximo passo (texto fixo): criar uma pasta, colocar os dois arquivos, abrir o Claude Code nela e enviar o prompt sugerido:
  `Leia SPEC.md e construa a aplicação descrita usando apenas dados_tratados.csv. Siga os critérios de aceitação e não invente dados.`
  (o prompt aparece num `st.code` para copiar).

---

## 7. Regras de tratamento e feedback

### 7.1 Métricas antes × depois (executor)
Para cada passo calcular e exibir: linhas, colunas, total de nulos, colunas criadas, colunas removidas, colunas que mudaram de tipo. Se o passo remover > 20% das linhas, mostrar `st.error` "Este passo removeu X% da base".

### 7.2 Desfazer
Reexecutar a lista de passos restantes a partir de `df_original.copy()`. Não guardar um DataFrame por passo.

### 7.3 Revelação da categoria
A categoria e o `feedback` só aparecem depois de aplicar. Isso é intencional: o participante decide com base na explicação e no diagnóstico, e depois vê a consequência.

---

## 8. Catálogo de temas e blocos

Os números entre parênteses (ex.: "~11 linhas") são referência para conferência; o app sempre mostra o valor real calculado.

Nas tabelas, `<br>` separa as linhas de um mesmo trecho de código; ao implementar, cada segmento entre crases é uma linha (mantenha a indentação do `for` no T13). "Requer" lista colunas e, depois de ";", blocos pré-requisito. Todos os trechos foram testados com pandas 2.x em dados com as mesmas colunas.

### 8.1 Tema `telco` — Telecom: quem vai cancelar?
- Arquivo: `data/telco_churn.csv` — base completa (7.043 linhas, 21 colunas).
- Fonte: https://www.kaggle.com/datasets/blastchar/telco-customer-churn
- Alvo: `Churn` (Yes/No, ~26,5% Yes).
- Colunas de vazamento: nenhuma na base original (o vazamento aparece pelo bloco T09).
- Problemática: a operadora perde ~1 em cada 4 clientes e não sabe quais perfis cancelam mais nem onde agir primeiro.
- Proposta inicial de entrega: painel com taxa de churn geral e por tipo de contrato, forma de pagamento e faixa de tempo de casa; filtros na barra lateral; lista de clientes ativos com perfil de maior risco (regra simples baseada nos segmentos de maior churn).
- Aprofundamentos: simulador "e se" de retenção (ex.: migrar X% dos contratos mensais para anuais); estimativa de receita mensal em risco.

| ID | Grupo | Título | Categoria | Requer | Código | Feedback (após aplicar) |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | Tipos | Converter `TotalCharges` para número | boa_pratica | TotalCharges | `df["TotalCharges"] = pd.to_numeric(df["TotalCharges"].astype(str).str.strip(), errors="coerce")` | A coluna era texto por causa de ~11 espaços em branco. Agora é numérica e esses casos viraram nulos visíveis — o problema apareceu, falta decidir o que fazer com ele. |
| T02 | Valores ausentes | Preencher `TotalCharges` vazio com 0 quando `tenure` = 0 | boa_pratica | TotalCharges, tenure; bloco T01 | `df.loc[df["TotalCharges"].isna() & (df["tenure"] == 0), "TotalCharges"] = 0` | Regra de negócio: cliente recém-chegado ainda não foi cobrado. Nenhuma linha perdida e o valor faz sentido. |
| T03 | Valores ausentes | Preencher `TotalCharges` vazio com a média | armadilha | TotalCharges; bloco T01 | `df["TotalCharges"] = df["TotalCharges"].fillna(df["TotalCharges"].mean())` | Clientes com 0 meses de casa passaram a ter ~2.280 de cobrança acumulada. A média "tapa o buraco" mas inventa um valor impossível. |
| T04 | Valores ausentes | Remover linhas com qualquer valor vazio | depende | bloco T01 | `df = df.dropna()` | Removeu só as ~11 linhas de clientes novos. Aqui o impacto é pequeno, mas você apagou justamente um grupo (recém-chegados). Em outras bases o mesmo comando apaga quase tudo. |
| T05 | Variáveis | Padronizar `SeniorCitizen` para Yes/No | boa_pratica | SeniorCitizen | `df["SeniorCitizen"] = df["SeniorCitizen"].map({0: "No", 1: "Yes"})` | Todas as colunas sim/não agora usam o mesmo padrão, o que evita confusão em filtros e gráficos. |
| T06 | Variáveis | Unificar "No internet service" e "No phone service" em "No" | boa_pratica | OnlineSecurity | `cols = ["MultipleLines","OnlineSecurity","OnlineBackup","DeviceProtection","TechSupport","StreamingTV","StreamingMovies"]`<br>`df[cols] = df[cols].replace({"No internet service": "No", "No phone service": "No"})` | Três categorias diziam a mesma coisa. Agora os gráficos não dividem o "não" em três barras. |
| T07 | Alvo | Converter `Churn` para 0/1 | boa_pratica | Churn | `df["Churn"] = df["Churn"].map({"Yes": 1, "No": 0})` | Com 0/1, a média da coluna já é a taxa de churn. Facilita cálculos no app final. |
| T08 | Estrutura | Remover `customerID` | depende | customerID | `df = df.drop(columns=["customerID"])` | Para um modelo, o ID não ajuda. Mas a proposta pede uma **lista de clientes em risco** — sem ID, o app final não consegue dizer quem são eles. |
| T09 | Variáveis | Criar "taxa de churn por forma de pagamento" como nova coluna | armadilha | Churn, PaymentMethod | `df["taxa_churn_pagamento"] = df.groupby("PaymentMethod")["Churn"].transform(lambda s: s.astype(str).isin(["Yes", "1"]).mean())` | Vazamento de dados: a coluna foi calculada a partir do próprio resultado (`Churn`). Qualquer modelo que a use "cola" a resposta e parece ótimo, mas falha com clientes novos. |
| T10 | Outliers | Remover "outliers" de `MonthlyCharges` (z-score > 1,5) | armadilha | MonthlyCharges | `z = (df["MonthlyCharges"] - df["MonthlyCharges"].mean()) / df["MonthlyCharges"].std()`<br>`df = df[z.abs() <= 1.5]` | Removeu clientes legítimos de mensalidade alta ou baixa — não eram erros, eram clientes reais (e muitos dos que mais cancelam). Outlier se investiga antes de apagar. |
| T11 | Variáveis | Transformar todas as colunas de texto em colunas 0/1 (one-hot) | armadilha | — | `df = pd.get_dummies(df, columns=df.select_dtypes("object").columns.tolist())` | A base explodiu para milhares de colunas porque o `customerID` (único por linha) também foi transformado. O CSV fica ilegível para o app final. |
| T12 | Variáveis | Criar faixa de tempo de casa (`faixa_tenure`) | boa_pratica | tenure | `df["faixa_tenure"] = pd.cut(df["tenure"], bins=[-1, 12, 24, 48, 72], labels=["0-12 meses", "13-24 meses", "25-48 meses", "49-72 meses"])`<br>`df["faixa_tenure"] = df["faixa_tenure"].astype(str)` | Agrupar facilita ver que o churn se concentra nos primeiros meses. |
| T13 | Variáveis | Normalizar `MonthlyCharges` e `TotalCharges` entre 0 e 1 | depende | MonthlyCharges, TotalCharges; bloco T01 | `for c in ["MonthlyCharges", "TotalCharges"]:`<br>`    df[c] = (df[c] - df[c].min()) / (df[c].max() - df[c].min())` | Útil para alguns modelos, mas o painel final perde os valores em dinheiro. Se o objetivo é um dashboard, prefira manter os valores reais. |

Regras de checklist do tema (além das genéricas, seção 8.4):
- ❌ `taxa_churn_pagamento` existe → "Coluna derivada do alvo (vazamento)."
- ❌ `TotalCharges` não é numérica.
- ⚠️ `customerID` ausente → "A proposta pede lista de clientes; sem ID ela não é possível."
- ⚠️ algum cliente com `tenure == 0` e `TotalCharges > 0`.
- ⚠️ mais de 50 colunas.

### 8.2 Tema `hotel` — Turismo: por que as reservas são canceladas?
- Arquivo: `data/hotel_bookings.csv` — **amostra de 30.000 linhas** (seed 42) da base original (119.390 linhas, 32 colunas).
- Fonte: https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand (artigo original: Antonio, Almeida e Nunes, *Data in Brief*, 2019).
- Alvo: `is_canceled` (0/1, ~37% cancelado).
- Colunas de vazamento: `reservation_status`, `reservation_status_date`.
- Problemática: dois hotéis em Portugal perdem receita com cancelamentos (~37% das reservas) e não sabem quais reservas têm mais risco.
- Proposta inicial de entrega: painel com taxa de cancelamento por hotel, mês de chegada, antecedência da reserva (faixas de `lead_time`), tipo de depósito e canal de venda; filtros; ranking dos segmentos de maior risco.
- Aprofundamentos: estimativa de receita perdida (`adr` × noites das reservas canceladas); calendário de ocupação por mês.

| ID | Grupo | Título | Categoria | Requer | Código | Feedback |
| --- | --- | --- | --- | --- | --- | --- |
| H01 | Valores ausentes | Preencher `children` vazio com 0 | boa_pratica | children | `df["children"] = df["children"].fillna(0).astype(int)` | Poucos casos; 0 crianças é a leitura mais provável e a coluna volta a ser inteira. |
| H02 | Valores ausentes | Preencher `country` vazio com "Desconhecido" | boa_pratica | country | `df["country"] = df["country"].fillna("Desconhecido")` | Mantém as linhas e deixa explícito que o país não foi informado. |
| H03 | Valores ausentes | Tratar `agent` vazio como "Sem agente" | boa_pratica | agent | `df["agent"] = df["agent"].fillna(0).astype(int).astype(str).replace("0", "Sem agente")` | Aqui o vazio tem significado: reserva feita sem agência. Apagar ou preencher com média destruiria essa informação. |
| H04 | Estrutura | Remover a coluna `company` | boa_pratica | company | `df = df.drop(columns=["company"])` | ~94% vazia. Remover a coluna preserva todas as linhas. |
| H05 | Valores ausentes | Remover linhas com qualquer valor vazio | armadilha | — | `df = df.dropna()` | Como `company` está vazia em quase todas as reservas, este comando apagou mais de 90% da base. Sempre olhe de onde vêm os nulos antes de um `dropna()`. |
| H06 | Datas | Criar a data de chegada `arrival_date` | boa_pratica | arrival_date_year, arrival_date_month, arrival_date_day_of_month | `meses = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6, "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}`<br>`df["arrival_date"] = pd.to_datetime(dict(year=df["arrival_date_year"], month=df["arrival_date_month"].map(meses), day=df["arrival_date_day_of_month"]))` | A data estava espalhada em 3 colunas (e o mês em texto em inglês). Agora dá para fazer séries no tempo e ordenar corretamente. |
| H07 | Variáveis | Criar colunas 0/1 a partir de `reservation_status` para enriquecer a análise | armadilha | reservation_status | `df = pd.get_dummies(df, columns=["reservation_status"], prefix="status")` | Vazamento: `reservation_status` diz se a reserva foi cancelada — é o próprio resultado. `status_Canceled` é praticamente igual a `is_canceled`. |
| H08 | Estrutura | Remover `reservation_status` e `reservation_status_date` | boa_pratica | reservation_status, reservation_status_date | `df = df.drop(columns=["reservation_status", "reservation_status_date"])` | Essas colunas só são conhecidas depois do desfecho da reserva. Removê-las evita que o app final "preveja" com informação do futuro. |
| H09 | Linhas inválidas | Remover reservas sem nenhum hóspede | boa_pratica | adults, children, babies | `df = df[(df["adults"] + df["children"].fillna(0) + df["babies"]) > 0]` | Reservas com 0 adultos, 0 crianças e 0 bebês são registros inválidos. |
| H10 | Outliers | Remover diárias (`adr`) negativas ou acima de 1.000 | boa_pratica | adr | `df = df[(df["adr"] >= 0) & (df["adr"] <= 1000)]` | Diária negativa é erro de registro e a original tem uma diária de 5.400, muito acima das demais. Poucas linhas, grande efeito nas médias. |
| H11 | Outliers | Remover reservas com diária (`adr`) igual a 0 | armadilha | adr | `df = df[df["adr"] != 0]` | Diária 0 é legítima (cortesias, pacotes, funcionários). Você removeu reservas reais e distorceu a taxa de cancelamento. |
| H12 | Duplicados | Remover linhas duplicadas | depende | — | `df = df.drop_duplicates()` | A base não tem ID de reserva: linhas iguais podem ser reservas diferentes de um mesmo grupo. Remover reduz bastante a base; manter pode inflar contagens. Justifique sua escolha. |
| H13 | Variáveis | Padronizar `meal` "Undefined" como "SC" (sem refeição) | boa_pratica | meal | `df["meal"] = df["meal"].replace("Undefined", "SC")` | Segundo a documentação da base, "Undefined" e "SC" significam o mesmo: sem refeição. |
| H14 | Variáveis | Criar total de noites (`total_noites`) | boa_pratica | stays_in_weekend_nights, stays_in_week_nights | `df["total_noites"] = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]` | Base para calcular receita da reserva (`adr` × noites). |

Regras de checklist do tema:
- ❌ `reservation_status` ou `reservation_status_date` ou qualquer coluna iniciada por `status_` presente.
- ❌ menos de 50% das linhas originais mantidas.
- ⚠️ `adr` com valor negativo.
- ⚠️ `arrival_date` ausente.
- ⚠️ `children` com nulos.

### 8.3 Tema `noshow` — Saúde pública: quem falta às consultas?
- Arquivo: `data/noshow_consultas.csv` — **amostra de 30.000 linhas** (seed 42) da base original (110.527 linhas, 14 colunas, consultas em Vitória-ES, 2016).
- Fonte: https://www.kaggle.com/datasets/joniarroba/noshowappointments
- Alvo: `No-show` — **atenção: "Yes" significa que o paciente FALTOU** (~20%).
- Colunas de vazamento: nenhuma na base original.
- Problemática: cerca de 1 em cada 5 consultas agendadas no SUS tem falta, desperdiçando horários que poderiam atender outros pacientes.
- Proposta inicial de entrega: painel com taxa de falta por tempo de espera (faixas), dia da semana, faixa etária, recebimento de SMS e bairro (top 10); filtros; lista de consultas futuras com perfil de maior risco para priorizar lembretes.
- Aprofundamentos: comparar efeito do SMS por faixa de espera; mapa/ranking de bairros.

| ID | Grupo | Título | Categoria | Requer | Código | Feedback |
| --- | --- | --- | --- | --- | --- | --- |
| N01 | Alvo | Criar coluna `faltou` (1 = faltou) | boa_pratica | No-show | `df["faltou"] = (df["No-show"] == "Yes").astype(int)` | Na base, "No-show = Yes" significa que o paciente **não** compareceu. Agora a média de `faltou` é a taxa de faltas (~20%). |
| N02 | Alvo | Criar coluna `compareceu` a partir de `No-show` | armadilha | No-show | `df["compareceu"] = (df["No-show"] == "Yes").astype(int)` | Leitura invertida: o nome sugere presença, mas o valor 1 marca quem faltou. Pela sua coluna, só ~20% compareceram — o contrário da realidade. Sempre confira o dicionário de dados. |
| N03 | Datas | Converter `ScheduledDay` e `AppointmentDay` para data/hora | boa_pratica | ScheduledDay, AppointmentDay | `df["ScheduledDay"] = pd.to_datetime(df["ScheduledDay"])`<br>`df["AppointmentDay"] = pd.to_datetime(df["AppointmentDay"])` | Eram texto. Agora dá para calcular intervalos e extrair dia da semana. |
| N04 | Variáveis | Calcular dias de espera (comparando só as datas) | boa_pratica | ScheduledDay; bloco N03 | `df["dias_espera"] = (df["AppointmentDay"].dt.normalize() - df["ScheduledDay"].dt.normalize()).dt.days` | `AppointmentDay` não tem horário (vem como 00:00). Comparar só as datas faz consultas no mesmo dia valerem 0. |
| N05 | Variáveis | Calcular dias de espera (subtração direta) | armadilha | ScheduledDay; bloco N03 | `df["dias_espera"] = (df["AppointmentDay"] - df["ScheduledDay"]).dt.days` | Como a consulta vem sem horário, quem agendou e foi atendido no mesmo dia ficou com −1 dia de espera. Um terço da base virou "espera negativa". |
| N06 | Linhas inválidas | Remover consultas com espera negativa | boa_pratica | dias_espera | `df = df[df["dias_espera"] >= 0]` | Com N04, remove só os poucos registros inconsistentes (consulta antes do agendamento). Se você usou N05, este bloco apaga um terço da base — olhe a métrica de linhas removidas. |
| N07 | Linhas inválidas | Remover idade negativa | boa_pratica | Age | `df = df[df["Age"] >= 0]` | Existe idade −1 na base: erro de cadastro. |
| N08 | Linhas inválidas | Remover pacientes com idade 0 | armadilha | Age | `df = df[df["Age"] > 0]` | Idade 0 são bebês com menos de 1 ano — pacientes reais de pediatria. Você removeu um grupo inteiro da análise. |
| N09 | Duplicados | Remover pacientes repetidos (`PatientId`) | armadilha | PatientId | `df = df.drop_duplicates(subset="PatientId")` | Cada linha é uma **consulta**, não um paciente. Pacientes com várias consultas são normais (e importantes para entender faltas recorrentes). Você apagou grande parte da base. |
| N10 | Tipos | Converter `PatientId` para texto | boa_pratica | PatientId | `df["PatientId"] = df["PatientId"].astype("int64").astype(str)` | O ID estava como número decimal (aparece em notação científica em planilhas). ID não é para fazer conta. |
| N11 | Variáveis | Criar dia da semana da consulta | boa_pratica | AppointmentDay; bloco N03 | `dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]`<br>`df["dia_semana"] = df["AppointmentDay"].dt.dayofweek.map(dict(enumerate(dias)))` | Permite analisar se a falta varia ao longo da semana. |
| N12 | Variáveis | Criar faixa etária | boa_pratica | Age | `df["faixa_etaria"] = pd.cut(df["Age"], bins=[-1, 12, 18, 30, 45, 60, 200], labels=["0-12", "13-18", "19-30", "31-45", "46-60", "61+"]).astype(str)` | Faixas tornam o painel mais legível que 100 idades diferentes. |
| N13 | Variáveis | Transformar `Handcap` em sim/não (`tem_deficiencia`) | depende | Handcap | `df["tem_deficiencia"] = (df["Handcap"] > 0).astype(int)`<br>`df = df.drop(columns=["Handcap"])` | `Handcap` vai de 0 a 4 (nº de deficiências), não é 0/1 como as outras. Binarizar simplifica, mas perde a quantidade. |
| N14 | Estrutura | Renomear colunas para português e corrigir grafia | boa_pratica | Hipertension | `df = df.rename(columns={"PatientId": "id_paciente", "AppointmentID": "id_consulta", "Gender": "sexo", "ScheduledDay": "data_agendamento", "AppointmentDay": "data_consulta", "Age": "idade", "Neighbourhood": "bairro", "Scholarship": "bolsa_familia", "Hipertension": "hipertensao", "Diabetes": "diabetes", "Alcoholism": "alcoolismo", "Handcap": "deficiencias", "SMS_received": "recebeu_sms", "No-show": "no_show_original"})` | Nomes claros ajudam o agente de código e quem lê o painel. Repare que os blocos que dependem dos nomes antigos ficaram desabilitados: a ordem das operações importa. |

Regras de checklist do tema:
- ❌ coluna `compareceu` presente.
- ❌ `dias_espera` com valores negativos.
- ❌ menos de 70% das linhas originais mantidas.
- ⚠️ alvo `faltou` ausente.
- ⚠️ `Age`/`idade` com valor negativo.

### 8.4 Regras genéricas de checklist (todos os temas)
| ID | Nível | Regra | Por que importa |
| --- | --- | --- | --- |
| G01 | erro | O alvo do tema (ou sua versão tratada) ainda existe | Sem a coluna de resultado, o app final não calcula taxas. |
| G02 | erro | Nenhuma coluna de `colunas_vazamento` (nem derivada) presente | Vazamento faz qualquer análise preditiva parecer perfeita e falhar na prática. |
| G03 | alerta | ≥ 80% das linhas originais mantidas | Remover muitas linhas pode enviesar o resultado. |
| G04 | alerta | Nenhum nulo restante | Nulos geram erros e gráficos incompletos no app final. |
| G05 | alerta | Nenhuma coluna de texto que parece número | Números como texto não somam nem fazem média. |
| G06 | alerta | ≤ 60 colunas | Bases muito largas confundem o agente e quem lê o painel. |
| G07 | info | Lista de blocos aplicados por categoria | Registro das decisões para a avaliação. |

---

## 9. Assistente da SPEC (core/spec_builder.py)

Oito passos. Cada passo tem: título, pergunta, campos, `spec_defaults` do tema como valor inicial, texto "💡 Por que isso importa?" e campos obrigatórios (*).

| Passo | Pergunta | Campos | Por que isso importa? (texto exibido) |
| --- | --- | --- | --- |
| 1. Problema | Que problema sua solução resolve, e para quem? | Problema* (texto), Usuário principal* (seleção: gestor, atendente, analista, outro + texto) | Um agente de código sem problema claro constrói "qualquer coisa que funcione". O problema é a bússola de todas as decisões. |
| 2. Objetivo e escopo | O que entra na primeira versão? | Itens da proposta inicial (checkboxes, todos marcados por padrão)*, Aprofundamentos escolhidos (checkboxes), Fora do escopo (texto) | Escopo explícito evita que o agente gaste tempo em funcionalidades que ninguém pediu. Dizer o que NÃO fazer é tão importante quanto o que fazer. |
| 3. Dados | (gerado automaticamente) Confirme o dicionário das colunas do seu CSV | Tabela editável: coluna, tipo, significado (pré-preenchido do `dicionario`; colunas criadas pelos blocos têm descrição padrão do bloco) | O agente só conhece seus dados pelo que você descreve. Colunas sem significado viram suposições — e suposições viram alucinações. |
| 4. Funcionalidades | O que o usuário consegue fazer na aplicação? | Lista de funcionalidades (sugestões do tema, editáveis; adicionar/remover)* | Cada funcionalidade vira uma tarefa verificável para o agente. |
| 5. Regras de negócio | Quais regras a solução deve respeitar? | Lista de regras (sugestões do tema; ex.: "taxa de churn = clientes com Churn=1 ÷ total do filtro")* | Regras escritas impedem que o agente invente fórmulas. É aqui que o resultado fica correto, não só bonito. |
| 6. Arquitetura e restrições | Como a solução deve ser construída? | Stack (padrão: Python + Streamlit + pandas + plotly; editável), Restrições (checkboxes pré-marcadas: usar só o CSV fornecido; não inventar dados; não usar APIs externas; não alterar o CSV; código em um único `app.py` se possível) | Restrições reduzem o espaço de erro do agente. Sem elas, ele pode buscar dados na internet ou criar uma estrutura complexa demais para 1 hora. |
| 7. Critérios de aceitação e métricas | Como saberemos que ficou pronto e correto? | Critérios (lista no formato "Dado/Quando/Então" ou frases verificáveis; sugestões do tema)*, Métrica de sucesso do negócio (texto) | Critério verificável é o que permite conferir o trabalho do agente. "Ficar bonito" não é verificável; "o painel mostra a taxa geral de 26,5% sem filtros" é. |
| 8. Apresentação | Como a equipe vai apresentar? | Formato (pitch de 3 min, padrão), Roteiro (problema → dados → decisão de tratamento → demo → impacto) editável | A apresentação é parte da entrega. Planejar o roteiro agora orienta o que a aplicação precisa mostrar. |

`spec_defaults` de cada tema deve conter: problema, usuario, funcionalidades (≥ 4), regras_negocio (≥ 3), criterios_aceitacao (≥ 4), metrica_sucesso. Escreva-os coerentes com a Problemática e a Proposta inicial da seção 8. Exemplo (telco):
- Regras: "Taxa de churn = soma de Churn (0/1) ÷ nº de clientes do filtro"; "Cliente em risco = contrato mensal E tempo de casa ≤ 12 meses E sem suporte técnico"; "Valores em moeda exibidos com 2 casas decimais".
- Critérios: "Sem filtros, o painel mostra a taxa de churn geral calculada do CSV"; "Ao filtrar por contrato, todos os gráficos se atualizam"; "A lista de risco mostra customerID, contrato, tenure e MonthlyCharges"; "O app abre sem erros com `streamlit run app.py`".

### 9.1 Template da SPEC.md gerada
O texto entre `{ }` é preenchido pelo app. Seções vazias não aparecem.

```markdown
# SPEC — {nome_da_solucao}
Equipe: {equipe} · Desafio: {tema.nome} · Gerado em {data}

## 1. Contexto e problema
{problema}
Usuário principal: {usuario}

## 2. Objetivo e escopo
### Entra nesta versão
- {itens da proposta inicial marcados}
- {aprofundamentos escolhidos}
### Fora do escopo
- {fora_escopo}

## 3. Dados
Arquivo: `dados_tratados.csv` — {linhas} linhas, {colunas} colunas. Alvo: `{coluna_alvo}`.
| Coluna | Tipo | Significado |
| --- | --- | --- |
{uma linha por coluna}

### 3.1 Tratamentos já aplicados (não refazer)
{lista numerada: título do bloco — categoria — feedback resumido}
### 3.2 Decisões conscientes e justificativas
{alertas/erros do checklist mantidos + justificativa do participante}
### 3.3 Cuidados com os dados
- Não usar como entrada de previsão: {colunas de vazamento, se houver}
- {observações automáticas, ex.: "idade 0 = bebês, é válido"}

## 4. Funcionalidades
1. {funcionalidade}

## 5. Regras de negócio
- {regra}

## 6. Arquitetura e restrições
- Stack: {stack}
- {restrições marcadas}

## 7. Critérios de aceitação
- [ ] {critério}
Métrica de sucesso: {metrica}

## 8. Apresentação
Formato: {formato}
Roteiro: {roteiro}

## 9. Instruções para o agente de código
1. Leia esta SPEC inteira antes de escrever código.
2. Use somente `dados_tratados.csv`; não invente, baixe ou gere dados.
3. Implemente primeiro o escopo da seção 2 e confira cada critério da seção 7.
4. Se algo estiver ambíguo, escolha a opção mais simples e registre a suposição no README.
```

---

## 10. Exportação (core/exporter.py)
- `gerar_csv(df) -> bytes`: `df.to_csv(index=False).encode("utf-8-sig")`. Colunas de data saem em ISO (`YYYY-MM-DD` ou `YYYY-MM-DD HH:MM:SS`).
- `gerar_spec(estado) -> str`: aplica o template 9.1.
- A seção 3 da SPEC é **sempre** gerada do DataFrame final real (nomes, tipos e contagens), nunca digitada.

---

## 11. Requisitos não funcionais
- Português do Brasil em toda a interface.
- Layout `st.set_page_config(layout="wide")`; tema escuro ou claro do Streamlit, sem CSS complexo.
- Funcionar no Chrome/Edge em Windows 10/11, em telas de 1366×768.
- Nenhum dado pessoal é coletado além do nome da equipe; nada é salvo no servidor.
- Tratamento de erros: nenhuma exceção não tratada pode aparecer para o participante.

---

## 12. Dados e preparação (scripts/preparar_dados.py)
- Entrada: CSVs originais baixados do Kaggle em `data/raw/` (pasta ignorada pelo git):
  - `WA_Fn-UseC_-Telco-Customer-Churn.csv`
  - `hotel_bookings.csv`
  - `KaggleV2-May-2016.csv`
- Saída em `data/`:
  - `telco_churn.csv` — cópia integral.
  - `hotel_bookings.csv` — `df.sample(n=30000, random_state=42)` **sem** limpar nada.
  - `noshow_consultas.csv` — `df.sample(n=30000, random_state=42)` **sem** limpar nada.
- O script imprime, para cada saída: linhas, colunas, % nulos, nº de duplicados — e confere que os "defeitos" esperados continuam presentes (ex.: `TotalCharges` com espaços; `company` com > 80% nulos; `Age` com valores ≤ 0; `reservation_status` presente). Se algum defeito sumir na amostra, falhar com mensagem clara.

---

## 13. Marcos de implementação (ordem obrigatória)

Cada marco termina com o app rodando (`streamlit run app.py`) e os testes passando.

1. **M1 — Esqueleto e dados**: estrutura de pastas, `requirements.txt`, `models.py`, `preparar_dados.py`, `themes/telco.py` completo, navegação entre etapas com `session_state`, etapas 0 e 1.
2. **M2 — Diagnóstico**: `diagnostics.py` + etapa 2 para o tema telco.
3. **M3 — Tratamento**: `executor.py` (aplicar, métricas, desfazer, pré-requisitos) + etapa 3. Testes: todo bloco do telco executa na base real; armadilhas produzem o efeito descrito.
4. **M4 — Checklist**: `checklist.py` + etapa 4 com justificativas.
5. **M5 — Spec e exportação**: `spec_builder.py`, etapa 5 com preview ao vivo, `exporter.py`, etapa 6.
6. **M6 — Temas hotel e noshow**: catálogos completos das seções 8.2 e 8.3 + regras + `spec_defaults`. Testes para todos os blocos.
7. **M7 — Polimento e deploy**: textos, ícones, revisão de linguagem, `README.md` (como rodar, créditos e licenças das bases), deploy no Streamlit Community Cloud.

## 14. Testes de aceitação (mínimos)
- `test_blocks.py`: para cada tema, cada bloco executa sobre a base do repositório (respeitando pré-requisitos) sem exceção.
- Telco: após T01, `TotalCharges` é numérica e tem nulos; após T01+T02, não há nulos em `TotalCharges`; após T11, há > 1.000 colunas.
- Hotel: H05 mantém < 10% das linhas; após H08, colunas de vazamento ausentes; H06 gera `arrival_date` sem nulos.
- Noshow: N05 gera ≥ 25% de `dias_espera` negativos; N04 gera < 1% negativos; N09 remove ≥ 20% das linhas; média de `faltou` entre 0,15 e 0,25.
- `test_executor.py`: desfazer o passo k reproduz exatamente o resultado de aplicar os demais passos do zero; bloco sem pré-requisito fica desabilitado; exceção em bloco não altera o estado.
- `test_checklist.py`: base telco crua dispara G05; após T09, dispara G02/erro do tema.
- `test_spec_builder.py`: a SPEC gerada contém todas as colunas do DataFrame final na seção 3 e a lista de blocos aplicados na 3.1.
- Teste manual de ponta a ponta para cada tema, em < 15 min, sem erros.
