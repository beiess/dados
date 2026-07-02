# Catálogo de Fontes & Retroalimentação — Painel Estratégico (TCE-MG / MG)

> **Norma do projeto:** todo dado e toda atualização são **documentados** aqui, de modo que a base
> **se retroalimente a partir das fontes identificadas** — nunca editar dado à mão; sempre re-rodar o
> script de refresh a partir da origem. Aplica as regras do `CLAUDE.md` (proveniência obrigatória,
> chaves canônicas, papel A3 curador-fontes, só fontes oficiais abertas, CPF mascarado na exposição).

## Campos de proveniência (obrigatórios por dataset)
`fonte` · `fonte_url` · `fonte_tipo` · `data_coleta` · `grau_confianca` (A–F) · `chaves_canonicas`
· `cadencia` (com que frequência a fonte publica) · `refresh` (comando/script) · `armadilhas`.

**Grau de confiança:** A=identificador oficial completo (CNPJ/PNCP/id) · B=registro oficial sem CPF
· C=cruzamento por nome/CPF-mascarado (homônimo possível) · D=proxy/derivado · E/F=incerto.

**Onde ficam os scripts:** raiz do projeto canônico `TCEMG/tools/` (coleta/consolidação) e
`beiess/dados` → `tools/` (carga Supabase + estado MG). Carga padrão: `tools/load_supabase.py`.

---

## Painel 1 — Servidores municipais (folha SICOM, 853 municípios)
| campo | valor |
|---|---|
| fonte | Folha de remuneração SICOM/TCE-MG (remessas `remuneracao-municipio`, `pessoa-orgao`) + enriquecimento |
| fonte_url | SICOM (arquivos das remessas municipais, consolidado local); enriquecimento: Portal da Transparência/CGU `dadosabertos-download.cgu.gov.br` (CEIS/CNEP/CEAF), TSE `cdn.tse.jus.br` (cand. 2024), Receita Federal QSA `arquivos.receitafederal.gov.br` (WebDAV) |
| fonte_tipo | CSV/ZIP de remessa (SICOM) + CDN de dados abertos |
| data_coleta | 2026-07-01 (consolidado exec. 2024/2025) |
| grau_confianca | **B** (folha oficial) / **C** (enriquecimento por CPF-mascarado+nome — sanção/mandato/sócio) |
| chaves_canonicas | `cpf` (interno, mascarado na exposição) + `matricula`+`cod_orgao`; `cod_ibge` |
| cadencia | Remuneração mensal; enriquecimentos anuais (TSE) / periódicos (CEIS/QSA) |
| refresh | `tools/folha_mg.py` (baixa 853, trava de disco) → `extrair_setor_remuneracao`/`extrair_responsabilidade` → `build_painel_mg` → enriquecer por CPF (`exports/enriquecimento/*`) → `load_supabase.py painel1 <csv>` |
| armadilhas | 1.355.103 linhas; DELETE em massa dá timeout → limpar em lotes de 50k. Só fonte oficial (recusado dado pessoal privado). |

## Painel 2 — Cadastro Institucional (entes/órgãos MG)
| campo | valor |
|---|---|
| fonte | Cadastro institucional PNTP / dados abertos MG (PJ de MG) + enriquecimento de links oficiais |
| fonte_url | Dados abertos MG (aba `Cadastro_Institucional`); ver [[cadastro-institucional-pntp]] |
| fonte_tipo | XLSX/CSV |
| data_coleta | 2026-06-24 |
| grau_confianca | **B** |
| chaves_canonicas | `cnpj` (14) / `cnpj_raiz` (8); `cod_ibge` |
| cadencia | Esporádica (cadastro) |
| refresh | consolidação → `load_supabase.py cadastro <csv>` |
| armadilhas | Base pode ficar 0 linhas no Supabase se não recarregada; app tolera (join só enriquece). |

## Painel 3 — Fornecedores de obra/engenharia
| campo | valor |
|---|---|
| fonte | SICOM licitação (homolog. `dsc_nat_objeto=OBRAS…`) + empenho por natureza `4.4.x.51`; cadastro via BrasilAPI |
| fonte_url | SICOM (consolidado) + `brasilapi.com.br` (CNPJ) |
| fonte_tipo | CSV SICOM + API REST |
| data_coleta | 2026-06-25 |
| grau_confianca | **B** (fornecedor PJ por CNPJ) |
| chaves_canonicas | `cnpj` |
| cadencia | Anual (execução) |
| refresh | `tools/fornecedores_obra.py` + `fornecedores_empenho.py` → `forn_cadastro.py` (BrasilAPI, resumível, backoff 429) → `load_supabase.py` |
| armadilhas | `valor_empenho_obra` tem escala suspeita (qualidade pré-existente). Empenho sem histórico livre. |

## Painel 4 — Contratos 2026
| campo | valor |
|---|---|
| fonte | TCE-MG ReportViewer, relatório UC30 (Contratos) |
| fonte_url | `reportviewer.tce.mg.gov.br/default.aspx` (wrapper; ReportServer não é público) |
| fonte_tipo | Relatório ASPX → export CSV |
| data_coleta | 2026-06-26 |
| grau_confianca | **B** (objeto/valores) / doc do contratado 0% preenchido → cruzamento com P3 por **nome** (C) |
| chaves_canonicas | `cod_ibge` (=IBGE), `num_contrato`+`num_processo` |
| cadencia | Contínua (2026) |
| refresh | `tools/contratos_tce.py` (varre 853; GET viewstate → POST "Exibir" → ExportUrlBase+CSV; `verify=False`; `decode utf-8-sig`) → `load_supabase.py` |
| armadilhas | Encoding UTF-8 **com BOM** (latin1 → mojibake). Municípios com 0 contratos não entram em "feitos". Objeto vem em `Textbox6`. |

