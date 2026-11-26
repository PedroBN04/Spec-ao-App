# Da Spec ao App

Laboratório guiado de dados e especificação, feito para o minicurso + hackathon de 26/11/2026.

> **Projeto educacional, sem fins comerciais.** As bases de dados em `data/` são usadas apenas para fins
> educativos, com atribuição às fontes (ver [Créditos e licenças das bases](#créditos-e-licenças-das-bases)).

O participante atua como analista de dados: aceita uma **missão** (uma solicitação de uma área cliente),
investiga a base num **diagnóstico** guiado, monta uma **pipeline** de tratamento em blocos, no estilo de um
fluxo do n8n (com blocos prontos e blocos configuráveis), **revisa** o resultado e escreve a **SPEC** por conta
própria, com perguntas-guia. No fim, baixa um kit `.zip` com `dados_tratados.csv`, uma planilha
`dados_tratados_excel.xlsx` (abre direto no Excel) e `SPEC.md`, e envia o kit para a organização pelo WhatsApp. A organização entrega o kit a um agente de IA
(sempre com o mesmo pedido) para construir o painel do hackathon. O progresso pode ser salvo e
retomado com um rascunho `.json`, pela barra lateral. Depois da exportação, uma etapa de **revisão
com o facilitador** mostra o gabarito: quais blocos eram boas práticas, armadilhas ou "depende".

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

O script copia a base telco inteira, tira amostras de 30.000 linhas (seed 42) das outras duas (no hotel,
as 6 linhas com defeitos raros — `children` vazio, `adr` negativa ou acima de 1.000 — entram sempre; ver
`DECISOES.md`, item 1) e confere
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
