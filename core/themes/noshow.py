"""Tema noshow — Saúde pública: quem falta às consultas? (seção 8.3 da APP_SPEC).

ATENÇÃO: o campo `codigo` de cada bloco é cópia literal da seção 8 da APP_SPEC.
Blocos de armadilha e "depende" são errados ou discutíveis DE PROPÓSITO (o app é didático).
Não corrija, melhore nem "otimize" esses trechos. tests/test_blocks.py confere o texto.
"""

import pandas as pd

from core.models import Block, Check, Theme

BLOCOS = (
    Block(
        id='N01',
        titulo='Criar coluna `faltou` (1 = faltou)',
        grupo='Alvo',
        explicacao='Cria a coluna `faltou` com 1 quando `No-show` é "Yes" e 0 nos demais casos.',
        codigo='df["faltou"] = (df["No-show"] == "Yes").astype(int)',
        requer_colunas=('No-show',),
        categoria='boa_pratica',
        feedback='Na base, "No-show = Yes" significa que o paciente **não** compareceu. Agora a média de `faltou` é a taxa de faltas (~20%).',
        pergunta_reflexao='Qual é a média de `faltou`? Ela bate com a taxa de faltas do diagnóstico?',
    ),
    Block(
        id='N02',
        titulo='Criar coluna `compareceu` a partir de `No-show`',
        grupo='Alvo',
        explicacao='Cria a coluna `compareceu` com 1 quando `No-show` é "Yes" e 0 nos demais casos.',
        codigo='df["compareceu"] = (df["No-show"] == "Yes").astype(int)',
        requer_colunas=('No-show',),
        categoria='armadilha',
        feedback='Leitura invertida: o nome sugere presença, mas o valor 1 marca quem faltou. Pela sua coluna, só ~20% compareceram — o contrário da realidade. Sempre confira o dicionário de dados.',
        pergunta_reflexao='Releia o dicionário: o que "No-show = Yes" quer dizer?',
        sugestao='N01',
    ),
    Block(
        id='N03',
        titulo='Converter `ScheduledDay` e `AppointmentDay` para data/hora',
        grupo='Datas',
        explicacao='Converte `ScheduledDay` (dia do agendamento) e `AppointmentDay` (dia da consulta) de texto para data/hora.',
        codigo='df["ScheduledDay"] = pd.to_datetime(df["ScheduledDay"])\ndf["AppointmentDay"] = pd.to_datetime(df["AppointmentDay"])',
        requer_colunas=('ScheduledDay', 'AppointmentDay'),
        categoria='boa_pratica',
        feedback='Eram texto. Agora dá para calcular intervalos e extrair dia da semana.',
        pergunta_reflexao='Que cálculos com datas ficam possíveis agora?',
    ),
    Block(
        id='N04',
        titulo='Calcular dias de espera (comparando só as datas)',
        grupo='Variáveis',
        explicacao='Cria `dias_espera`: quantos dias entre o agendamento e a consulta, comparando só as datas (sem as horas).',
        codigo='df["dias_espera"] = (df["AppointmentDay"].dt.normalize() - df["ScheduledDay"].dt.normalize()).dt.days',
        requer_colunas=('ScheduledDay',),
        requer_blocos=('N03',),
        categoria='boa_pratica',
        feedback='`AppointmentDay` não tem horário (vem como 00:00). Comparar só as datas faz consultas no mesmo dia valerem 0.',
        pergunta_reflexao='Quantas consultas foram marcadas para o mesmo dia (espera 0)?',
    ),
    Block(
        id='N05',
        titulo='Calcular dias de espera (subtração direta)',
        grupo='Variáveis',
        explicacao='Cria `dias_espera` subtraindo diretamente a data/hora do agendamento da data da consulta.',
        codigo='df["dias_espera"] = (df["AppointmentDay"] - df["ScheduledDay"]).dt.days',
        requer_colunas=('ScheduledDay',),
        requer_blocos=('N03',),
        categoria='armadilha',
        feedback='Como a consulta vem sem horário, quem agendou e foi atendido no mesmo dia ficou com −1 dia de espera. Um terço da base virou "espera negativa".',
        pergunta_reflexao='Olhe os menores valores de `dias_espera`. Faz sentido esperar −1 dia?',
        sugestao='N04',
    ),
    Block(
        id='N06',
        titulo='Remover consultas com espera negativa',
        grupo='Linhas inválidas',
        explicacao='Apaga as consultas com `dias_espera` menor que 0.',
        codigo='df = df[df["dias_espera"] >= 0]',
        requer_colunas=('dias_espera',),
        categoria='boa_pratica',
        feedback='Com N04, remove só os poucos registros inconsistentes (consulta antes do agendamento). Se você usou N05, este bloco apaga um terço da base — olhe a métrica de linhas removidas.',
        pergunta_reflexao='Quantas linhas saíram? Isso confirma ou contradiz o cálculo de espera que você escolheu?',
    ),
    Block(
        id='N07',
        titulo='Remover idade negativa',
        grupo='Linhas inválidas',
        explicacao='Apaga as consultas de pacientes com idade (`Age`) negativa.',
        codigo='df = df[df["Age"] >= 0]',
        requer_colunas=('Age',),
        categoria='boa_pratica',
        feedback='Existe idade −1 na base: erro de cadastro.',
        pergunta_reflexao='Quantos pacientes tinham idade negativa?',
    ),
    Block(
        id='N08',
        titulo='Remover pacientes com idade 0',
        grupo='Linhas inválidas',
        explicacao='Apaga as consultas de pacientes com idade (`Age`) igual a 0.',
        codigo='df = df[df["Age"] > 0]',
        requer_colunas=('Age',),
        categoria='armadilha',
        feedback='Idade 0 são bebês com menos de 1 ano — pacientes reais de pediatria. Você removeu um grupo inteiro da análise.',
        pergunta_reflexao='Quem tem idade 0 numa base de saúde?',
        sugestao='N07',
    ),
    Block(
        id='N09',
        titulo='Remover pacientes repetidos (`PatientId`)',
        grupo='Duplicados',
        explicacao='Mantém só a primeira consulta de cada paciente (`PatientId`) e apaga as demais.',
        codigo='df = df.drop_duplicates(subset="PatientId")',
        requer_colunas=('PatientId',),
        categoria='armadilha',
        feedback='Cada linha é uma **consulta**, não um paciente. Pacientes com várias consultas são normais (e importantes para entender faltas recorrentes). Você apagou grande parte da base.',
        pergunta_reflexao='Cada linha da base é um paciente ou uma consulta?',
    ),
    Block(
        id='N10',
        titulo='Converter `PatientId` para texto',
        grupo='Tipos',
        explicacao='Converte o código do paciente (`PatientId`) de número decimal para texto.',
        codigo='df["PatientId"] = df["PatientId"].astype("int64").astype(str)',
        requer_colunas=('PatientId',),
        categoria='boa_pratica',
        feedback='O ID estava como número decimal (aparece em notação científica em planilhas). ID não é para fazer conta.',
        pergunta_reflexao='Faz sentido somar ou tirar a média de um código de paciente?',
    ),
    Block(
        id='N11',
        titulo='Criar dia da semana da consulta',
        grupo='Variáveis',
        explicacao='Cria `dia_semana` com o nome do dia da semana da consulta (Segunda a Domingo).',
        codigo='dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]\ndf["dia_semana"] = df["AppointmentDay"].dt.dayofweek.map(dict(enumerate(dias)))',
        requer_colunas=('AppointmentDay',),
        requer_blocos=('N03',),
        categoria='boa_pratica',
        feedback='Permite analisar se a falta varia ao longo da semana.',
        pergunta_reflexao='Em que dia da semana você acha que mais pacientes faltam?',
    ),
    Block(
        id='N12',
        titulo='Criar faixa etária',
        grupo='Variáveis',
        explicacao='Cria `faixa_etaria`, agrupando as idades em faixas: 0-12, 13-18, 19-30, 31-45, 46-60 e 61+.',
        codigo='df["faixa_etaria"] = pd.cut(df["Age"], bins=[-1, 12, 18, 30, 45, 60, 200], labels=["0-12", "13-18", "19-30", "31-45", "46-60", "61+"]).astype(str)',
        requer_colunas=('Age',),
        categoria='boa_pratica',
        feedback='Faixas tornam o painel mais legível que 100 idades diferentes.',
        pergunta_reflexao='Qual faixa etária falta mais? E qual falta menos?',
    ),
    Block(
        id='N13',
        titulo='Transformar `Handcap` em sim/não (`tem_deficiencia`)',
        grupo='Variáveis',
        explicacao='Cria `tem_deficiencia` (1 se `Handcap` for maior que 0) e apaga a coluna `Handcap`.',
        codigo='df["tem_deficiencia"] = (df["Handcap"] > 0).astype(int)\ndf = df.drop(columns=["Handcap"])',
        requer_colunas=('Handcap',),
        categoria='depende',
        feedback='`Handcap` vai de 0 a 4 (nº de deficiências), não é 0/1 como as outras. Binarizar simplifica, mas perde a quantidade.',
        pergunta_reflexao='Para o seu painel, importa saber QUANTAS deficiências o paciente tem?',
    ),
    Block(
        id='N14',
        titulo='Renomear colunas para português e corrigir grafia',
        grupo='Estrutura',
        explicacao='Renomeia as colunas para português e corrige a grafia (ex.: `Hipertension` → `hipertensao`, `No-show` → `no_show_original`).',
        codigo='df = df.rename(columns={"PatientId": "id_paciente", "AppointmentID": "id_consulta", "Gender": "sexo", "ScheduledDay": "data_agendamento", "AppointmentDay": "data_consulta", "Age": "idade", "Neighbourhood": "bairro", "Scholarship": "bolsa_familia", "Hipertension": "hipertensao", "Diabetes": "diabetes", "Alcoholism": "alcoolismo", "Handcap": "deficiencias", "SMS_received": "recebeu_sms", "No-show": "no_show_original"})',
        requer_colunas=('Hipertension',),
        categoria='boa_pratica',
        feedback='Nomes claros ajudam o agente de código e quem lê o painel. Repare que os blocos que dependem dos nomes antigos ficaram desabilitados: a ordem das operações importa.',
        pergunta_reflexao='Depois de renomear, quais blocos do catálogo ficaram bloqueados? Por quê?',
    ),
)

