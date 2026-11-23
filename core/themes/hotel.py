"""Tema hotel — Turismo: por que as reservas são canceladas? (seção 8.2 da APP_SPEC).

ATENÇÃO: o campo `codigo` de cada bloco é cópia literal da seção 8 da APP_SPEC.
Blocos de armadilha e "depende" são errados ou discutíveis DE PROPÓSITO (o app é didático).
Não corrija, melhore nem "otimize" esses trechos. tests/test_blocks.py confere o texto.
"""

import pandas as pd

from core.models import Block, Check, Theme

BLOCOS = (
    Block(
        id='H01',
        titulo='Preencher `children` vazio com 0',
        grupo='Valores ausentes',
        explicacao='Preenche com 0 os campos vazios de `children` (número de crianças) e transforma a coluna em número inteiro.',
        codigo='df["children"] = df["children"].fillna(0).astype(int)',
        requer_colunas=('children',),
        categoria='boa_pratica',
        feedback='Poucos casos; 0 crianças é a leitura mais provável e a coluna volta a ser inteira.',
        pergunta_reflexao='Quantas reservas tinham `children` vazio? Isso muda alguma taxa?',
    ),
    Block(
        id='H02',
        titulo='Preencher `country` vazio com "Desconhecido"',
        grupo='Valores ausentes',
        explicacao='Preenche os países vazios de `country` com o texto "Desconhecido".',
        codigo='df["country"] = df["country"].fillna("Desconhecido")',
        requer_colunas=('country',),
        categoria='boa_pratica',
        feedback='Mantém as linhas e deixa explícito que o país não foi informado.',
        pergunta_reflexao='Um país "Desconhecido" deveria aparecer no ranking de países do painel?',
    ),
    Block(
        id='H03',
        titulo='Tratar `agent` vazio como "Sem agente"',
        grupo='Valores ausentes',
        explicacao='Troca os vazios de `agent` (agência que fez a reserva) por "Sem agente" e guarda os códigos de agência como texto.',
        codigo='df["agent"] = df["agent"].fillna(0).astype(int).astype(str).replace("0", "Sem agente")',
        requer_colunas=('agent',),
        categoria='boa_pratica',
        feedback='Aqui o vazio tem significado: reserva feita sem agência. Apagar ou preencher com média destruiria essa informação.',
        pergunta_reflexao='Reservas sem agência cancelam mais ou menos que as feitas por agência?',
    ),
    Block(
        id='H04',
        titulo='Remover a coluna `company`',
        grupo='Estrutura',
        explicacao='Apaga a coluna `company` (empresa que fez ou pagou a reserva) da base inteira.',
        codigo='df = df.drop(columns=["company"])',
        requer_colunas=('company',),
        categoria='boa_pratica',
        feedback='~94% vazia. Remover a coluna preserva todas as linhas.',
        pergunta_reflexao='Que pergunta de negócio você perderia sem a coluna `company`?',
    ),
    Block(
        id='H05',
        titulo='Remover linhas com qualquer valor vazio',
        grupo='Valores ausentes',
        explicacao='Apaga da base toda reserva que tenha pelo menos um campo vazio, em qualquer coluna.',
        codigo='df = df.dropna()',
        categoria='armadilha',
        feedback='Como `company` está vazia em quase todas as reservas, este comando apagou mais de 90% da base. Sempre olhe de onde vêm os nulos antes de um `dropna()`.',
        pergunta_reflexao='Antes de apagar linhas com vazios, você olhou QUAIS colunas têm vazios?',
        sugestao='H04',
    ),
    Block(
        id='H06',
        titulo='Criar a data de chegada `arrival_date`',
        grupo='Datas',
        explicacao='Junta ano, mês (escrito em inglês) e dia de chegada em uma única coluna de data, `arrival_date`.',
        codigo='meses = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6, "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}\ndf["arrival_date"] = pd.to_datetime(dict(year=df["arrival_date_year"], month=df["arrival_date_month"].map(meses), day=df["arrival_date_day_of_month"]))',
        requer_colunas=('arrival_date_year', 'arrival_date_month', 'arrival_date_day_of_month'),
        categoria='boa_pratica',
        feedback='A data estava espalhada em 3 colunas (e o mês em texto em inglês). Agora dá para fazer séries no tempo e ordenar corretamente.',
        pergunta_reflexao='Agora dá para ordenar as chegadas no tempo. Que gráfico isso permite fazer?',
    ),
    Block(
        id='H07',
        titulo='Criar colunas 0/1 a partir de `reservation_status` para enriquecer a análise',
        grupo='Variáveis',
        explicacao='Cria uma coluna 0/1 para cada valor de `reservation_status` (situação final da reserva) e remove a coluna original.',
        codigo='df = pd.get_dummies(df, columns=["reservation_status"], prefix="status")',
        requer_colunas=('reservation_status',),
        categoria='armadilha',
        feedback='Vazamento: `reservation_status` diz se a reserva foi cancelada — é o próprio resultado. `status_Canceled` é praticamente igual a `is_canceled`.',
        pergunta_reflexao='Você saberia a situação final de uma reserva no momento em que ela é feita?',
        sugestao='H08',
    ),
    Block(
        id='H08',
        titulo='Remover `reservation_status` e `reservation_status_date`',
        grupo='Estrutura',
        explicacao='Apaga as colunas `reservation_status` e `reservation_status_date`, que registram a situação final da reserva.',
        codigo='df = df.drop(columns=["reservation_status", "reservation_status_date"])',
        requer_colunas=('reservation_status', 'reservation_status_date'),
        categoria='boa_pratica',
        feedback='Essas colunas só são conhecidas depois do desfecho da reserva. Removê-las evita que o app final "preveja" com informação do futuro.',
        pergunta_reflexao='Que outras colunas só são conhecidas depois que a reserva termina?',
    ),
    Block(
        id='H09',
        titulo='Remover reservas sem nenhum hóspede',
        grupo='Linhas inválidas',
        explicacao='Apaga as reservas em que adultos + crianças + bebês somam 0.',
        codigo='df = df[(df["adults"] + df["children"].fillna(0) + df["babies"]) > 0]',
        requer_colunas=('adults', 'children', 'babies'),
        categoria='boa_pratica',
        feedback='Reservas com 0 adultos, 0 crianças e 0 bebês são registros inválidos.',
        pergunta_reflexao='Como uma reserva sem nenhum hóspede pode ter entrado no sistema?',
    ),
    Block(
        id='H10',
        titulo='Remover diárias (`adr`) negativas ou acima de 1.000',
        grupo='Outliers',
        explicacao='Apaga as reservas com diária média (`adr`) negativa ou acima de 1.000.',
        codigo='df = df[(df["adr"] >= 0) & (df["adr"] <= 1000)]',
        requer_colunas=('adr',),
        categoria='boa_pratica',
        feedback='Diária negativa é erro de registro e a original tem uma diária de 5.400, muito acima das demais. Poucas linhas, grande efeito nas médias.',
        pergunta_reflexao='Quantas linhas saíram? Compare com o efeito na diária média.',
    ),
    Block(
        id='H11',
        titulo='Remover reservas com diária (`adr`) igual a 0',
        grupo='Outliers',
        explicacao='Apaga as reservas com diária média (`adr`) igual a 0.',
        codigo='df = df[df["adr"] != 0]',
        requer_colunas=('adr',),
        categoria='armadilha',
        feedback='Diária 0 é legítima (cortesias, pacotes, funcionários). Você removeu reservas reais e distorceu a taxa de cancelamento.',
        pergunta_reflexao='Quem pode se hospedar com diária 0? Essas reservas são erros?',
        sugestao='H10',
    ),
    Block(
        id='H12',
        titulo='Remover linhas duplicadas',
        grupo='Duplicados',
        explicacao='Apaga as linhas que são exatamente iguais a outra linha, em todas as colunas.',
        codigo='df = df.drop_duplicates()',
        categoria='depende',
        feedback='A base não tem ID de reserva: linhas iguais podem ser reservas diferentes de um mesmo grupo. Remover reduz bastante a base; manter pode inflar contagens. Justifique sua escolha.',
        pergunta_reflexao='Sem um código de reserva, como saber se duas linhas iguais são a mesma reserva?',
    ),
    Block(
        id='H13',
        titulo='Padronizar `meal` "Undefined" como "SC" (sem refeição)',
        grupo='Variáveis',
        explicacao='Troca o plano de refeição "Undefined" por "SC" na coluna `meal`.',
        codigo='df["meal"] = df["meal"].replace("Undefined", "SC")',
        requer_colunas=('meal',),
        categoria='boa_pratica',
        feedback='Segundo a documentação da base, "Undefined" e "SC" significam o mesmo: sem refeição.',
        pergunta_reflexao='Onde você confirmaria que dois códigos significam a mesma coisa?',
    ),
    Block(
        id='H14',
        titulo='Criar total de noites (`total_noites`)',
        grupo='Variáveis',
        explicacao='Cria `total_noites`, somando as noites de fim de semana e de dias úteis.',
        codigo='df["total_noites"] = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]',
        requer_colunas=('stays_in_weekend_nights', 'stays_in_week_nights'),
        categoria='boa_pratica',
        feedback='Base para calcular receita da reserva (`adr` × noites).',
        pergunta_reflexao='Com `total_noites` e `adr`, como calcular a receita de uma reserva?',
    ),
)

