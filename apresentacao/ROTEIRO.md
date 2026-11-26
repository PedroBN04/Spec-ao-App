# Roteiro da apresentação — Da Spec ao App

Janela da apresentação: **19h10 às 20h30** (80 min). Conteúdo planejado: **~70 min**, com folga para
perguntas e para as equipes se organizarem antes do hackathon (20h30).

Arquivo para apresentar: **`da_spec_ao_app.html`** (arquivo único; funciona sem internet e sem a pasta
`assets/`). Plano B: `da_spec_ao_app_abertura.pdf`.

---

## 1. Comandos durante a apresentação

| Tecla | O que faz |
| --- | --- |
| **→**, **espaço**, **Enter** ou **Page Down** | Avança. Se um texto ainda está sendo “digitado” na tela, o 1º toque só completa a animação; o 2º avança. |
| **←**, **Page Up** ou **Backspace** | Volta um slide |
| **F** | Tela cheia (liga/desliga) |
| **S** | Abre a janela de **notas do apresentador**: texto de apoio, tempo sugerido, cronômetro, relógio e qual é o próximo slide. As setas também funcionam nessa janela. |
| **Ctrl+P** | “Ir para slide”: digite parte do nome (ex.: `analy`, `tdd`, `whatsapp`), escolha com ↑/↓ e **Enter**. **Esc** fecha. |
| **E** | Esconde/mostra o explorador de arquivos (mais espaço para o slide) |
| **Home** / **End** | Primeiro / último slide |
| Clique no explorador | Clicar numa pasta vai para o 1º slide da seção; clicar num arquivo abre aquele slide |
| `#número` no endereço | Abre direto num slide (ex.: `da_spec_ao_app.html#25` abre o caso Analy) |

**Dicas de projeção**

- Use **Chrome ou Edge**. Configure o projetor como **tela estendida** (não duplicada): o slide em tela
  cheia no projetor (**F**) e a janela de notas (**S**) no notebook.
- Se a janela de notas não abrir, o navegador bloqueou pop-up: permita pop-ups para o arquivo e aperte **S**
  de novo.
- **Ctrl+P** está reservado para “ir para slide”. Para imprimir/gerar PDF, use o menu do navegador
  (⋮ → Imprimir) — ou use o PDF pronto.
- Os slides se ajustam a qualquer resolução (testado em 1920×1080 e 1366×768).

---

## 2. Roteiro fala a fala

Legenda: **Mensagem** = a ideia que o público precisa levar; **Fale** = sugestão de fala (não precisa ler);
**Ponte** = frase para passar ao slide seguinte. Os horários são de referência.

### A. Abertura — 19h10 às 19h15

**1 · Capa** (1 min)
- **Mensagem:** boas-vindas; todos abrem o site agora.
- **Fale:** “Boa noite! Este é o *Da Spec ao App*, minicurso + hackathon da ACE de Inteligência de Negócios.”
  Apresente o Prof. José Eduardo e a organização. “Apontem a câmera para o QR Code e deixem o site aberto:
  vamos usar daqui a pouco.”
- **Atenção:** dê 30–60 s para o QR Code. Pergunte se todos conseguiram abrir.

**2 · Agenda** (1 min)
- **Mensagem:** a noite tem duas partes — apresentação até 20h30, depois mão na massa, com envio do kit até 21h30.
- **Fale:** percorra os horários e leia o quadro “Você sai daqui sabendo”.
- **Ponte:** “Para chegar lá, vamos seguir um mapa.”

**3 · Mapa da apresentação** (1,5 min)
- **Mensagem:** a lógica da noite: história → métodos → IA → SDD → dados → caso real → hackathon.
- **Fale:** “Vamos começar em 1991, passar por como se fazia software antes da IA, ver o que muda com a IA,
  um caso real aqui da região e, no fim, as regras do hackathon. O explorador à esquerda mostra onde estamos.”
- **Ponte:** “E a história começa com um estudante e um computador comum.”

### B. Da garagem à IA — 19h15 às 19h22

**4 · Linux, 1991** (2 min)
- **Mensagem:** uma pessoa, um PC comum e muito conhecimento técnico.
- **Fale:** “Agosto de 1991. Um estudante finlandês de 21 anos, Linus Torvalds, escreve num fórum: estou
  fazendo um sistema operacional, *só um hobby, nada grande e profissional*.” Deixe a mensagem terminar de
  ser digitada e leia a tradução. “Ele tinha um PC 386 comprado naquele ano. Nada de supercomputador.”
- **Pergunta ao público (opcional):** “Alguém aqui sabe o que esse ‘hobby’ virou?”

