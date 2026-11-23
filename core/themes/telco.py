"""Tema telco — Telecom: quem vai cancelar? (seção 8.1 da APP_SPEC).

ATENÇÃO: o campo `codigo` de cada bloco é cópia literal da seção 8 da APP_SPEC.
Blocos de armadilha e "depende" são errados ou discutíveis DE PROPÓSITO (o app é didático).
Não corrija, melhore nem "otimize" esses trechos. tests/test_blocks.py confere o texto.
"""

import pandas as pd

from core.models import Block, Check, Theme

# ---------------------------------------------------------------------------
# Blocos
# ---------------------------------------------------------------------------

BLOCOS = (
    Block(
        id="T01",
        titulo="Converter `TotalCharges` para número",
        grupo="Tipos",
        explicacao=(
            "A coluna `TotalCharges` (total já cobrado do cliente) foi lida como texto. "
            "Este bloco tira espaços em branco e converte tudo para número. "
            "O que não for número vira vazio (nulo)."
        ),
        codigo='df["TotalCharges"] = pd.to_numeric(df["TotalCharges"].astype(str).str.strip(), errors="coerce")',
        requer_colunas=("TotalCharges",),
        categoria="boa_pratica",
        feedback=(
            "A coluna era texto por causa de ~11 espaços em branco. Agora é numérica e esses casos "
            "viraram nulos visíveis — o problema apareceu, falta decidir o que fazer com ele."
        ),
        pergunta_reflexao="Quem são os clientes que ficaram com `TotalCharges` vazio? O que eles têm em comum?",
    ),
    Block(
        id="T02",
        titulo="Preencher `TotalCharges` vazio com 0 quando `tenure` = 0",
        grupo="Valores ausentes",
        explicacao=(
            "Preenche com 0 o total cobrado apenas dos clientes que estão vazios E têm 0 meses de casa "
            "(`tenure` = 0). Os demais valores não mudam."
        ),
        codigo='df.loc[df["TotalCharges"].isna() & (df["tenure"] == 0), "TotalCharges"] = 0',
        requer_colunas=("TotalCharges", "tenure"),
        requer_blocos=("T01",),
        categoria="boa_pratica",
        feedback=(
            "Regra de negócio: cliente recém-chegado ainda não foi cobrado. "
            "Nenhuma linha perdida e o valor faz sentido."
        ),
        pergunta_reflexao="Que outra informação da base confirma que esses clientes acabaram de chegar?",
    ),
    Block(
        id="T03",
        titulo="Preencher `TotalCharges` vazio com a média",
        grupo="Valores ausentes",
        explicacao=(
            "Calcula a média de `TotalCharges` de todos os clientes e usa esse valor "
            "para preencher os campos vazios."
        ),
        codigo='df["TotalCharges"] = df["TotalCharges"].fillna(df["TotalCharges"].mean())',
        requer_colunas=("TotalCharges",),
        requer_blocos=("T01",),
        categoria="armadilha",
        feedback=(
            "Clientes com 0 meses de casa passaram a ter ~2.280 de cobrança acumulada. "
            "A média \"tapa o buraco\" mas inventa um valor impossível."
        ),
        pergunta_reflexao="Faz sentido um cliente que acabou de chegar já ter pago mais de 2 mil?",
        sugestao="T02",
    ),
    Block(
        id="T04",
        titulo="Remover linhas com qualquer valor vazio",
        grupo="Valores ausentes",
        explicacao="Apaga da base toda linha que tenha pelo menos um campo vazio, em qualquer coluna.",
        codigo="df = df.dropna()",
        requer_blocos=("T01",),
        categoria="depende",
        feedback=(
            "Removeu só as ~11 linhas de clientes novos. Aqui o impacto é pequeno, mas você apagou "
            "justamente um grupo (recém-chegados). Em outras bases o mesmo comando apaga quase tudo."
        ),
        pergunta_reflexao="Se o seu painel quisesse mostrar clientes novos, essas linhas fariam falta?",
    ),
    Block(
        id="T05",
        titulo="Padronizar `SeniorCitizen` para Yes/No",
        grupo="Variáveis",
        explicacao=(
            "`SeniorCitizen` (cliente idoso) usa 0 e 1, enquanto as outras colunas de sim/não usam "
            "\"Yes\" e \"No\". Este bloco troca 0 por \"No\" e 1 por \"Yes\"."
        ),
        codigo='df["SeniorCitizen"] = df["SeniorCitizen"].map({0: "No", 1: "Yes"})',
        requer_colunas=("SeniorCitizen",),
        categoria="boa_pratica",
        feedback=(
            "Todas as colunas sim/não agora usam o mesmo padrão, o que evita confusão em filtros e gráficos."
        ),
        pergunta_reflexao="Em quais outras colunas um mesmo significado aparece escrito de jeitos diferentes?",
    ),
    Block(
        id="T06",
        titulo="Unificar \"No internet service\" e \"No phone service\" em \"No\"",
        grupo="Variáveis",
        explicacao=(
            "Nas colunas de serviços adicionais, troca \"No internet service\" e \"No phone service\" "
            "por um simples \"No\"."
        ),
        codigo=(
            'cols = ["MultipleLines","OnlineSecurity","OnlineBackup","DeviceProtection","TechSupport","StreamingTV","StreamingMovies"]\n'
            'df[cols] = df[cols].replace({"No internet service": "No", "No phone service": "No"})'
        ),
        requer_colunas=("OnlineSecurity",),
        categoria="boa_pratica",
        feedback=(
            "Três categorias diziam a mesma coisa. Agora os gráficos não dividem o \"não\" em três barras."
        ),
        pergunta_reflexao="Que informação se perde ao juntar \"sem internet\" com \"não contratou\"? Ela importa para o seu painel?",
    ),
    Block(
        id="T07",
        titulo="Converter `Churn` para 0/1",
        grupo="Alvo",
        explicacao=(
            "`Churn` diz se o cliente cancelou (\"Yes\") ou não (\"No\"). "
            "Este bloco troca \"Yes\" por 1 e \"No\" por 0."
        ),
        codigo='df["Churn"] = df["Churn"].map({"Yes": 1, "No": 0})',
        requer_colunas=("Churn",),
        categoria="boa_pratica",
        feedback="Com 0/1, a média da coluna já é a taxa de churn. Facilita cálculos no app final.",
        pergunta_reflexao="Qual é a média da coluna `Churn` agora? O que esse número significa?",
    ),
    Block(
        id="T08",
        titulo="Remover `customerID`",
        grupo="Estrutura",
        explicacao="Apaga a coluna `customerID`, o código que identifica cada cliente.",
        codigo='df = df.drop(columns=["customerID"])',
        requer_colunas=("customerID",),
        categoria="depende",
        feedback=(
            "Para um modelo, o ID não ajuda. Mas a proposta pede uma **lista de clientes em risco** — "
            "sem ID, o app final não consegue dizer quem são eles."
        ),
        pergunta_reflexao="O seu app final precisa mostrar QUEM são os clientes, ou só quantos são?",
    ),
    Block(
        id="T09",
        titulo="Criar \"taxa de churn por forma de pagamento\" como nova coluna",
        grupo="Variáveis",
        explicacao=(
            "Calcula, para cada forma de pagamento, a proporção de clientes que cancelaram, "
            "e grava esse número numa nova coluna em cada linha."
        ),
        codigo='df["taxa_churn_pagamento"] = df.groupby("PaymentMethod")["Churn"].transform(lambda s: s.astype(str).isin(["Yes", "1"]).mean())',
        requer_colunas=("Churn", "PaymentMethod"),
        categoria="armadilha",
        feedback=(
            "Vazamento de dados: a coluna foi calculada a partir do próprio resultado (`Churn`). "
            "Qualquer modelo que a use \"cola\" a resposta e parece ótimo, mas falha com clientes novos."
        ),
        pergunta_reflexao="Para um cliente que acabou de chegar, você saberia o valor desta coluna?",
    ),
    Block(
        id="T10",
        titulo="Remover \"outliers\" de `MonthlyCharges` (z-score > 1,5)",
        grupo="Outliers",
        explicacao=(
            "Calcula o quanto cada mensalidade se afasta da média (o \"z-score\") e apaga os clientes "
            "cujo valor está a mais de 1,5 desvios-padrão da média, para cima ou para baixo."
        ),
        codigo=(
            'z = (df["MonthlyCharges"] - df["MonthlyCharges"].mean()) / df["MonthlyCharges"].std()\n'
            "df = df[z.abs() <= 1.5]"
        ),
        requer_colunas=("MonthlyCharges",),
        categoria="armadilha",
        feedback=(
            "Removeu clientes legítimos de mensalidade alta ou baixa — não eram erros, eram clientes reais "
            "(e muitos dos que mais cancelam). Outlier se investiga antes de apagar."
        ),
        pergunta_reflexao="Uma mensalidade alta é um erro de digitação ou um cliente com muitos serviços?",
    ),
    Block(
        id="T11",
        titulo="Transformar todas as colunas de texto em colunas 0/1 (one-hot)",
        grupo="Variáveis",
        explicacao=(
            "Para cada coluna de texto, cria uma coluna 0/1 para cada valor diferente "
            "(técnica chamada one-hot) e remove a coluna de texto original."
        ),
        codigo='df = pd.get_dummies(df, columns=df.select_dtypes("object").columns.tolist())',
        categoria="armadilha",
        feedback=(
            "A base explodiu para milhares de colunas porque o `customerID` (único por linha) também foi "
            "transformado. O CSV fica ilegível para o app final."
        ),
        pergunta_reflexao="Quantas colunas o seu CSV tem agora? Alguém conseguiria ler essa tabela?",
    ),
    Block(
        id="T12",
        titulo="Criar faixa de tempo de casa (`faixa_tenure`)",
        grupo="Variáveis",
        explicacao=(
            "Cria a coluna `faixa_tenure`, que agrupa os meses de casa (`tenure`) em 4 faixas: "
            "0-12, 13-24, 25-48 e 49-72 meses."
        ),
        codigo=(
            'df["faixa_tenure"] = pd.cut(df["tenure"], bins=[-1, 12, 24, 48, 72], labels=["0-12 meses", "13-24 meses", "25-48 meses", "49-72 meses"])\n'
            'df["faixa_tenure"] = df["faixa_tenure"].astype(str)'
        ),
        requer_colunas=("tenure",),
        categoria="boa_pratica",
        feedback="Agrupar facilita ver que o churn se concentra nos primeiros meses.",
        pergunta_reflexao="Em qual faixa você imagina que a taxa de cancelamento é maior?",
    ),
    Block(
        id="T13",
        titulo="Normalizar `MonthlyCharges` e `TotalCharges` entre 0 e 1",
        grupo="Variáveis",
        explicacao=(
            "Reescala os valores em dinheiro para ficarem entre 0 (o menor valor) e 1 (o maior valor)."
        ),
        codigo=(
            'for c in ["MonthlyCharges", "TotalCharges"]:\n'
            '    df[c] = (df[c] - df[c].min()) / (df[c].max() - df[c].min())'
        ),
        requer_colunas=("MonthlyCharges", "TotalCharges"),
        requer_blocos=("T01",),
        categoria="depende",
        feedback=(
            "Útil para alguns modelos, mas o painel final perde os valores em dinheiro. "
            "Se o objetivo é um dashboard, prefira manter os valores reais."
        ),
        pergunta_reflexao="O gestor que vai usar o painel entende uma mensalidade de 0,37?",
    ),
)

