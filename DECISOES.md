# Decisões de implementação

Decisões tomadas onde a APP_SPEC não diz nada, é ambígua ou conflita com os dados reais.
Regra geral (CLAUDE.md): na dúvida, a opção mais simples.

## Regra permanente

- **O código dos blocos é intocável.** O campo `codigo` de todos os blocos, inclusive armadilhas e
  "depende", é cópia literal da seção 8 da APP_SPEC. `tests/test_blocks.py` lê as tabelas do
  `APP_SPEC.md` e confere código, título, grupo, categoria, requisitos e feedback de cada bloco.

## Marco M1 — Esqueleto e dados

1. **Amostra do hotel inclui os defeitos raros.** Com `sample(n=30000, random_state=42)` puro, a amostra
   ficava sem `children` vazio, sem `adr` negativa e sem `adr` > 1000. Assim, H01 e H10 não fariam nada,
   seus feedbacks ficariam falsos e duas regras de checklist nunca disparariam. Agora o
   `preparar_dados.py` sempre inclui essas 6 linhas e completa as 30.000 com
   `sample(random_state=42)` sobre o resto. Nada é limpo. O script também confere esses defeitos.
2. **Telco é copiado byte a byte** (`shutil.copyfile`), para garantir a "cópia integral".
3. **pandas fixado em `>=2.2,<3`.** A spec diz que os blocos foram testados com pandas 2.x. No pandas 3,
   texto vira o tipo `str` em vez de `object`, o que mudaria o que o participante vê.
4. **`Block.sugestao`** (campo novo, opcional): id do bloco correto sugerido após uma armadilha
   ("Experimente o bloco T02"). Telco: T03 → T02. As armadilhas T09, T10 e T11 não têm bloco
   substituto; só o feedback é mostrado.
5. **`Theme.emoji`** (campo novo, opcional): ícone do cartão da etapa 1.
6. **Hotel e noshow no M1** têm nome, problemática, proposta, fonte, licença e dicionário completos, para
   os cartões da etapa 1 e o diagnóstico funcionarem. Blocos, regras e `spec_defaults` entram no M6.
7. **Licenças** (conferidas nas páginas do Kaggle em 23/11/2026, ver item 20): telco "Data files ©
   Original Authors" (sem licença aberta); hotel CC BY 4.0; noshow CC BY-NC-SA 4.0.
8. **Regras de checklist do telco** já estão no tema, com ids `TEL01`–`TEL05`. A execução e a etapa 4
   vêm no M4.
9. **Estado entre etapas.** O Streamlit apaga o valor de widgets que saem da tela. Os valores ficam em
   `st.session_state` com nome próprio (`equipe`, `diagnostico_lido`) e os widgets (`w_<nome>`)
   são reabastecidos ao voltar (`campo_persistente`).
10. **Trocar de desafio** pede confirmação só se já houver passos aplicados ou respostas da SPEC.
    Confirmando, zera pipeline, checklist, SPEC e o checkbox do diagnóstico.
11. **Etapas 3 a 6** existem como telas "em construção" navegáveis até seus marcos.
12. **Erro inesperado em qualquer tela** mostra mensagem simples e o detalhe técnico num expander
    (requisito 11: nenhuma exceção crua para o participante).

## Marco M2 — Diagnóstico

13. **"Parece número"**: ≥ 90% dos valores **não vazios** convertíveis após `str.strip()`.
14. **"Parece data"**: coluna de texto (que não parece número) com ≥ 90% dos valores no formato
    `AAAA-MM-DD` (com ou sem hora) ou `DD/MM/AAAA`. Usamos padrão de texto em vez de
    `pd.to_datetime` para não confundir números com datas.
15. **"1 valor só"** ignora vazios (`nunique(dropna=True) <= 1`).
16. **O diagnóstico é sempre da base original** (antes do tratamento) e fica em cache por tema.
17. **Raio-X** mostra o tipo do pandas (`object`, `int64`...) com uma legenda em português logo abaixo.
18. **Gráfico de coluna** abre na primeira coluna que não é o alvo (o alvo já tem gráfico ao lado).

19. **Base original em `st.cache_resource`** (uma cópia na memória, compartilhada por todas as sessões),
    em vez de `cache_data` (que entrega uma cópia nova a cada chamada). A spec pede "carregada uma vez
    e nunca alterada": o executor sempre roda sobre `df.copy()` e nenhuma tela altera a original.