# ---------------------------------------------------------------------------
# Regras de checklist do tema (seção 8.3)
# ---------------------------------------------------------------------------


def _sem_compareceu(df_original: pd.DataFrame, df: pd.DataFrame, ids: list[str]) -> tuple[bool, str]:
    if "compareceu" in df.columns:
        return False, "A coluna `compareceu` está invertida: o valor 1 marca quem FALTOU."
    return True, "Nenhuma coluna com leitura invertida do alvo."


def _espera_negativa(df_original: pd.DataFrame, df: pd.DataFrame, ids: list[str]) -> tuple[bool, str]:
    if "dias_espera" not in df.columns:
        return True, "A coluna `dias_espera` não está na base."
    n = int((df["dias_espera"] < 0).sum())
    if n:
        return False, f"{n} consulta(s) com espera negativa."
    return True, "Nenhuma espera negativa."


def _setenta_por_cento(df_original: pd.DataFrame, df: pd.DataFrame, ids: list[str]) -> tuple[bool, str]:
    pct = len(df) / len(df_original) if len(df_original) else 1.0
    texto = f"{pct:.1%}".replace(".", ",")
    if pct < 0.7:
        return False, f"Só {texto} das consultas originais continuam na base."
    return True, f"{texto} das consultas originais continuam na base."


