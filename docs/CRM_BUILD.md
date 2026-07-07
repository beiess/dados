# Plenum CRM — Build real (MVP)

App: `crm/index.html` (vanilla JS + supabase-js CDN, mesmo padrão do painel).
Conceito navegável que o originou: `crm/crm-conceito.html` (v14) e Artifact
https://claude.ai/code/artifact/4c107f85-67e6-40dd-bad9-15b8a33bd60d

## Decisões do MVP
- **Front-end**: vanilla JS estático (GitHub Pages), sem build step — igual aos painéis.
- **Escopo**: fluxo completo do funil (login → cascata → campanha → captura → 360 → equipe),
  comissão *prevista* calculada no cliente; motor de apuração automática = Fase 2
  (`apuracoes` já existe e é imutável — gestor insere via app/SQL).
- **Visibilidade**: equipe inteira (org = matriz + filiais) vê todas as capturas (RLS).

## Regras de negócio implementadas (schema + app)
- Captura é **por servidor**; `ux_cap_servidor_ativo` garante **uma campanha por vez**.
- Quem captura vira **responsável**; transferir/remanejar = **só gerente/admin**
  (trigger `t_capturas_resp`).
- **Escopo do rateio, % e valor unitário** ficam na **campanha** (admin define; captura herda).
- Comissão: `regras_versoes` com vigência (`vigente_ate NULL` = vigente) e `apuracoes`
  **imutáveis** com `regra_versao` + `regra_snapshot` (regra aplicada à época).
- Login CPF+senha = alias `cpf<digitos>@crm.plenumbrasil.com.br` no Supabase Auth;
  o app aceita **email ou CPF**. `israel@licitapublica.com.br` → `acesso_irrestrito`.
- Meta configurável por vendedor (`funcionarios.meta_individual`).
- LGPD: CPF mascarado na exibição; senhas preenchidas no app ficam TRANSIENTES em
  `logins_pendentes` (só gestor lê) até `crm_logins.py` provisionar e apagar.

## Passo a passo (ordem)
1. **Schema** — rodar `db/schema_crm.sql` no SQL Editor:
   https://supabase.com/dashboard/project/ntkntgcegvqqlarjspjp/sql/new
2. **Colaboradores** — `source .supabase_env && python3 tools/load_crm_colaboradores.py`
   (planilha RH → empresas/funcionarios; PII não vai ao git).
3. **Cascata** — `python3 tools/load_crm_entidades.py` (painel de obras →
   crm_entidades/setores/servidores; `--dry` para conferir, `--force` recarrega).
4. **Logins** —
   - `python3 tools/crm_logins.py --link israel@licitapublica.com.br --senha <senha>`
     (cria/vincula o acesso irrestrito);
   - depois que o admin preencher CPF+senha nos cadastros do app:
     `python3 tools/crm_logins.py` (provisiona pendentes e apaga as senhas).
5. **Publicar** — commit + push (GitHub Pages serve `/crm/`).
   Local: `python3 -m http.server` na raiz e abrir `http://localhost:8000/crm/`
   (o app usa `../config.js`).

## Fase 2 (pendências conhecidas)
- Motor `calcular_comissao()` (progressivo/pós-meta/base×novo/rateios) gravando `apuracoes`.
- Participações múltiplas na captura via UI (tabela `participacoes` já pronta).
- Sigilo server-side: limites de volume por sessão, log de acesso, watermark por usuário.
- Realtime (supabase channel) para "todos veem a evolução" sem recarregar.