# ---------------------------------------------------------------------------
# Regras de checklist do tema (seção 8.2)
# ---------------------------------------------------------------------------


def _sem_status(df_original: pd.DataFrame, df: pd.DataFrame, ids: list[str]) -> tuple[bool, str]:
    achadas = [c for c in df.columns if c in ("reservation_status", "reservation_status_date") or str(c).startswith("status_")]
    if achadas:
        return False, "Colunas que só existem depois do desfecho da reserva: " + ", ".join(f"`{c}`" for c in achadas) + "."
    return True, "Nenhuma coluna com a situação final da reserva."


def _metade_das_linhas(df_original: pd.DataFrame, df: pd.DataFrame, ids: list[str]) -> tuple[bool, str]:
    pct = len(df) / len(df_original) if len(df_original) else 1.0
    texto = f"{pct:.1%}".replace(".", ",")
    if pct < 0.5:
        return False, f"Só {texto} das reservas originais continuam na base."
    return True, f"{texto} das reservas originais continuam na base."


def _adr_negativa(df_original: pd.DataFrame, df: pd.DataFrame, ids: list[str]) -> tuple[bool, str]:
    if "adr" not in df.columns:
        return True, "A coluna `adr` não está na base."
    n = int((df["adr"] < 0).sum())
    if n:
        return False, f"{n} reserva(s) com diária (`adr`) negativa."
    return True, "Nenhuma diária negativa."