**5 · “Só um hobby”…** (1,5 min)
- **Mensagem:** o hobby virou infraestrutura do mundo.
- **Fale:** “Todos os 500 supercomputadores mais rápidos rodam Linux desde 2017. O Android é construído
  sobre ele. E o Linus ainda criou o Git, que é o que este ‘editor’ está imitando.”
- **Ponte:** “A ferramenta era modesta. O diferencial era o conhecimento. Hoje temos uma ferramenta nova.”

**6 · A IA é a nova alavanca** (2 min)
- **Mensagem:** a IA facilita construir muita coisa — **desde que haja conhecimento técnico adequado**.
- **Fale:** compare as duas linhas (1991 × 2026). “A IA acelera código, telas e consultas. Mas entender o
  problema, escolher os dados, definir as regras e conferir continua sendo nosso trabalho. Sem base técnica,
  a IA acelera também os erros.”
- **Ponte:** “E essa preocupação com método não é nova. Vamos ver como se fazia software antes da IA.”

### C. Como se fazia software — 19h22 às 19h33

**7 · Linha do tempo dos métodos** (1,5 min)
- **Mensagem:** cada método resolveu um problema do anterior.
- **Fale:** percorra 1970 → 2025 sem se aprofundar. Destaque os dois de 2025: vibe coding (vermelho) e SDD
  (verde). “Vamos ver rapidinho os principais.”

**8 · Cascata** (1,5 min)
- **Mensagem:** erro de entendimento descoberto só no fim custa caro.
- **Fale:** “Requisitos, projeto, código, testes — um depois do outro. O problema: se o pedido foi mal
  entendido, a gente só descobre no fim.” Curiosidade: o próprio Royce, em 1970, já dizia que isso “é
  arriscado e convida ao fracasso”.

**9 · Manifesto Ágil** (1,5 min)
- **Mensagem:** ciclos curtos; mudança é normal.
- **Fale:** leia os quatro valores. “Cuidado com o mito: ágil não é ‘sem documentação’. O texto diz que os
  itens da direita têm valor; só valorizamos mais os da esquerda.”

**10 · TDD** (2 min)
- **Mensagem:** definir o “pronto” **antes** de construir.
- **Fale:** “Primeiro um teste que falha — vermelho. Depois o mínimo de código para passar — verde. Depois
  melhora sem quebrar — refatorar.” Aponte o código. “O site que vocês vão usar tem 272 testes automáticos.”

**11 · BDD** (1,5 min)
- **Mensagem:** escrever o comportamento em linguagem de negócio — exatamente o que é um critério de aceitação.
- **Fale:** leia o cenário Dado/Quando/Então. “Qualquer pessoa da área cliente lê isso e diz se está certo.
  Na SPEC de vocês, isso vira o critério de aceitação. Só que agora quem também lê é o agente de IA.”

**12 · O que o SDD herda** (1,5 min)
- **Mensagem:** o SDD junta o melhor dos métodos anteriores; a novidade é que o leitor é um agente.
- **Fale:** percorra a tabela linha a linha. Termine na linha “Novo”: “nada pode ficar implícito”.
- **Ponte:** “E por que isso ficou urgente agora? Porque a IA chegou de vez.”

### D. A IA chegou — 19h33 às 19h39

**13 · O mercado pede agilidade** (1,5 min)
- **Mensagem:** a fila de pedidos de dados cresce mais rápido do que a capacidade de entrega.
- **Pergunta ao público:** “Quem aqui já precisou de um relatório ‘para ontem’?”
- **Fale:** “Como entregar mais rápido sem entregar errado? Essa é a pergunta da noite.”

**14 · A IA chegou ao desenvolvimento** (1,5 min)
- **Mensagem:** usar IA virou rotina; confiar exige poder conferir.
- **Fale:** “Pesquisa da Stack Overflow de 2026: dois em cada três desenvolvedores usam assistentes de código.
  Mas só 6,6% confiam na IA para decisões importantes. Quase metade confia quando consegue verificar.”
- **Pergunta ao público (opcional):** “Levantem a mão: quem já usou IA para escrever código ou fórmula?”

**15 · Vibe coding** (2 min)
- **Mensagem:** pedido vago + aceitar sem olhar = erro com cara de certo.
- **Fale:** leia o pedido vago. Depois os 4 problemas: taxa invertida, coluna inventada, filtro inventado,
  regra que ninguém pediu. “Nenhum aparece na tela bonita. É a IA sem o conhecimento técnico do slide do Linux.”
- **Ponte:** “O antídoto tem nome: Spec-Driven Development.”

### E. Spec-Driven Development — 19h39 às 19h47

**16 · O que é SDD** (1,5 min)
- **Mensagem:** a especificação é a fonte da verdade; o código é consequência.
- **Fale:** percorra o ciclo: especificar → planejar → gerar → verificar. “Mudou o pedido? Muda a spec e gera
  de novo.”