# ---------------------------------------------------------------------------
# Regras de checklist do tema (seção 8.1). Executadas no marco M4.
# ---------------------------------------------------------------------------


def _sem_vazamento(df_original: pd.DataFrame, df: pd.DataFrame, ids: list[str]) -> tuple[bool, str]:
    if "taxa_churn_pagamento" in df.columns:
        return False, "Coluna derivada do alvo (vazamento): `taxa_churn_pagamento`."
    return True, "Nenhuma coluna calculada a partir do alvo."


def _totalcharges_numerica(df_original: pd.DataFrame, df: pd.DataFrame, ids: list[str]) -> tuple[bool, str]:
    if "TotalCharges" not in df.columns:
        return True, "A coluna `TotalCharges` não está na base."
    if pd.api.types.is_numeric_dtype(df["TotalCharges"]):
        return True, "`TotalCharges` é numérica."
    return False, "`TotalCharges` ainda é texto: não dá para somar nem fazer média."


def _tem_customer_id(df_original: pd.DataFrame, df: pd.DataFrame, ids: list[str]) -> tuple[bool, str]:
    if "customerID" in df.columns:
        return True, "`customerID` presente."
    return False, "A proposta pede lista de clientes; sem ID ela não é possível."


def _tenure_zero_cobrado(df_original: pd.DataFrame, df: pd.DataFrame, ids: list[str]) -> tuple[bool, str]:
    if not {"tenure", "TotalCharges"} <= set(df.columns) or not pd.api.types.is_numeric_dtype(df["TotalCharges"]):
        return True, "Verificação não se aplica a esta base."
    n = int(((df["tenure"] == 0) & (df["TotalCharges"] > 0)).sum())
    if n:
        return False, f"{n} cliente(s) com 0 meses de casa e cobrança acumulada maior que 0."
    return True, "Nenhum cliente novo com cobrança acumulada."