def _tem_arrival_date(df_original: pd.DataFrame, df: pd.DataFrame, ids: list[str]) -> tuple[bool, str]:
    if "arrival_date" in df.columns:
        return True, "`arrival_date` presente."
    return False, "Sem `arrival_date`, o painel não consegue ordenar as chegadas no tempo."


def _children_sem_nulos(df_original: pd.DataFrame, df: pd.DataFrame, ids: list[str]) -> tuple[bool, str]:
    if "children" not in df.columns:
        return True, "A coluna `children` não está na base."
    n = int(df["children"].isna().sum())
    if n:
        return False, f"{n} reserva(s) com `children` vazio."
    return True, "`children` sem vazios."


REGRAS = (
    Check("HOT01", "Sem a situação final da reserva", "erro", _sem_status,
          "`reservation_status` e colunas derivadas revelam se a reserva foi cancelada: é o próprio resultado."),
    Check("HOT02", "Pelo menos metade das reservas mantidas", "erro", _metade_das_linhas,
          "Perder mais da metade da base muda completamente as taxas de cancelamento."),
    Check("HOT03", "Nenhuma diária negativa", "alerta", _adr_negativa,
          "Diária negativa é erro de registro e distorce médias de receita."),
    Check("HOT04", "Data de chegada criada", "alerta", _tem_arrival_date,
          "Uma coluna de data permite séries no tempo e ordenar os meses corretamente."),
    Check("HOT05", "`children` sem vazios", "alerta", _children_sem_nulos,
          "Vazios em `children` quebram somas de hóspedes e filtros."),
)