20. **Licenças conferidas** em 23/11/2026, no campo "License" de cada página do Kaggle (depois de liberar
    www.kaggle.com no ambiente de desenvolvimento): telco "Data files © Original Authors", hotel
    "Attribution 4.0 International (CC BY 4.0)", noshow "CC BY-NC-SA 4.0". README e campo `licenca`
    dos temas atualizados. A base telco não tem licença aberta: o README avisa para usar só no
    contexto educacional e consultar os autores antes de redistribuir.

## Marcos M3 e M4 — Tratamento e checklist

21. **Desfazer em cascata:** além de colunas faltando, um passo cujo **bloco pré-requisito** foi desfeito
    também sai (ex.: desfazer T01 remove T02, com aviso). Um passo que der erro ao ser reaplicado também
    sai, com aviso.
22. **Motivo de bloco desabilitado:** se falta um bloco: "Este bloco precisa que o bloco T01 seja aplicado
    antes."; se falta uma coluna criada por outro bloco: "Este bloco precisa da coluna `x`. Aplique antes
    o bloco N04 ou N05." (os blocos que criam a coluna são achados no próprio código); se a coluna existia
    na base original: "...que não existe mais na base atual (um passo anterior removeu ou renomeou)".
23. **N04 e N05 juntos:** ambos podem ser aplicados (cada um uma vez); vale o último.
24. **"Ver código"** é um botão que mostra/esconde o código (o Streamlit não permite um expander dentro de
    outro).
25. **Bases muito largas (T11):** a tabela mostra só as 50 primeiras colunas, com aviso. O CSV exportado
    tem todas. O código do bloco não muda.
26. **Tipos amigáveis:** a etapa 3 mostra "texto → número decimal" em vez de `object → float64`.
27. **Mensagem após aplicar:** além do cartão no pipeline (com `st.warning` + sugestão para armadilhas),
    o topo mostra "Bloco X aplicado. Veja a avaliação em Meu pipeline", porque o pipeline pode estar
    fora da tela em 1366×768.
28. **Clique duplo em Aplicar:** o callback ignora um bloco que já está no pipeline.
29. **Checklist — G01 "versão tratada"**: `Theme.alvos_aceitos` (noshow: `faltou`, `no_show_original`).
    Depois do T11, `Churn` vira `Churn_No`/`Churn_Yes` e G01 acusa erro — comportamento intencional.
30. **Checklist — G02 "nem derivada"**: `Theme.vazamento_derivado` (telco: `taxa_churn_pagamento`; hotel:
    prefixo `status_`). A spec também tem regras do tema para o mesmo caso; as duas contam (ex.: T09 gera
    G02 e TEL01), como a spec descreve.
31. **Item informativo (G07)** aparece como "ℹ️ Informação" e não entra no placar nem na nota.
32. **"Vou corrigir"** não libera o avanço: o item só sai da lista quando a regra passa. "Vou manter" exige
    justificativa com ≥ 15 caracteres (sem contar espaços nas pontas). Justificativas ficam guardadas por
    regra; se a regra passar depois, a justificativa é ignorada.
33. **Regra com defeito** (exceção dentro da função) aparece como não verificada, sem derrubar a tela.

## Marco M5 — Assistente da SPEC e exportação

34. **Nome da solução** (`{nome_da_solucao}` do template): campo opcional no passo 1, com padrão
    "Painel — <nome do desafio>".
35. **Listas** (funcionalidades, regras, critérios, fora do escopo) são caixas de texto com **um item por
    linha**, já preenchidas com os `spec_defaults`; marcadores "-", "*" e "•" no início são ignorados.
36. **Passo 3 (Dados):** só o **significado** é editável; coluna e tipo vêm do DataFrame real (seção 10).
    Tipos aparecem em português ("texto", "número inteiro"...). Colunas criadas por blocos têm descrição
    própria (`Theme.dicionario_extra`) ou "Criada pelo bloco X: título". Colunas cujo tipo foi mudado
    por um bloco ganham "ATENÇÃO: valores convertidos pelo bloco T07 (...)". Só os significados
    editados pela equipe são guardados; os demais acompanham a base.
