# Base Canônica TCE-MG — Painéis

App estático (GitHub Pages) que consulta o Supabase:
- **Painel 1 — Dados Estratégicos**: servidores (SICOM) + atores de sites (fontes complementares); CPF mascarado.
- **Painel 2 — Cadastro Institucional**: órgãos/entidades (PNTP+SICOM+sites), contatos, gestores, geo.
- **Painel 7 — Obras e Serviços de Engenharia**: órgãos/setores que **contratam obras** (lead B2G), com
  contato (email/telefone/site), nº de obras, valor, modalidades e as secretarias/setores que publicaram.
  Fonte: PNCP + classificação heurística de obra + RFB. Ver [docs/PAINEL_OBRAS_ENGENHARIA.md](docs/PAINEL_OBRAS_ENGENHARIA.md).
  Tem `emails_setoriais` (email por secretaria, do cadastro por CNPJ; múltiplos separados por vírgula).
- **Painel 11 — Pessoas ligadas a Obras**: pessoas (nome · função/setor · email) dos órgãos **executivos**
  que contratam obra. Fonte: `painel6_responsaveis` (com email) + engenheiros do `painel1_servidores`,
  deduplicado por pessoa. Tabela `pessoas_obras` (ver `db/schema_p11.sql`, carga `tools/build_pessoas_obras.py`).

Navegação por município, busca, filtros e troca entre os painéis.

## Setup
1. Crie projeto no Supabase, rode `db/schema.sql` no SQL Editor.
2. Carregue os dados: `SUPABASE_URL=... SUPABASE_KEY=service_role python3 tools/load_supabase.py painel1 <painel_MG_enriquecido.csv>` (e `cadastro`).
3. Preencha `config.js` com a URL + anon key.
4. Ative GitHub Pages (branch main, /root).

### Painel 7 (obras)
1. Rode `db/schema_p7.sql` no SQL Editor.
2. Colete: `python3 tools/pncp_obras_engenharia.py --inicio 20260101 --fim 20260706 --uf MG` (Fase 1 MG; depois `--resume` sem `--uf` p/ o Brasil).
3. Carregue: `SUPABASE_URL=... SUPABASE_KEY=service_role python3 tools/load_obras_engenharia.py`.

Dados 12/2024 (P1/P2). CPF é chave interna, mascarado na exposição (LGPD/LAI).
