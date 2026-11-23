"""Tema noshow — Saúde pública: quem falta às consultas? (seção 8.3 da APP_SPEC).

Marco M1: metadados, dicionário e proposta. Os blocos, as regras de checklist e os
spec_defaults entram no marco M6.
"""

from core.models import Theme

DICIONARIO = {
    "PatientId": "Código do paciente (um paciente pode ter várias consultas)",
    "AppointmentID": "Código da consulta (único por linha)",
    "Gender": "Sexo do paciente (F = feminino, M = masculino)",
    "ScheduledDay": "Data e hora em que a consulta foi agendada",
    "AppointmentDay": "Data da consulta (sem horário: vem sempre como 00:00)",
    "Age": "Idade do paciente em anos (0 = bebê com menos de 1 ano)",
    "Neighbourhood": "Bairro onde fica a unidade de saúde",
    "Scholarship": "Paciente recebe Bolsa Família? (1 = sim, 0 = não)",
    "Hipertension": "Tem hipertensão? (1 = sim, 0 = não) — nome da coluna com erro de grafia no original",
    "Diabetes": "Tem diabetes? (1 = sim, 0 = não)",
    "Alcoholism": "Tem alcoolismo? (1 = sim, 0 = não)",
    "Handcap": "Número de deficiências do paciente (0 a 4) — nome com erro de grafia no original",
    "SMS_received": "Recebeu SMS de lembrete? (1 = sim, 0 = não)",
    "No-show": "Alvo: o paciente FALTOU? (Yes = faltou, No = compareceu) — atenção à leitura invertida",
}

THEME = Theme(
    id="noshow",
    nome="Saúde pública: quem falta às consultas?",
    dominio="Saúde pública",
    arquivo="data/noshow_consultas.csv",
    fonte="https://www.kaggle.com/datasets/joniarroba/noshowappointments",
    licenca="CC BY-NC-SA 4.0 (uso não comercial, com atribuição — conferir na página do Kaggle).",
    alvo="No-show",
    descricao_base=(
        "Consultas agendadas em unidades de saúde de Vitória-ES em 2016. "
        "Amostra de 30.000 das 110.527 consultas originais. Uma linha por consulta."
    ),
    dicionario=DICIONARIO,
    problematica=(
        "Cerca de 1 em cada 5 consultas agendadas no SUS tem falta, desperdiçando horários "
        "que poderiam atender outros pacientes."
    ),
    proposta_inicial=[
        "Painel com taxa de falta por tempo de espera (faixas), dia da semana, faixa etária, "
        "recebimento de SMS e bairro (top 10)",
        "Filtros",
        "Lista de consultas futuras com perfil de maior risco para priorizar lembretes",
    ],
    aprofundamentos=[
        "Comparar o efeito do SMS por faixa de espera",
        "Mapa/ranking de bairros",
    ],
    colunas_vazamento=(),
    blocos=(),
    regras_checklist=(),
    spec_defaults={},
    emoji="🏥",
)