37. **Aviso de colunas inexistentes:** nos passos 4, 5 e 7, se o texto cita uma coluna conhecida do tema
    que não está na base final (ex.: critério com `customerID` depois do T08), aparece um aviso.
38. **3.1:** "título — categoria — feedback do bloco" (feedback completo; ver item 51). **3.2:** só erros/alertas que continuam
    falhando e foram mantidos com justificativa válida. **3.3:** colunas de vazamento presentes
    (`colunas_vazamento` + `vazamento_derivado`) e observações do tema (`Theme.observacoes`), mostradas
    só se a coluna existir.
39. **Alvo na seção 3:** primeiro nome aceito presente (ex.: `faltou`), senão o alvo original; se não
    existir, aparece "(ausente na base tratada)".
40. **Data da SPEC** no formato dd/mm/aaaa.
41. **Datas no CSV:** colunas de data com fuso (N03 gera UTC) são convertidas para UTC sem fuso;
    `AAAA-MM-DD` se todas as horas forem 00:00, senão `AAAA-MM-DD HH:MM:SS`.
42. **Nomes dos arquivos:** equipe sem acentos, minúsculas, espaços → `_`, demais símbolos removidos
    ("Equipe Ação Já!" → `equipe_acao_ja`). A etapa 6 orienta renomear para `dados_tratados.csv` e
    `SPEC.md`, que são os nomes citados no prompt e na SPEC.
43. **Etapa 6** mostra aviso (sem bloquear o download) se o checklist ou a SPEC ficaram com pendências
    depois de a equipe voltar e mudar o tratamento.
44. **Prévia da SPEC:** formatada por padrão; botão "Ver como texto" alterna para `st.code`.

## Marco M6 — Temas hotel e noshow

45. **Código, título, grupo, requisitos e feedback dos blocos H01–H14 e N01–N14** foram gerados por script
    a partir das tabelas do `APP_SPEC.md` (cópia literal) e conferidos por `tests/test_blocks.py`. Só
    explicação, pergunta de reflexão e sugestão foram escritas à mão.
46. **Teste do N09 ajustado (o bloco NÃO mudou):** a seção 14 pede "N09 remove ≥ 20% das linhas". Na
    amostra do repositório (seed 42) o N09 remove **19,54%**. Pela regra do projeto, o teste passou a
    exigir ≥ 15%, que ainda comprova "apagou grande parte da base".
47. **Sugestões de bloco correto:** H05 → H04, H07 → H08, H11 → H10, N02 → N01, N05 → N04, N08 → N07.
    N09 não tem bloco substituto.
48. **Hotel:** `vazamento_derivado = ("status_",)` (colunas criadas pelo H07). Regras HOT01–HOT05
    conforme 8.2.
49. **Noshow:** `alvos_aceitos = ("faltou", "no_show_original")`. Regras NOS01–NOS05 conforme 8.3; a de
    idade olha `Age` ou `idade` (depois do N14). Colunas renomeadas pelo N14 herdam o significado do
    dicionário original (`Theme.dicionario_extra`).
50. **G05 ignora identificadores** (nome terminado em `Id`/`ID`/`_id` ou começando com `id_`): o N10
    (boa prática) transforma `PatientId` em texto de propósito; sem essa exceção, a boa prática
    geraria alerta de "número guardado como texto".
51. **SPEC 3.1** usa o feedback inteiro do bloco (1 a 3 frases), não só a primeira frase: no N06 a
    primeira frase ("Com N04, ...") enganava quando a equipe usou o N05.
52. **Pipeline compacto:** cada passo é um expander (o mais recente aberto) com as métricas numa linha
    ("Linhas: 30.000 → 25.826 (−4.174)"), para caber em 1366×768 com muitos passos.
53. **Observação (não alterado):** o feedback do H05 diz "apagou mais de 90% da base"; se o H04 for
    aplicado antes, o H05 remove bem menos (~14%). O texto é o da spec; as métricas ao lado mostram o
    valor real.

## Marco M7 — Polimento e deploy

54. **`.streamlit/config.toml`:** `toolbarMode = "viewer"` (esconde o botão "Deploy" e o menu de
    desenvolvedor, em inglês), `showErrorDetails = "none"` (nunca mostrar traceback), tema claro e sem
    coleta de estatísticas de uso.