def _ate_50_colunas(df_original: pd.DataFrame, df: pd.DataFrame, ids: list[str]) -> tuple[bool, str]:
    if df.shape[1] > 50:
        return False, f"A base tem {df.shape[1]} colunas (mais de 50)."
    return True, f"A base tem {df.shape[1]} colunas."


REGRAS = (
    Check(
        id="TEL01",
        titulo="Sem coluna derivada do alvo",
        nivel="erro",
        funcao=_sem_vazamento,
        explicacao="Uma coluna calculada a partir do resultado entrega a resposta e engana qualquer análise preditiva.",
    ),
    Check(
        id="TEL02",
        titulo="`TotalCharges` é numérica",
        nivel="erro",
        funcao=_totalcharges_numerica,
        explicacao="Valores em dinheiro guardados como texto não somam, não fazem média e quebram gráficos.",
    ),
    Check(
        id="TEL03",
        titulo="`customerID` mantido",
        nivel="alerta",
        funcao=_tem_customer_id,
        explicacao="A proposta inicial pede uma lista de clientes em risco: é preciso saber quem são.",
    ),
    Check(
        id="TEL04",
        titulo="Clientes novos sem cobrança inventada",
        nivel="alerta",
        funcao=_tenure_zero_cobrado,
        explicacao="Cliente com 0 meses de casa ainda não foi cobrado. Um valor maior que 0 foi inventado.",
    ),
    Check(
        id="TEL05",
        titulo="No máximo 50 colunas",
        nivel="alerta",
        funcao=_ate_50_colunas,
        explicacao="Bases muito largas ficam ilegíveis para o agente de código e para quem lê o painel.",
    ),
)

