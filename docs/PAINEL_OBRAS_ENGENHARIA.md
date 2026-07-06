# Painel 7 — Obras e Serviços de Engenharia

**Objetivo (lead B2G):** cadastro dos **órgãos e setores/secretarias que CONTRATAM obras e
serviços de engenharia**, com o que interessa para abordagem comercial —
`UF → Município → Órgão (CNPJ) → Setor (Secretaria de Obras) → contato (email/telefone/site)` —
mais o volume de demanda (nº de obras, valor estimado, modalidades, exemplos de objeto).

Novo painel, no mesmo padrão do **Painel 2N** (PNCP em cascata), porém **recortado para obras**.
Grão duplo: **órgão (CNPJ)** + **setor (unidade que publicou a obra)**.

---

## 1. Fonte e recorte

Espinha dorsal: **PNCP** consulta `GET /v1/contratacoes/publicacao` (CORS ✓, sem chave), mesma
varredura do P2N (janela × modalidades, dedup por CNPJ).

**Como identificamos "obra/serviço de engenharia":** o PNCP **não** expõe a categoria de obra na
consulta pública — o `objetoCompra` é texto livre e a categoria do item vem quase sempre
`"Não se aplica"`. Portanto classificamos por **heurística textual sobre `objetoCompra`**, em 3
camadas (código em `tools/pncp_obras_engenharia.py`, função `eh_obra`):

1. **NEG** — exclui confusáveis: insumo agrícola (herbicida/defensivo/adubo/semente), merenda e
   material escolar, gêneros alimentícios, medicamentos, combustível, compra pura de material de
   construção, obra literária/reforma agrária.
2. **STRONG** — termo inequívoco de obra basta 1: `obra`, `construção`, `pavimentação`,
   `drenagem`, `calçamento`, `terraplenagem`, `edificação`, `empreitada`, `adutora`, `barragem`,
   `esgotamento`, `infraestrutura`, `serviços de engenharia`, e **estruturas de engenharia civil**
   inerentemente obra (`ponte`, `passarela`, `viaduto`, `tubulão`, `bueiro`, `poço tubular`,
   `estação elevatória`), além de `engenharia` isolado.
3. **STRUCT + verbo** — substantivo estrutural (`escola`, `creche`, `posto de saúde`, `quadra`,
   `rodovia`, `estrada`, `rede de esgoto/água`, `iluminação pública`, `telhado`…) **só** conta como
   obra se houver também um **verbo de construção/execução** (`construção`, `reforma`, `ampliação`,
   `execução`, `implantação`, `pavimentação`…). Isso evita "merenda escolar", "transporte escolar",
   "herbicida em estradas vicinais" etc.

Validação ao vivo (amostra MG, modalidades 4/8): **precisão alta** no bucket de obra e recall
recuperado em casos difíceis (ponte terse do DER-MG, tubulão). Bateria de regressão em 13 casos:
13/13. Por ser recorte heurístico, todo registro leva **`grau_confianca = 'B'`** e guarda 2–3
**exemplos de objeto** (evidência) — distinto do `'A'` do cadastro (identificação por CNPJ oficial).

**Modalidades varridas** (default): `1,2,4,5,6,7,8,9,12`. Obras usam sobretudo Concorrência (4/5) e
Diálogo (2); Pregão (6/7) só p/ serviços comuns de engenharia; Dispensa/Inexigibilidade (8/9) para
obras emergenciais/pequeno valor. Varrer todas maximiza cobertura; a classificação filtra o objeto.

## 2. Enriquecimento (contato)

Dois passos, porque **email de órgão público não vem da Receita**:

1. **RFB** via `minhareceita.org/{cnpj}` (cache em `data_full/.rfb_cache.json`): situação cadastral
   (100%), endereço, natureza jurídica e **telefone** (~66%). ⚠️ **Email: 0%** — verificado ao vivo,
   o espelho da RFB (e a BrasilAPI) redigem o campo `email` mesmo p/ CNPJ privado; para órgão público
   a Receita raramente tem email cadastrado. **Não use RFB para email.**
2. **Cross-ref por CNPJ com `cadastro_institucional` (Painel 2)** — `tools/enrich_obras_email.py`.
   O Painel 2 tem **emails institucionais curados de MG** (`prefeitura@x.mg.gov.br`, ouvidoria,
   setoriais) com CNPJ. Join determinístico preenche **email (~32%)** e completa **telefone (→77%)**.
   Idempotente; rodar após a carga. É a fonte correta do email institucional.

`site` fica a construir (sem API; padrões `*.gov.br` / semente `entidades-tce-mg.csv`). Melhoria
futura: usar `emails_setoriais` do cadastro para email **por secretaria** (match por nome de setor).

## 3. Modelo de dados

Cascata (JSON) + achatado (CSV, 1 linha = órgão) + Supabase (`db/schema_p7.sql`):
- **`obras_engenharia_orgaos`** (grão = CNPJ): razão social, poder, esfera, UF, município, cod_ibge,
  `n_obras`, `n_setores_obras`, `valor_estimado_obras`, `modalidades_obras`, `primeira_obra`,
  `ultima_obra`, `exemplos_objeto`, email, telefone, situação, endereço, site + proveniência.
- **`obras_engenharia_unidades`** (grão = setor): `nome_unidade` (a "Secretaria de Obras"),
  `n_obras`, `valor_estimado_obras`, `ultima_obra`.

> Nota de granularidade: o "setor" é a `unidadeOrgao` do PNCP. Onde o município registra uma
> **Secretaria de Obras/Infraestrutura** própria, ela aparece; onde publica sob a unidade genérica
> "Prefeitura Municipal", é isso que consta (limite honesto da fonte). Órgãos especializados
> (ex.: **DER-MG**) trazem setores granulares.

## 4. Operação

```bash
# Fase 1 — MG (validar) — janela do ano corrente, todas as modalidades de obra:
python3 tools/pncp_obras_engenharia.py --inicio 20260101 --fim 20260706 --uf MG

# Fase 2 — Brasil (background, resumível; sobe throttle p/ não tomar 429):
PNCP_THROTTLE=0.5 python3 tools/pncp_obras_engenharia.py --inicio 20260101 --fim 20260706 --resume

# Carga no Supabase (rodar db/schema_p7.sql antes):
SUPABASE_URL=... SUPABASE_KEY=service_role python3 tools/load_obras_engenharia.py            # 1ª carga (truncate)
SUPABASE_URL=... SUPABASE_KEY=service_role python3 tools/enrich_obras_email.py               # email/tel via cadastro (Painel 2)
SUPABASE_URL=... SUPABASE_KEY=service_role python3 tools/load_obras_engenharia.py --upsert   # retro semanal (reenriquecer depois)
```

Resiliência: throttle educado (`PNCP_THROTTLE`, default 0.34s) + **backoff em HTTP 429/5xx**
(respeita `Retry-After`) + checkpoint a cada 200 páginas em `data_full/.sweep_obras_state.json`
(retomar com `--resume`). Cache de RFB resumível.

## 5. Integração no painel (index.html)
Card **Painel 7 — Obras e Serviços de Engenharia**: árvore UF → Município → Órgão → Setores; ficha
do órgão (contato, nº de obras, valor, modalidades, exemplos, site); filtros por UF/esfera/poder e
faixa de nº de obras; busca; export CSV/Excel. Mesmo padrão dos demais (Supabase REST +
`data_full/*.json` para carga estática).

_Fonte da análise: sondagem ao vivo das APIs PNCP e minhareceita em 2026-07-06._