def _tem_faltou(df_original: pd.DataFrame, df: pd.DataFrame, ids: list[str]) -> tuple[bool, str]:
    if "faltou" in df.columns:
        return True, "`faltou` presente."
    return False, "Sem a coluna `faltou` (1 = faltou), o app final precisa reinterpretar o `No-show` invertido."


def _idade_negativa(df_original: pd.DataFrame, df: pd.DataFrame, ids: list[str]) -> tuple[bool, str]:
    coluna = "Age" if "Age" in df.columns else ("idade" if "idade" in df.columns else None)
    if coluna is None:
        return True, "A coluna de idade não está na base."
    n = int((df[coluna] < 0).sum())
    if n:
        return False, f"{n} paciente(s) com `{coluna}` negativa."
    return True, "Nenhuma idade negativa."


REGRAS = (
    Check("NOS01", "Sem coluna de alvo invertida", "erro", _sem_compareceu,
          "Uma coluna com nome contrário ao valor faz o app final mostrar o oposto da realidade."),
    Check("NOS02", "Nenhuma espera negativa", "erro", _espera_negativa,
          "Ninguém é atendido antes de agendar: espera negativa é erro de cálculo ou de registro."),
    Check("NOS03", "Pelo menos 70% das consultas mantidas", "erro", _setenta_por_cento,
          "Perder muitas consultas apaga justamente os padrões de falta que o painel precisa mostrar."),
    Check("NOS04", "Alvo `faltou` criado", "alerta", _tem_faltou,
          "Com `faltou` (1 = faltou), a média da coluna já é a taxa de falta."),
    Check("NOS05", "Nenhuma idade negativa", "alerta", _idade_negativa,
          "Idade negativa é erro de cadastro e distorce as faixas etárias."),
)

