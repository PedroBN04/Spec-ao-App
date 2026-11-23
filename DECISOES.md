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
7. **Licenças a confirmar no Kaggle:** telco sem licença explícita (base de exemplo da IBM);
   hotel CC BY 4.0 (artigo em acesso aberto); noshow CC BY-NC-SA 4.0.
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
20. **Licenças não puderam ser conferidas:** o kaggle.com está fora da rede permitida do ambiente de
    desenvolvimento. Os textos de licença ficam marcados "conferir" até a organização confirmar.

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
38. **3.1:** "título — categoria — primeira frase do feedback". **3.2:** só erros/alertas que continuam
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
