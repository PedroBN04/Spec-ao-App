# CLAUDE.md

Este repositório contém o app didático "Da Spec ao App" (Streamlit + pandas) para um minicurso + hackathon.

- A especificação completa está em `APP_SPEC.md`. Leia inteira antes de qualquer código.
- Implemente na ordem dos marcos da seção 13 da APP_SPEC. Ao fim de cada marco: `streamlit run app.py` precisa abrir sem erros e `pytest` precisa passar.
- O código de cada bloco de tratamento (seção 8) é a fonte única da verdade: o app exibe e executa exatamente esse texto. Não "corrija" os blocos de armadilha; eles são errados de propósito.
- Interface 100% em português do Brasil, linguagem simples, para iniciantes.
- Sem APIs externas, sem banco de dados, sem login.
- Decisões não cobertas pela spec: escolha a opção mais simples e registre em `DECISOES.md`.
- Nunca altere os CSVs em `data/` pelo app; eles são gerados por `scripts/preparar_dados.py`.
