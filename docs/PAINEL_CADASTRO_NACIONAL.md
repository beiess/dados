# Painel — Cadastro Institucional Nacional (PNCP em cascata)

**Objetivo:** cadastro de todas as instituições públicas do Brasil (órgãos, secretarias, autarquias,
câmaras, fundos) que **publicaram no PNCP**, em **cascata**:
`UF → Município → Órgão (CNPJ) → Unidades/Setores → Responsáveis (email/contato) → Site institucional → Info complementares`.

Novo painel, separado do atual **Painel 2 — Cadastro Institucional** (que é só MG, base TCE-MG).
Proposta de nome: **Painel 2N — Cadastro Institucional (Brasil / PNCP)**.

---

## 1. Espinha dorsal — PNCP (fonte primária, define "quem publicou")

Base: `https://pncp.gov.br/api/consulta` (CORS ✓, sem chave). Manual: `/swagger-ui/index.html`.

### 1.1 Enumeração dos publicadores — `GET /v1/contratacoes/publicacao`
Params obrigatórios: `dataInicial`, `dataFinal` (yyyyMMdd), `codigoModalidadeContratacao`, `pagina`.
`tamanhoPagina` deve ser **≥ 10** (default 10, máx 50). Resposta paginada:
`{data[], totalRegistros, totalPaginas, numeroPagina, paginasRestantes}`.

Cada registro traz o par órgão+unidade que **queremos** para a cascata:
```
orgaoEntidade: { cnpj, razaoSocial, poderId (L/E/J), esferaId (M/E/F/D) }
unidadeOrgao:  { ufSigla, ufNome, municipioNome, codigoIbge, codigoUnidade, nomeUnidade }
```
**Estratégia:** varrer janela temporal (ex.: últimos 12 meses) × modalidades, **deduplicar por `cnpj`**.
O conjunto de CNPJs converge rápido (instituições publicam com frequência).

Modalidades (`codigoModalidadeContratacao`): 1 Leilão-eletrônico · 2 Diálogo competitivo · 3 Concurso ·
4 Concorrência-eletrônica · 5 Concorrência-presencial · **6 Pregão-eletrônico** · 7 Pregão-presencial ·
**8 Dispensa** · 9 Inexigibilidade · 12 Credenciamento · 13 Leilão-presencial. Para enumerar publicadores,
**6 + 8** já cobrem a grande maioria; varredura completa usa todas.

### 1.2 Dados do órgão — `GET /api/pncp/v1/orgaos/{cnpj}`
`{ cnpj, razaoSocial, nomeFantasia, codigoNaturezaJuridica, poderId, esferaId, statusAtivo, validado }`.

### 1.3 Unidades/setores do órgão — `GET /api/pncp/v1/orgaos/{cnpj}/unidades`
Lista **completa** de unidades (não só as que publicaram):
`[{ codigoUnidade, nomeUnidade, municipio:{nome, codigoIbge, uf:{siglaUF, nomeUF}} }]`.
→ preenche o nível **Setores** da cascata.

---

## 2. Enriquecimento por CNPJ

| Campo desejado | Fonte | Endpoint | Cobertura |
|---|---|---|---|
| Natureza jurídica, situação, endereço, CEP, ente responsável | **RFB** | `https://minhareceita.org/{cnpj}` (espelho) · alt. `brasilapi.com.br/api/cnpj/v1/{cnpj}` | Alta |
| **Email / telefone** | **RFB** (mesmos endpoints) | campos `email`, `ddd_telefone_1/2` | ⚠️ **Parcial** — muitos órgãos públicos vêm vazios |
| UASG / código SIASG / órgão superior | **Compras.gov.br** | `dadosabertos.compras.gov.br/modulo-uasg/1_consultarUasg` (21.941 UASGs) | Federal/SISG |
| **Site institucional** | — (sem API) | enriquecimento: padrões `*.gov.br`, busca, semente `entidades-tce-mg.csv` (tem coluna URL p/ MG) | Baixa (a construir) |
| Sanções (CEIS/CNEP/CEPIM) | Portal da Transparência | `api.portaldatransparencia.gov.br/api-de-dados/{ceis,cnep,cepim}?codigoSancionado={cnpj}` | (chave) |

**Sementes locais já disponíveis:**
- `Outras Fontes/entidades-tce-mg.csv` — 12.525 entidades MG **com CNPJ e URL** (modelo da cascata + sites MG).
- `Contatos Jira.csv` — emails por setor (sistema municipal específico; uso pontual).

---

## 3. Modelo de dados (cascata)

```
ufs[UF] = { nome, municipios }
  municipios[codigoIbge] = { nome, uf, orgaos }
    orgaos[cnpj] = {
      razaoSocial, nomeFantasia, poder (L/E/J), esfera (M/E/F/D),
      naturezaJuridica, statusAtivo,
      rfb: { email, telefone, situacao, logradouro, bairro, cep, enteResponsavel },
      site,                              # enriquecido
      infoComplementar,
      unidades[codigoUnidade] = { nome, municipioIbge },   # setores
      fontePNCP: { publicou:true, primeiraPublicacao, ultimaPublicacao, nModalidades }
    }
```
Saídas: **JSON aninhado** (para o painel em cascata) + **CSV achatado** (1 linha = órgão) + tabela
Supabase `cadastro_institucional_br` (grão = órgão) e `cadastro_institucional_br_unidades` (grão = unidade).

---

## 4. Integração no painel (index.html) e Supabase
- Novo card **Painel 2N** com navegação em árvore UF → Município → Órgão → Setores, e ficha do órgão
  (CNPJ, natureza, contato, site, sanções). Filtros por UF/esfera/poder. Export CSV/Excel.
- Mesmo padrão dos painéis atuais: dados em Supabase (REST) + `data_full/*.json` para carga estática.
- Retroalimentação: job semanal varre novas publicações PNCP e faz upsert por CNPJ (idempotente),
  no mesmo molde do `retroalimentar_p8.py`.

## 5. Enriquecimento cruzado dos painéis existentes
- **P2 (MG)**: casar CNPJ do PNCP com `entidades-tce-mg.csv` → validar/gerar URL e natureza.
- **P3/P4 (fornecedores/contratos)**: PNCP já é fonte; ligar contrato→órgão→cascata nacional.
- **P6 (responsáveis)**: responsáveis por processo saem das atas/contratos PNCP (por órgão).
- **P9 (RFB)**: o cache de enriquecimento CNPJ alimenta as consultas ao vivo.

## 6. Escala e custo
- Publicadores PNCP distintos estimados: **~15k–40k CNPJs** (5.570 municípios × prefeitura+câmara+autarquias).
- Varredura PNCP: milhares de páginas (10.176 registros em 3 dias só na modalidade 8) → job em lote/background.
- Enriquecimento RFB: 1 request/CNPJ, throttle → horas para o país inteiro. **Rodar em background, resumível.**

_Fonte da análise: sondagem ao vivo das APIs PNCP, Compras.gov.br e minhareceita em 2026-07-05._
