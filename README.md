# Da Spec ao App

Laboratório guiado de dados e especificação, feito para o minicurso + hackathon de 24/11/2026.

O participante escolhe um desafio com uma base de dados real, faz um diagnóstico visual, trata os dados
clicando em blocos (boas práticas e **armadilhas** misturadas de propósito), passa por um checklist de
qualidade e responde a um assistente que monta uma `SPEC.md`. No fim, baixa dois arquivos —
`dados_tratados.csv` e `SPEC.md` — que entrega a um agente de código (Claude Code) para construir a
solução do hackathon.

> **Importante para quem for mexer no código:** os blocos de categoria "armadilha" e "depende" são errados
> ou discutíveis **de propósito**. O código de cada bloco é cópia literal da seção 8 da `APP_SPEC.md` e um
> teste garante isso. Não corrija esses blocos.

## Como rodar no seu computador

Requisitos: Python 3.11 ou mais novo.

```bash
git clone https://github.com/PedroBN04/Spec-ao-App.git
cd Spec-ao-App
python -m venv .venv
```

Ative o ambiente virtual:

- Windows: `.venv\Scripts\activate`
- Mac/Linux: `source .venv/bin/activate`

Instale e rode:

```bash
pip install -r requirements.txt
streamlit run app.py
```

O navegador abre em http://localhost:8501. As três bases já estão em `data/`; não é preciso baixar nada.

### Testes

```bash
pytest -q
```

Os testes conferem, entre outras coisas: que o código de cada bloco é idêntico ao da `APP_SPEC.md`, que
cada bloco roda na base real, os efeitos da seção 14 da spec, o desfazer, o checklist, a SPEC gerada e
jornadas completas na interface (com o `AppTest` do Streamlit).

### Regerar as bases (só para a organização)

As bases em `data/` são geradas a partir dos CSVs originais do Kaggle:

1. Baixe as três bases (links abaixo) e coloque os CSVs em `data/raw/` (pasta ignorada pelo git):
   `WA_Fn-UseC_-Telco-Customer-Churn.csv`, `hotel_bookings.csv` e `KaggleV2-May-2016.csv`.
2. Rode `python scripts/preparar_dados.py`.

O script copia a base telco inteira, tira amostras de 30.000 linhas (seed 42) das outras duas e confere
que os "defeitos" usados nos blocos continuam presentes. Se algum sumir, ele falha com uma mensagem clara.

## Estrutura

```
app.py                  ponto de entrada (roteia as 7 etapas)
core/                   lógica sem interface: temas e blocos, diagnóstico, executor, checklist,
                        assistente da SPEC e exportação
ui/                     componentes e uma tela por etapa
scripts/preparar_dados.py
data/                   bases usadas pelo app
tests/                  pytest
APP_SPEC.md             especificação completa
DECISOES.md             decisões tomadas onde a spec não dizia nada
```

## Publicar no Streamlit Community Cloud

1. Entre em https://share.streamlit.io com a conta do GitHub que tem acesso a este repositório.
2. Clique em **Create app** → **Deploy a public app from GitHub** (ou "Yup, I have an app").
3. Preencha: repositório `PedroBN04/Spec-ao-App`, branch (a que tiver a versão final, ex.: `main`),
   arquivo principal `app.py`.
4. Em **Advanced settings**, escolha **Python 3.12**. Não há segredos (*secrets*) para configurar.
5. Clique em **Deploy**. A primeira instalação leva alguns minutos. O endereço fica no formato
   `https://<nome-escolhido>.streamlit.app`.

Plano B no dia: `streamlit run app.py` num computador local, com os participantes na mesma rede
acessando `http://<ip-do-computador>:8501`.

## Créditos e licenças das bases

| Desafio | Base | Fonte | Licença (como aparece no Kaggle) |
| --- | --- | --- | --- |
| Telecom: quem vai cancelar? | Telco Customer Churn — publicada por BlastChar (base de exemplo da IBM) | https://www.kaggle.com/datasets/blastchar/telco-customer-churn | **"Data files © Original Authors"**: sem licença aberta; os direitos ficam com os autores originais |
| Turismo: por que as reservas são canceladas? | Hotel Booking Demand — publicada por Jesse Mostipak; dados de Antonio, Almeida e Nunes, *Hotel booking demand datasets*, Data in Brief 22 (2019) | https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand | **CC BY 4.0** (Attribution 4.0 International): uso livre, inclusive comercial, com atribuição — https://creativecommons.org/licenses/by/4.0/ |
| Saúde pública: quem falta às consultas? | Medical Appointment No Shows (Vitória-ES, 2016) — publicada por JoniHoppen | https://www.kaggle.com/datasets/joniarroba/noshowappointments | **CC BY-NC-SA 4.0**: uso não comercial, com atribuição e compartilhamento pela mesma licença — https://creativecommons.org/licenses/by-nc-sa/4.0/ |

Licenças conferidas nas páginas do Kaggle em 23/11/2026.

**Atenção — base telco:** a página não oferece licença aberta ("© Original Authors"). O uso aqui é
educacional, com atribuição à fonte; antes de redistribuir a base fora do minicurso (ou em um projeto
comercial), consulte os autores originais.

**Atenção — base no-show:** a licença CC BY-NC-SA 4.0 exige uso **não comercial**, atribuição e que
derivados (como `data/noshow_consultas.csv` e os CSVs exportados pelas equipes) sejam compartilhados sob a
mesma licença.

As bases do repositório são amostras (hotel e no-show) ou cópia integral (telco) dos arquivos originais,
sem nenhuma limpeza, usadas para fins educacionais.