55. **Dica "Press Enter to apply"** do Streamlit (em inglês) escondida com uma regra de CSS de uma linha;
    os campos orientam em português ("digite e tecle Enter", "clique fora do campo ou tecle Ctrl+Enter").
56. **Termos técnicos** ganharam dica na primeira aparição: CSV e agente de código (etapa 0), pipeline e
    bloco/pandas (etapa 3), nulo, alvo, histograma, tipos (etapa 2).
57. **Erro inesperado** mostra só "Tipo: mensagem" no expander técnico (sem traceback).
58. **Limitação conhecida:** menus internos de componentes do Streamlit (ex.: ícones da tabela, indicador
    "Running" no canto) continuam em inglês; não há configuração para traduzi-los.
59. **Deploy:** Python 3.12 no Streamlit Community Cloud; `requirements.txt` com faixas de versão
    testadas (instalação limpa conferida: streamlit 1.67.0, pandas 2.3.3, numpy 2.5.5, plotly 6.9.0).

## Auditoria final

60. **Recarregar a página recomeça do zero.** É consequência direta de "nada é salvo no servidor" (seção
    11) e de cada sessão viver em `st.session_state`. Em vez de persistir dados, a etapa 0 avisa:
    "Não recarregue a página (F5) nem feche a aba até baixar os arquivos".
61. **Capacidade (teste de carga):** 10 sessões simultâneas no tema hotel, cada uma aplicando 9 blocos
    e indo até a exportação: o servidor foi de 77 MB para um pico de 471 MB (~28 MB por sessão ativa).
    Estimativa para 25 sessões: ~780 MB — cabe em 1 GB, mas com pouca folga. O T11 (one-hot do telco)
    sozinho ocupa ~96 MB por sessão que o aplicar; o código do bloco não pode mudar. Recomendação:
    uma sessão por equipe (não por participante).
62. **"Barra de progresso fixa no topo"** foi interpretada como "presente no topo de toda tela" (não
    grudada na rolagem), para evitar CSS complexo (seção 11).
63. **Selo "Depende do objetivo"** usa a cor laranja: o `st.badge` do Streamlit não tem amarelo.

## Ensaio do hackathon (melhorias no spec builder)

Ensaio: jornada telco com boas escolhas, exportação, e um app construído só a partir da `SPEC.md`
(pasta `../ensaio_hackathon/`, fora do repositório). Na 1ª rodada os 4 critérios passaram, mas o agente
precisou de 5 suposições. Melhorias:

64. **Coluna "Valores reais" na seção 3** (e no passo 3 do assistente): calculada do DataFrame final —
    lista de categorias (até 12), faixa mín–máx para números e datas, nº de vazios. Resolve descrições do
    dicionário que ficam desatualizadas depois dos blocos (ex.: `SeniorCitizen` vira Yes/No pelo T05;
    "No internet service" some pelo T06 sem mudar o tipo). A SPEC avisa que os valores reais valem mais
    que o significado. É uma coluna a mais no template 9.1.
65. **"Números de referência" na seção 7**, calculados do CSV exportado (nº de linhas e taxa do alvo),
    para o agente conferir os critérios ("taxa geral = 26,5%"). Acréscimo ao template 9.1.
66. **Defaults mais precisos:** telco define "cliente ativo = Churn 0", `TechSupport = No`, formato das
    taxas (26,5%), moeda sem símbolo (a base não informa a moeda) e ordenação da lista de risco; hotel
    define formato e ordenação do ranking; noshow define o que são "consultas futuras" numa base de 2016,
    formato das taxas e as colunas/ordem da lista de risco.
67. **No passo 3 do assistente** a coluna editável "Significado" vem logo depois do nome da coluna.

Resultado da 2ª rodada: 4/4 critérios + 2 conferências extras (ordenação e só clientes ativos), sem
suposições sobre dados ou regras.

## Revisão dos textos (após o deploy)

68. **Uso educacional:** o repositório continua público; o README abre com o aviso "Projeto educacional,
    sem fins comerciais" e a etapa 1 mostra que as bases são usadas só para fins educativos.
69. **Correções de texto no hotel** (conferidas nos dados): `is_canceled = 1` inclui cancelamentos **e**
    no-shows (as 291 reservas "No-Show" têm `is_canceled = 1`); a base não informa a moeda de `adr`
    (tiramos "euros"); só 8 segmentos hotel × depósito × canal têm ≥ 100 reservas, então a
    funcionalidade fala em "ranking dos segmentos (até 10)".
