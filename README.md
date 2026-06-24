# Base Canônica TCE-MG — Painéis

App estático (GitHub Pages) que consulta o Supabase:
- **Painel 1 — Dados Estratégicos**: servidores (SICOM) + atores de sites (fontes complementares); CPF mascarado.
- **Painel 2 — Cadastro Institucional**: órgãos/entidades (PNTP+SICOM+sites), contatos, gestores, geo.

Navegação por município, busca, filtros, botão entre os dois painéis.

## Setup
1. Crie projeto no Supabase, rode `db/schema.sql` no SQL Editor.
2. Carregue os dados: `SUPABASE_URL=... SUPABASE_KEY=service_role python3 tools/load_supabase.py painel1 <painel_MG_enriquecido.csv>` (e `cadastro`).
3. Preencha `config.js` com a URL + anon key.
4. Ative GitHub Pages (branch main, /root).

Dados 12/2024. CPF é chave interna, mascarado na exposição (LGPD/LAI).
