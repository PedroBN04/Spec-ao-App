"""Traduções para exibição (meio-termo da proposta P0.3).

As bases continuam com os nomes e valores originais (em inglês), porque o código dos blocos da seção 8
da APP_SPEC depende deles. Estes dicionários só servem para MOSTRAR o equivalente em português no
Raio-X, no explorador e no dicionário da SPEC. Nada aqui altera os dados.
"""

NOMES_TELCO = {
    "customerID": "id_cliente", "gender": "genero", "SeniorCitizen": "idoso", "Partner": "tem_parceiro",
    "Dependents": "tem_dependentes", "tenure": "meses_de_contrato", "PhoneService": "servico_telefone",
    "MultipleLines": "multiplas_linhas", "InternetService": "servico_internet",
    "OnlineSecurity": "seguranca_online", "OnlineBackup": "backup_online", "DeviceProtection": "protecao_aparelho",
    "TechSupport": "suporte_tecnico", "StreamingTV": "tv_streaming", "StreamingMovies": "filmes_streaming",
    "Contract": "tipo_contrato", "PaperlessBilling": "fatura_digital", "PaymentMethod": "forma_pagamento",
    "MonthlyCharges": "mensalidade", "TotalCharges": "total_cobrado", "Churn": "cancelou",
    "faixa_tenure": "faixa_meses_de_contrato", "taxa_churn_pagamento": "taxa_cancelamento_pagamento",
}

VALORES_TELCO = {
    "Yes": "Sim", "No": "Não", "Male": "Masculino", "Female": "Feminino",
    "Month-to-month": "Mensal", "One year": "Anual (1 ano)", "Two year": "Bianual (2 anos)",
    "Fiber optic": "Fibra óptica", "DSL": "DSL (internet pela linha telefônica)",
    "No internet service": "Sem serviço de internet", "No phone service": "Sem serviço de telefone",
    "Electronic check": "Cheque eletrônico", "Mailed check": "Cheque pelo correio",
    "Bank transfer (automatic)": "Transferência bancária (automática)",
    "Credit card (automatic)": "Cartão de crédito (automático)",
}

NOMES_HOTEL = {
    "hotel": "hotel", "is_canceled": "cancelada", "lead_time": "antecedencia_dias",
    "arrival_date_year": "ano_chegada", "arrival_date_month": "mes_chegada",
    "arrival_date_week_number": "semana_chegada", "arrival_date_day_of_month": "dia_chegada",
    "stays_in_weekend_nights": "noites_fim_de_semana", "stays_in_week_nights": "noites_dias_uteis",
    "adults": "adultos", "children": "criancas", "babies": "bebes", "meal": "plano_refeicao",
    "country": "pais", "market_segment": "segmento_mercado", "distribution_channel": "canal_venda",
    "is_repeated_guest": "hospede_recorrente", "previous_cancellations": "cancelamentos_anteriores",
    "previous_bookings_not_canceled": "reservas_anteriores_nao_canceladas",
    "reserved_room_type": "tipo_quarto_reservado", "assigned_room_type": "tipo_quarto_entregue",
    "booking_changes": "alteracoes_reserva", "deposit_type": "tipo_deposito", "agent": "agencia",
    "company": "empresa", "days_in_waiting_list": "dias_lista_espera", "customer_type": "tipo_cliente",
    "adr": "valor_diaria", "required_car_parking_spaces": "vagas_estacionamento",
    "total_of_special_requests": "pedidos_especiais", "reservation_status": "situacao_reserva",
    "reservation_status_date": "data_situacao_reserva", "arrival_date": "data_chegada",
    "total_noites": "total_noites",
}

