# Painel 1 — pipeline do cadastro central de pessoas físicas (22–24/07/2026)

Scripts que construíram o cadastro-ouro (8,42M pessoas). Todos idempotentes
(ledger próprio; só preenchem nulos / anti-join por chave), re-executáveis, e
leem `SUPABASE_DB_URL` do ambiente (`set -a && . ./.supabase_env && set +a`).

| script | função | chave/dedup |
|---|---|---|
| scan_v2.py | inventário de cabeçalhos (nascimento) c/ checkpoint | — |
| scan_fields.py | inventário de campos complementares (headers.jsonl) | — |
| enrich_loop.py | nascimento por arquivos locais → só nulos | CPF; nome+município |
| tse_nasc_mg.py | nascimento via TSE (candidaturas MG 2024/22/20) | CPF (só ≤2020); nome+município |
| incorpora_novos.py | novos cadastros de arquivos + P6/CRM + sexo/email/tel | CPF (anti-join); nome+ibge |
| backfill_chunks.py | materializa esfera+uf (blocos c/ commit) | classificação por origem/fonte |
| replay_p12.py | Painel 12 → 1 (SIAPE etc.), por fonte c/ ledger | matricula||'|'||nome + orgao |

Lições operacionais registradas na memória do projeto (UPDATE órfão não commita;
matrícula mascarada colapsa chave; DDL pesado via psycopg2 em blocos; nunca gravar
grande no FUSE do Drive).
