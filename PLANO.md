# Plano — app "Da Spec ao App" (curadoria, arquitetura pedagógica e roadmap)

Evento: 24/11/2026, 19h às 22h30, UFU Bloco 1F sala 256, até 25 participantes.
Documento de apoio à equipe organizadora. A especificação para o Claude Code está em `APP_SPEC.md`.

---

## 1. Curadoria de datasets

As três bases têm o mesmo **tipo** de problema (um evento sim/não a explicar: cancelar, cancelar reserva, faltar). Isso permite usar a mesma régua de avaliação no hackathon e o mesmo formato de app final, mas em **domínios diferentes**, cada um com uma armadilha "assinatura" diferente.

| | Telecom — Churn | Turismo — Cancelamento de reservas | Saúde pública — Faltas em consultas |
| --- | --- | --- | --- |
| Base | [Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) | [Hotel Booking Demand](https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand) | [Medical Appointment No Shows](https://www.kaggle.com/datasets/joniarroba/noshowappointments) |
| Tamanho original | 7.043 × 21 (~1 MB) | 119.390 × 32 (~16 MB) | 110.527 × 14 (~10 MB) |
| No repositório | completa | amostra de 30 mil linhas | amostra de 30 mil linhas |
| Alvo | `Churn` (~26% Yes) | `is_canceled` (~37%) | `No-show` (~20% Yes = **faltou**) |
| Problemática | 1 em cada 4 clientes cancela; quais perfis e onde agir primeiro? | ~37% das reservas são canceladas; quais reservas têm mais risco? | 1 em cada 5 consultas do SUS tem falta; quem priorizar nos lembretes? |
| Proposta inicial | Painel de churn por contrato, pagamento e tempo de casa + lista de clientes em risco | Painel de cancelamento por hotel, mês, antecedência, depósito e canal + ranking de segmentos | Painel de faltas por espera, dia da semana, idade, SMS e bairro + lista de consultas de risco |
| Armadilha "assinatura" | Média para preencher cliente novo; outlier que não é erro; one-hot do ID | `dropna()` que apaga 90%; **vazamento** com `reservation_status` | Alvo de nome enganoso (`No-show=Yes`); data sem horário gera espera negativa; deduplicar paciente apaga consultas |

### Blocos certos × errados (resumo; detalhes e código na seção 8 da APP_SPEC)

**Telecom**
- ✅ Converter `TotalCharges` para número · preencher com 0 quando `tenure = 0` · padronizar `SeniorCitizen` · unificar "No internet service" em "No" · criar faixa de tempo de casa.
- ⚠️ Preencher `TotalCharges` com a média (cliente novo com 2.280 de cobrança) · taxa de churn por forma de pagamento como coluna (**vazamento**) · remover "outliers" de mensalidade (clientes reais) · one-hot em tudo (milhares de colunas por causa do ID).
- 🤔 Remover `customerID` (bom para modelo, ruim para a lista de risco) · normalizar valores (bom para modelo, ruim para painel).

**Turismo**
- ✅ `children` nulo → 0 · `agent` nulo → "Sem agente" (o vazio significa reserva direta) · remover a coluna `company` (94% vazia) · montar `arrival_date` · remover `reservation_status` · remover reservas sem hóspedes e diárias negativas.
- ⚠️ `dropna()` geral (perde > 90%) · one-hot de `reservation_status` (**vazamento**) · remover diárias 0 (cortesias são reais).
- 🤔 Remover duplicados (não há ID de reserva: podem ser reservas de grupo).

**Saúde**
- ✅ Criar `faltou` = `No-show == "Yes"` · converter datas · espera comparando só as datas · remover idade −1 · `PatientId` como texto · dia da semana e faixa etária.
- ⚠️ Criar `compareceu` com a leitura invertida · espera por subtração direta (1/3 da base fica negativa) · remover idade 0 (bebês) · deduplicar por paciente (cada linha é uma consulta).
- 🤔 Transformar `Handcap` (0 a 4) em sim/não.

Antes de subir no GitHub, confiram no Kaggle a licença de cada base e citem as fontes no README. A base de saúde costuma estar sob licença não comercial (uso educacional ok, com atribuição).

---

## 2. Arquitetura pedagógica

Fluxo proposto: **0 Boas-vindas → 1 Desafio → 2 Diagnóstico → 3 Tratamento → 4 Checklist → 5 Spec → 6 Exportar**.

Sessões acrescentadas às duas originais, e por quê:

| Sessão | Ganho didático |
| --- | --- |
| **Diagnóstico (EDA visual)** separado do tratamento | Cria o hábito "olhar antes de mexer". As armadilhas só funcionam como aprendizado se a pessoa teve chance de ver o problema antes (ex.: `company` 94% vazia explica o desastre do `dropna()`). |
| **Checklist de qualidade** antes da spec | Fecha o ciclo de feedback: mostra as consequências acumuladas (vazamento, linhas perdidas, nulos) e obriga a **corrigir ou justificar**. As justificativas entram na SPEC e viram material de avaliação ("coerência técnica das decisões"). |
| **Boas-vindas** curta | Define o nome da equipe e avisa que há armadilhas de propósito, o que muda a postura de "clicar em tudo" para "decidir". |

Duas decisões de design que sustentam o aprendizado:
- **Categoria escondida até aplicar**: o participante decide pela explicação e pelo diagnóstico; o selo (✅ ⚠️ 🤔) e o feedback aparecem depois, junto com o impacto real.
- **Código exibido = código executado**: cada bloco mostra o trecho pandas exato que roda. Quem quiser aprender o código vê; quem não quiser, entende pelo antes × depois.

Não recomendo acrescentar uma etapa de modelagem (treinar modelo): não cabe no tempo, desvia do foco (dados + especificação) e o público é iniciante.

---

## 3. Stack

**Streamlit + pandas + plotly**, deploy no **Streamlit Community Cloud** a partir do repositório.
- Executa pandas real no servidor (gera o CSV de verdade).
- É a mesma stack do app final do hackathon, então o participante já vê o tipo de aplicação que vai pedir ao Claude Code.
- Deploy gratuito, sem instalação nas máquinas do laboratório: só o link.
- Plano B: `git clone` + `pip install -r requirements.txt` + `streamlit run app.py` local (as máquinas já têm Python).

Risco principal do deploy gratuito: ~1 GB de memória para todas as sessões. Por isso as bases grandes viram amostras de 30 mil linhas e cada sessão guarda só o DataFrame atual. Testem com 5 a 10 abas abertas ao mesmo tempo antes do evento.

---

## 4. Roadmap até o evento

| Quando | O que | Saída |
| --- | --- | --- |
| Hoje 23/11, manhã | Criar repo; baixar as 3 bases em `data/raw/`; salvar `APP_SPEC.md` e `CLAUDE.md`; pedir ao Claude Code os marcos M1 e M2 | App navegando + diagnóstico do tema telco |
| Hoje, tarde | M3 e M4 (tratamento em blocos + checklist) | Fluxo telco completo até o checklist |
| Hoje, noite | M5 (spec + exportação) e teste de ponta a ponta com o telco | **Versão mínima utilizável** (1 tema) |
| 24/11, manhã | M6 (hotel e noshow) e M7 (textos + deploy) | 3 temas no ar |
| 24/11, até 16h | Ensaio em máquina Windows: 2 pessoas fazem a jornada inteira; levar os 2 arquivos ao Claude Code e verificar se ele constrói o app | Ajustes finais e **congelamento** do código |
| 24/11, 18h30 | Abrir o link no laboratório e testar 5 máquinas | Pronto |

Se o tempo apertar: entregar **só o tema telco** completo (é a base da proposta aprovada) e deixar hotel e noshow como aprofundamento.

---

## 5. Riscos e pontos de atenção

1. **Acesso ao Claude Code pelos participantes**: o Claude Code exige conta paga ou chave de API. Definam hoje como as equipes vão usá-lo: uma conta por equipe nas máquinas da organização, os organizadores rodando para cada equipe, ou um agente alternativo (ex.: GitHub Copilot, gratuito para estudantes). A `SPEC.md` gerada funciona com qualquer agente.
2. **Tempo do hackathon**: com o app, a jornada leva ~45–60 min. Somando a construção com o agente e o pitch, revisem o cronograma das 3h30.
3. **Mudança em relação à proposta aprovada**: o plano de aula previa os participantes escrevendo a spec no VS Code. Agora a spec é guiada pelo app. Vale avisar o professor da mudança, que é coerente com os objetivos (SDD, tratamento de dados, verificação).
4. **Kaggle exige login** para baixar: baixem hoje e subam no repositório para ninguém depender disso no dia.