# ---------------------------------------------------------------------------
# Tema
# ---------------------------------------------------------------------------

DICIONARIO = {
    "customerID": "Código que identifica o cliente",
    "gender": "Gênero do cliente (Male = masculino, Female = feminino)",
    "SeniorCitizen": "Cliente idoso? (1 = sim, 0 = não)",
    "Partner": "Tem cônjuge ou companheiro(a)? (Yes/No)",
    "Dependents": "Tem dependentes? (Yes/No)",
    "tenure": "Tempo de casa: meses como cliente",
    "PhoneService": "Tem serviço de telefone? (Yes/No)",
    "MultipleLines": "Tem mais de uma linha telefônica? (Yes/No/No phone service)",
    "InternetService": "Tipo de internet (DSL, Fiber optic = fibra, No = sem internet)",
    "OnlineSecurity": "Contratou segurança online? (Yes/No/No internet service)",
    "OnlineBackup": "Contratou backup online? (Yes/No/No internet service)",
    "DeviceProtection": "Contratou proteção de aparelho? (Yes/No/No internet service)",
    "TechSupport": "Contratou suporte técnico? (Yes/No/No internet service)",
    "StreamingTV": "Contratou TV por streaming? (Yes/No/No internet service)",
    "StreamingMovies": "Contratou filmes por streaming? (Yes/No/No internet service)",
    "Contract": "Tipo de contrato (Month-to-month = mensal, One year = 1 ano, Two year = 2 anos)",
    "PaperlessBilling": "Recebe fatura só digital? (Yes/No)",
    "PaymentMethod": "Forma de pagamento",
    "MonthlyCharges": "Valor cobrado por mês",
    "TotalCharges": "Valor total já cobrado do cliente",
    "Churn": "Alvo: o cliente cancelou? (Yes = cancelou, No = continua)",
}

