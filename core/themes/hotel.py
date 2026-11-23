"""Tema hotel — Turismo: por que as reservas são canceladas? (seção 8.2 da APP_SPEC).

Marco M1: metadados, dicionário e proposta. Os blocos, as regras de checklist e os
spec_defaults entram no marco M6.
"""

from core.models import Theme

DICIONARIO = {
    "hotel": "Tipo de hotel (Resort Hotel = resort, City Hotel = hotel urbano)",
    "is_canceled": "Alvo: a reserva foi cancelada? (1 = sim, 0 = não)",
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
    "adr": "Diária média (average daily rate), em euros",
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
        "Dados do artigo de Antonio, Almeida e Nunes (Data in Brief, 2019), publicado em acesso aberto "
        "(CC BY 4.0 — conferir na página do Kaggle)."
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
    blocos=(),
    regras_checklist=(),
    spec_defaults={},
    emoji="🏨",
)