SPEC_DEFAULTS = {
    "problema": (
        "Dois hotéis em Portugal perdem receita com cancelamentos (~37% das reservas) e não sabem "
        "quais reservas têm mais risco de serem canceladas."
    ),
    "usuario": "gestor",
    "funcionalidades": [
        "Ver a taxa de cancelamento geral da base",
        "Ver a taxa de cancelamento por hotel e por mês de chegada",
        "Ver a taxa de cancelamento por faixa de antecedência da reserva (`lead_time`)",
        "Ver a taxa de cancelamento por tipo de depósito (`deposit_type`) e canal de venda (`distribution_channel`)",
        "Filtrar todos os gráficos por hotel e por ano de chegada",
        "Ver o ranking dos segmentos (até 10) com maior taxa de cancelamento",
    ],
    "regras_negocio": [
        "Taxa de cancelamento = soma de `is_canceled` (0/1) ÷ nº de reservas do filtro",
        "Faixas de antecedência (`lead_time`): 0-7, 8-30, 31-90, 91-180 e mais de 180 dias",
        "Segmento = hotel + tipo de depósito + canal de venda; o ranking só considera segmentos com pelo menos 100 reservas",
        "Meses sempre em ordem do calendário (janeiro a dezembro), nunca em ordem alfabética",
        "Taxas exibidas em porcentagem com 1 casa decimal (ex.: 37,1%)",
        "Ranking ordenado da maior para a menor taxa de cancelamento",
    ],
    "criterios_aceitacao": [
        "Sem filtros, o painel mostra a taxa de cancelamento geral calculada do CSV",
        "Ao filtrar por hotel, todos os gráficos e o ranking se atualizam",
        "O gráfico por mês mostra os meses de janeiro a dezembro, nessa ordem",
        "O ranking mostra no máximo 10 segmentos, com a taxa e o nº de reservas de cada um",
        "O app abre sem erros com `streamlit run app.py`",
    ],
    "metrica_sucesso": "Apontar os 3 segmentos com maior taxa de cancelamento para revisar a política de depósito.",
}