## Painel 5 — Estrutura / Despesa 2026 (QDD/LOA)
| campo | valor |
|---|---|
| fonte | TCE-MG ReportViewer, relatório UC05 (Árvore — SICOM Consulta IP) |
| fonte_url | `reportviewer.tce.mg.gov.br` (param `municipioSelecionado=IBGE`, `exercicioSelecionado=2026`) |
| fonte_tipo | Relatório ASPX → export CSV |
| data_coleta | 2026-06-28 |
| grau_confianca | **B** (valor/estrutura) / `seq_orgao`,`seq_unidade` derivados (A após registro oficial de órgãos) |
| chaves_canonicas | `cod_ibge`; `cod_orgao`/`cod_unidade` → `seq_orgao`/`seq_unidade` (convenção FATO) |
| cadencia | Anual (LOA) |
| refresh | `tools/estrutura_tce.py` (4 workers, retries, `.done`) → `load_supabase.py estrutura <csv>`; seq derivado no app via `orgaos.json` (registro oficial SICOM Órgão) |
| armadilhas | Σ por município bate a LOA. seq depende de `orgaos.json` v4 (módulo Órgão do SICOM). |

## Painel 6 — Responsáveis (licitação + órgão)
| campo | valor |
|---|---|
| fonte | SICOM `licitacao.{respLicitacao,respDispensa,comissaoLicitacao,parecLicitacao}` + módulo Órgão `orgao.orgaoResp` |
| fonte_url | SICOM consolidado + `D:/OneDrive/…/SICOM/Orgão` (orgao.orgao, orgaoUnidade, orgaoResp) |
| fonte_tipo | CSV SICOM |
| data_coleta | 2026-07-01 |
| grau_confianca | **B** (registro oficial) / cruzamento com P1 por CPF-mascarado+nome (**C**) |
| chaves_canonicas | `cod_ibge`, `seq_orgao` (elo resp→município); `cpf` (completo quando casa no P1) |
| cadencia | Por exercício (licitação) |
| refresh | `tools/build_painel6.py` (env P6_SICOM/P6_P1/P6_EST/P6_ORG/P6_ORGRESP; modo ALL) → `load_supabase.py responsaveis <csv>` |
| armadilhas | 94.827 resp, 853/853 munic. Fiscais de contrato **indisponíveis** nas fontes atuais (módulo AM-Contratos não baixado). `no_painel1` 3 estados quando P1 não cobre o munic. |

## Painel 8 — Servidores do Estado de MG (2026)
| campo | valor |
|---|---|
| fonte | SEPLAG/MG — "Relação Nominal dos Servidores do Poder Executivo" |
| fonte_url | `dados.mg.gov.br` (CKAN), dataset `31bd2c27-b64f-447b-95db-83d221874951`; API `…/api/3/action/package_show?id=<dataset>` |
| fonte_tipo | CKAN → CSV mensal (`dados_serv_AAAAMM.csv`) |
| data_coleta | 2026-07-02 (meses 202601–202605) |
| grau_confianca | **B** (masp/nome/cargo/lotação/situação; sem CPF, sem remuneração) / `no_painel1` por nome (**C**) |
| chaves_canonicas | `masp` (matrícula) — 1 pessoa/masp; sem CPF na fonte |
| cadencia | **Mensal** (retroalimentar: puxar cada novo mês publicado) |
| refresh | `tools/baixa_servidores_estado.sh` (User-Agent + retry) → `tools/consolida_servidores_estado.py` (detecta encoding cp1252) → `load_supabase.py estado_2026 <consolidado.csv>`. Ver `DADOSMG/PROVENIENCIA.md`. |
| armadilhas | **403 sem User-Agent**; `datapackage.json` **cacheado** (usar API CKAN p/ meses novos); **encoding cp1252** (não utf-8); nomes repetidos = **homônimos** (não deduplicar por nome). |

---

## Fontes canônicas de referência (CLAUDE.md)
- **compras.gov.br** — `dadosabertos.compras.gov.br` (API REST, envelope paginado). Swagger em `/swagger-ui/index.html`.
- **Contratos.gov.br** — `contratos.comprasnet.gov.br` (OpenAPI `/docs/api-docs.json`).
- **dados.mg.gov.br** — CKAN Action API `/api/3/action/`.
- **TCE-MG** — `dadosabertos.tce.mg.gov.br` (SPA sobre API) + ReportViewer (UC05/UC30) + remessas SICOM.

## Como atualizar (retroalimentação)
1. Conferir se a fonte publicou novo período (ex.: CKAN `package_show`, novo mês SICOM/SEPLAG).
2. Rodar o `refresh` do painel (baixa da origem + reconstrói) — resumível, com retry, sem editar à mão.
3. Recarregar no Supabase (`load_supabase.py <alvo> <csv>`), em lotes.
4. **Atualizar este catálogo:** nova `data_coleta` + contagens; registrar qualquer nova armadilha.
5. Dado pessoal permanece mascarado na exposição; só fontes oficiais abertas.

> Próximo passo possível (opcional): automatizar 1–3 com agendamento (cron/rotina) por painel, mantendo
> este catálogo como fonte da verdade da proveniência.