70. **README** passou a descrever a amostra do hotel como ela é (6 linhas raras sempre incluídas).

## Versão 2 (pedido da organização após o deploy)

A organização pediu um app menos "mastigado", com mais liberdade, para públicos de níveis diferentes, e um
visual mais profissional. Decisões tomadas com a organização:

71. **Gabarito só no final:** categoria, feedback, pergunta de reflexão e sugestão de bloco não aparecem
    durante a jornada. Depois da exportação, a etapa "Revisão com o facilitador" mostra: a categoria e o
    feedback de cada passo, as boas práticas não usadas, as regras de qualidade (G01–G06 + regras do tema)
    e uma SPEC de referência (os `spec_defaults`).
72. **Missões:** `Theme.area_cliente`, `solicitante` e `missao` (mensagem da área cliente, sem nomes de
    pessoas). A tela deixa claro que dá para priorizar, deixar de fora com justificativa ou ir além.
73. **Diagnóstico sem alertas:** a lista de alertas automáticos e a coluna "Alerta" saíram da tela (as
    funções continuam em `core/diagnostics.py`). Entraram o roteiro de 8 perguntas genéricas, o Raio-X
    factual (mín./máx.), o explorador de colunas com estatísticas e a relação com o alvo, e anotações
    obrigatórias (≥ 30 caracteres), que reaparecem na pipeline e na SPEC.
74. **Pipeline estilo n8n, nativa do Streamlit** (sem componente de arrastar e soltar): nós ligados de
    entrada a saída, com subir/descer/remover, código e "por que este passo?" (vai para a SPEC 3.1). Toda
    mudança de ordem reexecuta o fluxo a partir da base original; passos que deixam de fazer sentido saem
    com aviso neutro.
75. **Blocos personalizados** (`core/blocos_livres.py`): 11 ações (remover colunas, preencher vazios,
    remover linhas com vazios, converter tipo, filtrar linhas, substituir valor, criar faixas, criar coluna
    0/1, calcular coluna, renomear, remover repetidas). O código é gerado a partir de escolhas em listas e
    de valores convertidos em literais Python (`repr`), então nenhum texto digitado é executado como
    código. Categoria "livre".
76. **Os 41 blocos da seção 8 continuam com o código literal** (teste mantido). Um bloco do catálogo entra
    no fluxo uma vez; blocos personalizados podem se repetir.
77. **Revisão factual** (`core/revisao.py`): antes × depois de linhas, colunas, vazios, repetidas, texto
    que parece número e presença da coluna de resultado original, mais comparativo por coluna. Sem nota.
    Observações opcionais (vão para a SPEC 3.2) e confirmação "Revisei o resultado".
78. **SPEC em branco:** todos os campos começam vazios (escopo marca os pedidos da área desmarcados);
    perguntas-guia por passo e um exemplo de outro domínio (biblioteca municipal) sob demanda. Automáticos
    continuam só os fatos dos dados: tabela da seção 3 (significado da documentação da base, editável),
    passos aplicados (sem categoria) e números de referência. Nome padrão: "Solução — <equipe>".
79. **Visual:** tema próprio no `.streamlit/config.toml` (Inter, índigo, cantos arredondados), navegação
    lateral por etapas (dá para voltar a qualquer etapa já visitada), glossário na barra lateral, ícones
    Material no lugar de emojis e pouco CSS.
80. **Itens da v1 substituídos:** a nota de qualidade, as justificativas obrigatórias do checklist, os selos
    durante o tratamento e os avisos de "colunas que parecem números" na tela deixam de existir na
    jornada (decisões 4, 26–33 e 36–38 valem só para o gabarito ou foram superadas).

## Proposta de melhorias da equipe (aprovada pela organização)