DICIONARIO = {
    "hotel": "Tipo de hotel (Resort Hotel = resort, City Hotel = hotel urbano)",
    "is_canceled": "Alvo: a reserva foi cancelada? (1 = cancelada ou hóspede não compareceu, 0 = hóspede veio)",
    "lead_time": "Antecedência: dias entre a reserva e a data de chegada",
    "arrival_date_year": "Ano de chegada",
    "arrival_date_month": "Mês de chegada (nome em inglês)",
    "arrival_date_week_number": "Semana do ano da chegada",
    "arrival_date_day_of_month": "Dia do mês da chegada",
    "stays_in_weekend_nights": "Noites de fim de semana (sábado e domingo) reservadas",
    "stays_in_week_nights": "Noites de dias de semana (segunda a sexta) reservadas",
    "adults": "Número de adultos",
    "children": "Número de crianças",
    "babies": "Número de bebês",
    "meal": "Plano de refeição (BB = café da manhã, HB = meia pensão, FB = pensão completa, SC/Undefined = sem refeição)",
    "country": "País de origem do hóspede (código de 3 letras)",
    "market_segment": "Segmento de mercado (ex.: Online TA = agência online, Groups = grupos)",
    "distribution_channel": "Canal de venda da reserva",
    "is_repeated_guest": "Hóspede que já se hospedou antes? (1 = sim, 0 = não)",
    "previous_cancellations": "Reservas anteriores canceladas por este hóspede",
    "previous_bookings_not_canceled": "Reservas anteriores NÃO canceladas por este hóspede",
    "reserved_room_type": "Tipo de quarto reservado (código)",
    "assigned_room_type": "Tipo de quarto entregue (código)",
    "booking_changes": "Número de alterações feitas na reserva",
    "deposit_type": "Tipo de depósito (No Deposit = sem depósito, Non Refund = não reembolsável, Refundable = reembolsável)",
    "agent": "Código da agência de viagem que fez a reserva (vazio = sem agência)",
    "company": "Código da empresa que fez/pagou a reserva (vazio = não foi empresa)",
    "days_in_waiting_list": "Dias na lista de espera até a confirmação",
    "customer_type": "Tipo de cliente (Transient = avulso, Contract = contrato, Group = grupo, Transient-Party = avulso ligado a outra reserva)",
    "adr": "Diária média (average daily rate); a base não informa a moeda",
    "required_car_parking_spaces": "Vagas de estacionamento pedidas",
    "total_of_special_requests": "Número de pedidos especiais (ex.: andar alto, cama de casal)",
    "reservation_status": "Situação final da reserva (Canceled, Check-Out, No-Show) — só conhecida depois do desfecho",
    "reservation_status_date": "Data da última atualização da situação da reserva — só conhecida depois do desfecho",
}

THEME = Theme(
    id="hotel",
    nome="Turismo: por que as reservas são canceladas?",
    dominio="Turismo e hotelaria",
    arquivo="data/hotel_bookings.csv",
    fonte="https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand",
    licenca=(
        "CC BY 4.0 (Attribution 4.0 International). Dados de Antonio, Almeida e Nunes, "
        "Hotel booking demand datasets, Data in Brief 22 (2019)."
    ),
    alvo="is_canceled",
    descricao_base=(
        "Reservas de dois hotéis em Portugal (um resort e um hotel urbano) com chegada entre 2015 e 2017. "
        "Amostra de 30.000 das 119.390 reservas originais. Uma linha por reserva."
    ),
    dicionario=DICIONARIO,
    problematica=(
        "Dois hotéis em Portugal perdem receita com cancelamentos (~37% das reservas) "
        "e não sabem quais reservas têm mais risco."
    ),
    proposta_inicial=[
        "Painel com taxa de cancelamento por hotel, mês de chegada, antecedência da reserva "
        "(faixas de `lead_time`), tipo de depósito e canal de venda",
        "Filtros",
        "Ranking dos segmentos de maior risco",
    ],
    aprofundamentos=[
        "Estimativa de receita perdida (`adr` × noites das reservas canceladas)",
        "Calendário de ocupação por mês",
    ],
    colunas_vazamento=("reservation_status", "reservation_status_date"),
    blocos=BLOCOS,
    regras_checklist=REGRAS,
    spec_defaults=SPEC_DEFAULTS,
    emoji="🏨",
    alvos_aceitos=(),
    vazamento_derivado=("status_",),
    dicionario_extra={
        "arrival_date": "Data de chegada (ano, mês e dia juntos), criada pelo bloco H06",
        "total_noites": "Total de noites da reserva (fim de semana + dias úteis)",
    },
    observacoes=(
        ("is_canceled", "`is_canceled` = 1 significa reserva cancelada OU hóspede que não apareceu (no-show); 0 significa que o hóspede veio (check-out)."),
        ("adr", "`adr` = 0 é válido: cortesias, pacotes e reservas de funcionários."),
        ("agent", "`agent` vazio ou \"Sem agente\" = reserva feita sem agência (não é erro)."),
        ("company", "`company` vazia = a reserva não foi feita por empresa (não é erro)."),
        ("arrival_date_month", "`arrival_date_month` tem o nome do mês em inglês: ordene pelo calendário, não pelo texto."),
    ),
)
