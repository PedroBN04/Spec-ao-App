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

## Pendências da spec (decidir antes do M6)

- **Teste do N09:** na amostra, N09 remove 19,5% das linhas e a seção 14 pede ≥ 20%. Proposta: baixar o
  limite do teste para ≥ 15% (o bloco e a amostra não mudam).