Avaliação completa feita antes de implementar. Dois itens da proposta foram mantidos como estão porque são
intencionais na spec: o bloco N02 (`compareceu` com leitura invertida) é uma **armadilha** da seção 8.3, e o
N14 (renomear para português) bloquear os demais blocos é o próprio ensinamento do bloco ("a ordem das
operações importa"). O app já usava `layout="wide"`; os cortes vinham da escala de tela do Windows
(125–150%) somada à barra lateral.

81. **Exportação (P0.4):** kit `kit_<equipe>.zip` como botão principal, com `dados_tratados.csv` (vírgula,
    para a IA), `dados_tratados_excel.xlsx` (planilha real, abre em colunas no Excel em português, números
    como números) e `SPEC.md`, já com os nomes finais. Downloads avulsos ficam num expander. O kit é gerado
    só no clique (o .xlsx do hotel leva ~7 s). Bases com mais de 3 milhões de células (ex.: depois do T11)
    saem sem o .xlsx, com aviso. Dependências novas: `xlsxwriter` (gera) e `openpyxl` (testes leem).
    Todas as tabelas sem coluna de índice.
82. **Rascunho .json (P3.1):** "Salvar ou retomar progresso" na barra lateral. O arquivo guarda só dados
    (nunca código), é validado ao retomar e a pipeline é reexecutada da base original. A barra lateral é
    desenhada depois da etapa, para o rascunho já incluir o que acabou de ser digitado.
83. **Início (P2.1):** nome da equipe num `st.form`; "Começar" funciona sem Enter e avisa se estiver vazio.
84. **Missão (P2.2):** durante a confirmação de troca, a mensagem é "Confirme ou cancele a troca de missão".
85. **Dependências (P2.3):** mensagens citam o nome do bloco, nunca o código (T01, N03...). Mover um passo para
    uma posição inválida não muda nada (o passo e a justificativa ficam) e explica por quê. Textos de exemplo
    dos campos em português ("Escolha uma opção").
86. **Significado na SPEC (P2.4):** `Theme.significado_apos` dá o significado depois de conversões conhecidas do
    catálogo (ex.: depois do T07, `Churn` = "1 = cancelou, 0 = continua"). Para blocos personalizados, o
    significado avisa que os valores mudaram. Texto "para 1 hora" trocado por tempo flexível.
87. **Linguagem (P1.1/P1.2):** termo em português primeiro e o técnico entre parênteses (churn, antecedência,
    diária, overbooking, one-hot, z-score). A pipeline é explicada como linha de montagem/receita, com o n8n
    como segundo exemplo. Glossário com 20 termos. Kaggle explicado. Instruções finais para qualquer
    assistente de IA (no computador ou chat na web).
88. **Diagnóstico (P1.3):** números no padrão brasileiro nas tabelas; gráficos sem a barra de ferramentas em
    inglês e com vírgula decimal; uma frase explica cada aba do explorador.
89. **Meio-termo da tradução (P0.3):** as bases continuam com os nomes e valores originais (o código dos 41
    blocos da seção 8 depende deles). O app mostra o equivalente em português: coluna "Em português" no
    Raio-X, nome em português no explorador e tradução dos valores na tabela "Valores mais frequentes"
    (`core/themes/traducoes.py`).
90. **Meio-termo dos vazios disfarçados (P1.3):** indicador factual "Células só com espaços" ao lado de
    "Células vazias (nulos)", sem tom de alerta. `PatientId` continua como número decimal (defeito didático
    tratado pelo N10).
91. **Meio-termo das linhas repetidas (P1.4):** o efeito de cada passo mostra "linhas repetidas: 0 → 22"
    (fato). A explicação da causa fica no gabarito. A contagem é desligada para bases com mais de 200 colunas
    (no T11 levaria ~2 s por passo).
92. **Meio-termo do rascunho guiado (P2.4):** botão "Usar esqueleto com lacunas" em cada passo da SPEC, com
    frases genéricas e lacunas [entre colchetes], sem conteúdo de nenhum tema. Só preenche campos vazios.
    Campo obrigatório com lacuna não preenchida conta como pendente.
93. **Gabarito (P3.3):** quando o tema tem o próprio limite de colunas (telco: 50), o genérico (60) não aparece.
94. **Layout estreito (P0.2):** biblioteca e fluxo em colunas iguais; rótulos curtos ("Código", "Próximo
    passo", "Texto"); margem inferior maior para o selo do Streamlit Cloud não cobrir botões. Conferido sem
    cortes em 1093×614 (1366 a 125%), 1280×720 e 1366×768.
95. **Não feito (fora do alcance do app):** "Fork" e ícone do GitHub no topo são do Streamlit Community Cloud
    para repositórios públicos; nenhuma configuração do app os esconde. Só tornar o repositório privado.
