# Diretório oficial de órgãos e entidades - Roraima (RR) + catálogo de APIs

Data da coleta: 2026-08-30. curl (UA navegador) + fallback Jina; só páginas públicas; contatos com URL de origem. Esfera: estadual.

Arquivos:
- `~/.claude/jobs/diretorios-uf/RR/orgaos.jsonl` - 57 linhas
- `~/.claude/jobs/diretorios-uf/RR/apis.jsonl` - 12 APIs/portais testados
- Área de trabalho: `~/.claude/jobs/diretorios-uf/RR/_trabalho/`

## 1. Fontes
- **API do Portal da Transparência RR**: `GET https://api.transparencia.rr.gov.br/api/v1/portal/orgaos` - diretório oficial de 49 órgãos do Executivo com endereço, telefone(s), e-mail, site e horário de atendimento (é a fonte da página "Horários de Atendimento" do SPA). Estrutura/organograma (PDF mensal) via `/estruturaorganizacional`.
- portal.rr.gov.br estava com erro 500 durante a coleta (o SPA da transparência funcionou normalmente).
- Crawl dos 49 sites dos órgãos + TJRR, ALE-RR, TCE-RR, MPRR, MPC-RR, DPE-RR (contatos/ouvidoria).

## 2. Cobertura (57 linhas)
| Campo | Linhas |
|---|---|
| Site | 55 |
| E-mail | 50 (116 e-mails) |
| Telefone | 54 (264 números) |
| Endereço | 49 |
| Ouvidoria | 28 |
| Fale conosco | 18 |
| Redes sociais | 18 |
| Com CNPJ-alvo | 45 - 52/53 CNPJs (exceção: CRECI-RR, conselho profissional federal, fora do escopo estadual) |

Tipos: {'autarquia': 12, 'empresa': 5, 'outro': 14, 'fundacao': 3, 'secretaria': 18, 'tribunal': 1, 'legislativo': 1, 'tce': 1, 'mp': 2}. Fundos mapeados ao gestor (FUNDEPRO->PGE; FMTCE->TCE; FUNSEFAZ->SEFAZ; FREA->PM; FREBOM->CBM; FUNDATER->IATER; FESP->SESP; FUNPER->SEJUC). DER-RR marcado extinto na própria fonte (e-mail placeholder "foi@extinto.rr" descartado).
Sem e-mail publicado: Departamento de Estradas de Rodagem, TJRR, TCE-RR, MPC-RR, UNIVIRR, IACTI-RR, VICE-GOV.

## 3. APIs (12) - status {'200 ok': 11, 'erro': 1}
- **api.transparencia.rr.gov.br/api/v1/portal**: REST JSON sem chave - `orgaos` (diretório com contatos), `estruturaorganizacional`, `curriculos`, `legislacao` (498 KB), `menus`. Endpoints de despesas/receitas do SPA não expostos por GET simples nesses caminhos (404) - o SPA usa outras rotas internas.
- TCE-RR (tcerr.tc.br + transparencia.tcerr.tc.br SPA), MPRR (transparencia.mprr.mp.br), TJRR (transparencia.tjrr.jus.br), ALE-RR (SAPL API REST 200), Imprensa Oficial (imprensaoficial.rr.gov.br), SEFAZ-RR.
- Sem CKAN estadual localizado (dados.rr.gov.br não existe).

## 4. Faltas
- IACTI e Vice-Governadoria: sem site/contato publicado localizado.
- compras.rr.gov.br fora do ar no teste.
- TCE-RR não publica e-mail em texto na home/contato (só telefones).