**17 · Anatomia de uma boa spec** (1,5 min)
- **Mensagem:** 7 seções — é exatamente o que vocês vão escrever hoje.
- **Fale:** leia as seções rapidamente. “Escrevam para um estranho: o agente só sabe o que estiver no
  arquivo. E digam o que fica de fora.”

**18 · Cada seção fecha uma porta** (1,5 min)
- **Mensagem:** spec clara = menos invenção (alucinação).
- **Fale:** “Escopo impede funcionalidade extra; dados impedem coluna inventada; regras impedem fórmula
  inventada; critérios permitem conferir.” Mostre a fórmula da taxa de churn.

**19 · Critério de aceitação** (1 min)
- **Mensagem:** critério bom se responde com sim ou não.
- **Fale:** leia um par vermelho/verde. “É o ‘Então’ do BDD.”

**20 · SDD no mercado** (1,5 min)
- **Mensagem:** não é teoria — GitHub, AWS e os agentes já trabalham assim.
- **Fale:** cite Spec Kit, Kiro, AGENTS.md/CLAUDE.md e regras do Cursor. “Curiosidade: o site de vocês foi
  construído assim, a partir de uma especificação.”
- **Ponte:** “E na área de dados? Vamos ver como a exploração de dados mudou.”

### F. Dados: antes e hoje — 19h47 às 19h55

**21 · Linha do tempo dos dados** (2 min)
- **Mensagem:** a cada geração, quem pergunta ficou mais perto do dado.
- **Fale:** VisiCalc (1979), Excel (1985), BI corporativo nos anos 90, Power BI (2015), Streamlit (2019 —
  “é o que roda o site de vocês”), agentes de dados (hoje).

**22 · Antes × hoje** (2 min)
- **Mensagem:** muito mudou, mas dado ruim continua gerando painel errado.
- **Fale:** percorra a tabela. Termine no quadro amarelo: “O que não mudou: lixo entra, lixo sai, e a regra
  de negócio precisa estar clara.”

**23 · Dados tratados + spec clara** (1,5 min)
- **Mensagem:** é o caminho do hackathon: base bruta → tratamento → CSV + SPEC → agente → painel.
- **Fale:** “Guardem esse fluxo: é exatamente o que vocês vão fazer daqui a pouco.”

**24 · Qualidade de dados** (1,5 min)
- **Mensagem:** o agente confia no CSV; armadilhas de tratamento viram erros no painel.
- **Fale:** explique as 3 armadilhas (média nos vazios, vazamento, apagar “outliers”). “Vocês vão encontrar
  armadilhas assim no site — e o site não avisa qual é qual.”
- **Ponte:** “Agora, um caso real, aqui da região. Pedro, com você.”

### G. Caso real: Analy — 19h55 às 20h05 (Pedro)

**25 · Caso Analy** (2,5 min)
- **Mensagem:** agente de dados da Algar, no Teams, com vários agentes treinados nos dados da empresa.
- **Fale:** o que é a Analy, onde ela fica (Teams), quem usa (vendas, marketing, sucesso do cliente) e para
  quê (churn, desempenho comercial, visão 360°). Deixe claro que a pergunta da tela é ilustrativa.

**26 · O que mudou na prática** (2 min)
- **Mensagem:** ganhos reais — e o que levava meses hoje leva semanas.
- **Fale:** “Segundo a Algar: +20% de produtividade em menos de seis meses de operação, um processo de até
  dois dias feito em cerca de 40 segundos, e 127 agentes de IA ativos.” Depois o relato próprio: “Agentes
  especialistas e data apps que levariam meses hoje ficam prontos em semanas.”
- **Atenção:** os números são divulgados pela própria empresa; fale “segundo a Algar”.

**27 · O principal aprendizado** (2 min)
- **Mensagem:** técnico + negócio = potencial infinito.
- **Fale:** “O aprendizado não foi sobre ferramenta. Foi a importância da regra de negócio e da boa
  comunicação com a área que pede. A IA não adivinha a regra. Quando juntamos conhecimento técnico com
  conhecimento de negócio, o potencial é infinito — e é isso que a SPEC de vocês faz.”

**28 · “Negar a IA é negar a ciência.”** (30 s)
- **Atenção:** a tela fica limpa (modo zen). Pause 3–4 segundos em silêncio antes de falar.
- **Fale:** “Mas IA com método: especificar, verificar e assumir a responsabilidade.”

**29 · Boas práticas e riscos** (1 min)
- **Mensagem:** revisar, proteger dados, seguir a governança, humano no controle.
- **Ponte:** “Chega de teoria. Agora é com vocês.”

### H. O hackathon — 20h05 às 20h20