SPEC_DEFAULTS = {
    "problema": (
        "Cerca de 1 em cada 5 consultas agendadas no SUS tem falta, desperdiçando horários que poderiam "
        "atender outros pacientes. A gestão não sabe quais consultas priorizar para lembretes."
    ),
    "usuario": "gestor",
    "funcionalidades": [
        "Ver a taxa de falta geral da base",
        "Ver a taxa de falta por faixa de tempo de espera (`dias_espera`)",
        "Ver a taxa de falta por dia da semana e por faixa etária",
        "Comparar a taxa de falta de quem recebeu e de quem não recebeu SMS",
        "Ver a taxa de falta dos 10 bairros com mais consultas",
        "Filtrar todos os gráficos por bairro e por faixa etária",
        "Ver a lista de consultas com perfil de maior risco de falta",
    ],
    "regras_negocio": [
        "Taxa de falta = soma de `faltou` (1 = faltou) ÷ nº de consultas do filtro",
        "Na coluna original `No-show`, \"Yes\" significa que o paciente FALTOU",
        "Faixas de espera (`dias_espera`): 0 (mesmo dia), 1-7, 8-30 e mais de 30 dias",
        "Consulta de maior risco = espera de 15 dias ou mais E paciente não recebeu SMS",
        "A base é de 2016: \"consultas futuras\" = todas as consultas da base, tratadas como a agenda a priorizar",
        "Taxas exibidas em porcentagem com 1 casa decimal (ex.: 19,9%)",
    ],
    "criterios_aceitacao": [
        "Sem filtros, o painel mostra a taxa de falta geral calculada do CSV (perto de 20%)",
        "Os dias da semana aparecem em ordem (Segunda a Sábado), não em ordem alfabética",
        "O gráfico de bairros mostra no máximo 10 bairros",
        "Ao filtrar por bairro, todos os gráficos e a lista de risco se atualizam",
        "A lista de risco mostra paciente, bairro, data da consulta e dias de espera, da maior para a menor espera",
        "O app abre sem erros com `streamlit run app.py`",
    ],
    "metrica_sucesso": "Identificar os grupos com maior taxa de falta para priorizar lembretes e reduzir horários desperdiçados.",
}

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
    blocos=BLOCOS,
    regras_checklist=REGRAS,
    spec_defaults=SPEC_DEFAULTS,
    emoji="🏥",
    alvos_aceitos=("faltou", "no_show_original"),
    vazamento_derivado=(),
    dicionario_extra={
        "faltou": "Alvo tratado: o paciente faltou? (1 = faltou, 0 = compareceu)",
        "compareceu": "ATENÇÃO: apesar do nome, 1 = o paciente FALTOU (coluna com leitura invertida)",
        "dias_espera": "Dias entre o agendamento e a consulta",
        "dia_semana": "Dia da semana da consulta (Segunda a Domingo)",
        "faixa_etaria": "Faixa etária do paciente (0-12, 13-18, 19-30, 31-45, 46-60, 61+)",
        "tem_deficiencia": "Paciente tem alguma deficiência? (1 = sim, 0 = não)",
        "id_paciente": DICIONARIO["PatientId"],
        "id_consulta": DICIONARIO["AppointmentID"],
        "sexo": DICIONARIO["Gender"],
        "data_agendamento": DICIONARIO["ScheduledDay"],
        "data_consulta": DICIONARIO["AppointmentDay"],
        "idade": DICIONARIO["Age"],
        "bairro": DICIONARIO["Neighbourhood"],
        "bolsa_familia": DICIONARIO["Scholarship"],
        "hipertensao": "Tem hipertensão? (1 = sim, 0 = não)",
        "diabetes": DICIONARIO["Diabetes"],
        "alcoolismo": DICIONARIO["Alcoholism"],
        "deficiencias": "Número de deficiências do paciente (0 a 4)",
        "recebeu_sms": DICIONARIO["SMS_received"],
        "no_show_original": DICIONARIO["No-show"],
    },
    observacoes=(
        ("No-show", "`No-show` = \"Yes\" significa que o paciente FALTOU (leitura invertida)."),
        ("no_show_original", "`no_show_original` = \"Yes\" significa que o paciente FALTOU (leitura invertida)."),
        ("faltou", "`faltou` = 1 significa que o paciente faltou; a média da coluna é a taxa de falta."),
        ("compareceu", "`compareceu` está INVERTIDA: 1 = faltou. Não use sem corrigir a leitura."),
        ("Age", "`Age` = 0 são bebês com menos de 1 ano: é válido."),
        ("idade", "`idade` = 0 são bebês com menos de 1 ano: é válido."),
        ("AppointmentDay", "`AppointmentDay` não tem horário (vem 00:00): compare só as datas."),
        ("data_consulta", "`data_consulta` não tem horário (vem 00:00): compare só as datas."),
        ("PatientId", "Um paciente pode ter várias consultas: cada linha é uma CONSULTA."),
        ("id_paciente", "Um paciente pode ter várias consultas: cada linha é uma CONSULTA."),
    ),
)