VALORES_HOTEL = {
    "City Hotel": "Hotel urbano", "Resort Hotel": "Resort",
    "Canceled": "Cancelada", "Check-Out": "Hóspede veio (check-out)", "No-Show": "Não compareceu (no-show)",
    "No Deposit": "Sem depósito", "Non Refund": "Não reembolsável", "Refundable": "Reembolsável",
    "Transient": "Avulso", "Contract": "Contrato", "Group": "Grupo", "Transient-Party": "Avulso ligado a outra reserva",
    "BB": "Café da manhã", "HB": "Meia pensão", "FB": "Pensão completa", "SC": "Sem refeição",
    "Undefined": "Indefinido",
    "Online TA": "Agência de viagem online", "Offline TA/TO": "Agência ou operadora tradicional",
    "TA/TO": "Agência ou operadora de viagem", "Direct": "Direto", "Corporate": "Corporativo",
    "Groups": "Grupos", "Complementary": "Cortesia", "Aviation": "Aviação",
    "GDS": "Sistema global de reservas (GDS)",
    "January": "Janeiro", "February": "Fevereiro", "March": "Março", "April": "Abril", "May": "Maio",
    "June": "Junho", "July": "Julho", "August": "Agosto", "September": "Setembro", "October": "Outubro",
    "November": "Novembro", "December": "Dezembro",
}

NOMES_NOSHOW = {
    "PatientId": "id_paciente", "AppointmentID": "id_consulta", "Gender": "sexo",
    "ScheduledDay": "data_agendamento", "AppointmentDay": "data_consulta", "Age": "idade",
    "Neighbourhood": "bairro", "Scholarship": "bolsa_familia", "Hipertension": "hipertensao",
    "Diabetes": "diabetes", "Alcoholism": "alcoolismo", "Handcap": "deficiencias",
    "SMS_received": "recebeu_sms", "No-show": "faltou (Yes = faltou)",
}

VALORES_NOSHOW = {"Yes": "Sim", "No": "Não", "F": "Feminino", "M": "Masculino"}

# Significado de colunas DEPOIS de conversões conhecidas do catálogo: {id_bloco: {coluna: significado}}
SIGNIFICADO_APOS_TELCO = {
    "T01": {"TotalCharges": "Valor total já cobrado do cliente (número; vazio onde antes havia só espaços)"},
    "T05": {"SeniorCitizen": "Cliente idoso? (Yes = sim, No = não)"},
    "T06": {c: f"{t} (Yes/No)" for c, t in {
        "MultipleLines": "Tem mais de uma linha telefônica?", "OnlineSecurity": "Contratou segurança online?",
        "OnlineBackup": "Contratou backup online?", "DeviceProtection": "Contratou proteção de aparelho?",
        "TechSupport": "Contratou suporte técnico?", "StreamingTV": "Contratou TV por streaming?",
        "StreamingMovies": "Contratou filmes por streaming?"}.items()},
    "T07": {"Churn": "Alvo: o cliente cancelou? (1 = cancelou, 0 = continua)"},
    "T13": {"MonthlyCharges": "Valor cobrado por mês, reescalado entre 0 (menor) e 1 (maior)",
            "TotalCharges": "Valor total já cobrado, reescalado entre 0 (menor) e 1 (maior)"},
}
SIGNIFICADO_APOS_HOTEL = {
    "H01": {"children": "Número de crianças (vazios preenchidos com 0)"},
    "H02": {"country": "País de origem do hóspede (código de 3 letras; \"Desconhecido\" quando não informado)"},
    "H03": {"agent": "Código da agência de viagem que fez a reserva (\"Sem agente\" = reserva sem agência)"},
    "H13": {"meal": "Plano de refeição (BB = café da manhã, HB = meia pensão, FB = pensão completa, SC = sem refeição)"},
}
SIGNIFICADO_APOS_NOSHOW = {
    "N03": {"ScheduledDay": "Data e hora em que a consulta foi agendada (data/hora)",
            "AppointmentDay": "Data da consulta (data/hora; o horário vem sempre 00:00)"},
    "N10": {"PatientId": "Código do paciente, como texto (um paciente pode ter várias consultas)"},
}