**30 · Agora é com vocês** (1 min)
- **Mensagem:** equipes prontas, missão, entrega do kit pelo WhatsApp até 21h30.
- **Fale:** “Cada equipe recebe uma missão de uma área cliente. No fim, vocês mandam o kit pelo WhatsApp para
  o organizador, e a organização roda o agente de IA.”

**31 · Três papéis** (1 min)
- **Mensagem:** vocês são a ponte entre negócio e técnico.

**32 a 37 · A jornada no site** (≈7 min no total)
- **Dica:** se der, mostre o site ao vivo ao lado dos slides. Um slide por etapa:
  - **0–1 Início e missão:** nome da equipe → Começar → aceitar a missão.
  - **2 Diagnóstico:** investigar antes de mexer; anotar (exemplo: `TotalCharges` com 11 células só com espaços).
  - **3 Pipeline:** blocos prontos e personalizados; **há armadilhas de propósito**; escrevam o porquê de cada passo.
  - **4 Revisão:** antes × depois; não gostou, volta ao fluxo.
  - **5 SPEC:** 8 passos com perguntas-guia; exemplo e esqueleto com lacunas para quem travar.
  - **6 Exportar:** baixar o `.zip` e **enviar pelo WhatsApp, como documento, com o nome da equipe**.
    **Prazo: 21h30.** Lembrar do “Salvar ou retomar progresso”.

**38 · Do kit ao painel** (1,5 min)
- **Mensagem:** o prompt é o mesmo para todas as equipes — quem decide o resultado é a SPEC.
- **Fale:** percorra o fluxo equipe → WhatsApp → organização → agente → painel.

**39 · Como vamos avaliar** (1 min)
- **Mensagem:** 4 critérios, 25% cada: resultado vs. missão, tratamento, clareza da SPEC, pitch.

**40 · Regras e dicas** (1 min)
- **Mensagem:** desenvolvimento das 20h30 às 21h30; kit pelo WhatsApp **até 21h30**; pitches a partir de 21h40; pitch de até 3 min (problema → dados → decisões →
  demonstração → impacto).
- **Fale:** diga em voz alta **para qual número** enviar o kit (ver pendências).

**41 · Bora construir?** (30 s)
- **Fale:** “Abram o site pelo QR Code, juntem-se às equipes e bora construir!” Deixe este slide projetado
  durante o hackathon (tem o QR Code).

### Perguntas e transição — 20h20 às 20h30

- Abra para perguntas (≈7 min).
- 20h27: chamar as equipes, conferir se cada uma está com o site aberto e com o nome da equipe digitado.
- Slides 42 e 43 (referências e créditos) são só para consulta; não precisam ser apresentados.

**Se estiver atrasado**, corte nesta ordem (economiza ~8 min): slide 9 (Ágil), slide 20 (SDD no mercado),
slide 21 (linha do tempo dos dados) e passe mais rápido pelos slides 32–37 (a jornada aparece no próprio site).

---

## 3. O que ainda falta (checklist da organização)

**Antes do evento**

- [ ] **Definir quem recebe os kits no WhatsApp** (número/nome) e combinar como avisar as equipes (falar no
      slide 40, escrever no quadro ou mandar no grupo do evento).
- [ ] **Geração dos painéis entre 21h30 e 21h40** (kits pedidos até 21h30): 10 minutos é pouco para rodar o
      agente em série para todas as equipes. Combine rodar em paralelo (uma máquina por pessoa da
      organização) e começar os pitches pelas equipes cujo painel ficou pronto primeiro.
- [ ] **Testar a máquina da organização** que vai rodar o agente: agente instalado e logado, Python +
      Streamlit, e um teste completo com um kit de exemplo (baixar do site → enviar no WhatsApp → extrair →
      rodar o prompt → abrir o painel).
- [ ] **Lista das equipes e missões** (quem fica em qual equipe e qual desafio cada uma recebe).
- [ ] **Ensaio com cronômetro** (tecla **S** mostra o cronômetro), principalmente a parte do Pedro (Analy).
- [ ] Conferir se a citação do caso Analy e a frase “meses → semanas” estão liberadas para apresentação
      pública.

**No dia, na sala**

- [ ] Testar o projetor com `da_spec_ao_app.html` em tela cheia (**F**) e as notas (**S**) no notebook.
- [ ] Testar a internet da sala no celular (o site precisa de internet). Plano B: rodar o site num computador
      local (`streamlit run app.py`) com todos na mesma rede — ver README.
- [ ] Abrir o site uma vez antes (o Streamlit Cloud pode “dormir” e leva alguns segundos para acordar).
- [ ] Ter o PDF num pendrive como reserva.
- [ ] Lista de presença / certificados.