SPEC_DEFAULTS = {
    "problema": (
        "A operadora perde cerca de 1 em cada 4 clientes e não sabe quais perfis cancelam mais "
        "nem onde agir primeiro para reter clientes."
    ),
    "usuario": "gestor",
    "funcionalidades": [
        "Ver a taxa de churn geral da base",
        "Ver a taxa de churn por tipo de contrato, forma de pagamento e faixa de tempo de casa",
        "Filtrar todos os gráficos pela barra lateral (contrato, internet, forma de pagamento)",
        "Ver a lista de clientes ativos com perfil de maior risco",
    ],
    "regras_negocio": [
        "Taxa de churn = soma de Churn (0/1) ÷ nº de clientes do filtro",
        "Cliente em risco = contrato mensal E tempo de casa ≤ 12 meses E sem suporte técnico",
        "Valores em moeda exibidos com 2 casas decimais",
    ],
    "criterios_aceitacao": [
        "Sem filtros, o painel mostra a taxa de churn geral calculada do CSV",
        "Ao filtrar por contrato, todos os gráficos se atualizam",
        "A lista de risco mostra customerID, contrato, tenure e MonthlyCharges",
        "O app abre sem erros com `streamlit run app.py`",
    ],
    "metrica_sucesso": "Identificar os 3 segmentos com maior taxa de churn para priorizar ações de retenção.",
}

THEME = Theme(
    id="telco",
    nome="Telecom: quem vai cancelar?",
    dominio="Telecomunicações",
    arquivo="data/telco_churn.csv",
    fonte="https://www.kaggle.com/datasets/blastchar/telco-customer-churn",
    licenca="Base de exemplo da IBM publicada no Kaggle; licença não informada na página (conferir antes de redistribuir).",
    alvo="Churn",
    descricao_base=(
        "Clientes de uma operadora de telecomunicações: dados de cadastro, serviços contratados, "
        "contrato, cobrança e se o cliente cancelou (churn). Uma linha por cliente."
    ),
    dicionario=DICIONARIO,
    problematica=(
        "A operadora perde ~1 em cada 4 clientes e não sabe quais perfis cancelam mais nem onde agir primeiro."
    ),
    proposta_inicial=[
        "Painel com taxa de churn geral e por tipo de contrato, forma de pagamento e faixa de tempo de casa",
        "Filtros na barra lateral",
        "Lista de clientes ativos com perfil de maior risco (regra simples baseada nos segmentos de maior churn)",
    ],
    aprofundamentos=[
        "Simulador \"e se\" de retenção (ex.: migrar X% dos contratos mensais para anuais)",
        "Estimativa de receita mensal em risco",
    ],
    colunas_vazamento=(),
    blocos=BLOCOS,
    regras_checklist=REGRAS,
    spec_defaults=SPEC_DEFAULTS,
    emoji="📱",
)
