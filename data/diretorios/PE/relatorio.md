# Diretório oficial de órgãos e entidades do Governo de Pernambuco + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl + Jina Reader). Somente páginas públicas; nenhum e-mail/telefone inventado - todo contato tem URL de origem (`fonte_url`/`fontes`).

Arquivos gerados (JSON Lines):
- `~/.claude/jobs/diretorios-uf/PE/orgaos.jsonl` - 93 linhas
- `~/.claude/jobs/diretorios-uf/PE/apis.jsonl` - 44 APIs/portais testados com 1 GET real
- `~/.claude/jobs/diretorios-uf/PE/relatorio.md` - este relatório
- Área de trabalho: `~/.claude/jobs/diretorios-uf/PE/_trabalho/`

## 1. Fontes-mãe (diretórios oficiais)

1. **Portal de Serviços PE - "Secretarias e Órgãos"**: https://www.pe.gov.br/app/catalog/secretarias-e-orgaos (SPA React). A lista vem da API aberta `https://www.pe.gov.br/v1/department` (72 órgãos: id, slug, name, shortName, link). O detalhe (`/v1/department/<id>`) exige Bearer token (401) e a página exibe "Não informado" para endereço/telefone - ou seja, o diretório oficial **não publica contatos**, só nome/sigla/link.
2. **Rede de Ouvidorias e SIC do Poder Executivo** (Ouvidoria-Geral do Estado/SCGE): https://www.ouvidoria.pe.gov.br/?page_id=110 - 63 blocos (60 unidades) com **ouvidor, endereço, horário, telefones, e-mail e site** de secretarias, autarquias, empresas, fundações, hospitais (HAM, HBL, HR, HGV, HOF, HRA, HUOC, PROCAPE, CISAM) e OGE. Foi a principal fonte de contatos. A página também informa quais órgãos não têm ouvidoria própria e são atendidos pela OGE (SAESPRI, LAFEPE, GABGOV, SEPE, Casa Civil, Casa Militar, SCGE, VICEGOV, EPC).
3. Sites oficiais de cada órgão (home + contato/ouvidoria) e dos Poderes (ALEPE, TJPE, TCE-PE + Escola de Contas, MPPE, DPE-PE). Portal da Transparência (https://transparencia.pe.gov.br/) e Portal da LAI (https://www.lai.pe.gov.br/) como referências transversais; Ouve.PE (https://ouve.pe.gov.br/) como ouvidoria única.

## 2. Cobertura - órgãos (93 linhas)

| Campo | Linhas com dado |
|---|---|
| Ouvidoria (URL) | 93 (100%) - própria, rede de ouvidorias ou Ouve.PE |
| Site | 85 (91%) |
| E-mail | 78 (84%) - 245 e-mails, todos com URL de origem |
| Telefone | 76 (82%) - 527 números |
| Endereço | 70 (75%) |
| Ouvidor/responsável | 65 |
| Fale conosco (URL) | 47 |
| Redes sociais | 44 |
| Casadas com CNPJ da lista-alvo (`cnpjs_pncp`) | 69 linhas -> **134 dos 134 CNPJs** de `alvos_PE.csv` |

Rendimento por tipo (linhas / com e-mail / com telefone / com site / com endereço):
- secretaria 28 / 23 / 22 / 24 / 22 (sem e-mail: Casa Civil, Casa Militar, SEPE, SEHAB, Vice-Governadoria - atendidas pela OGE)
- empresa 16 / 14 / 14 / 15 / 11 (Compesa, Copergás, CEPE, CEHAB, EPTI, LAFEPE, Perpart, Porto do Recife, Suape, ADEPE, AGE, CTM, Prorural, Porto Digital, EPC)
- autarquia 15 / 13 / 13 / 14 / 12 (Detran-PE bloqueia robôs - contatos vieram da rede de ouvidorias)
- fundação 6 / 5 / 6 / 6 / 5 (FACEPE só telefone)
- outro 24 / 20 / 17 / 22 / 16 (hospitais da SES/UPE, OGE, PM, PC, CBM, Polícia Científica, PGE, Noronha, Procon, Gabinete, CEDCA, APEVISA, CNPJ raiz do Estado)
- poderes: ALEPE (alepe@ e ouvidoria@alepe.pe.gov.br), TCE-PE (atendimento@/ouvidoria@tcepe.tc.br + Escola de Contas), MPPE (ouvidoria@mppe.mp.br), DPE-PE (17 e-mails setoriais), TJPE (só telefone (81) 3182-0100 e formulário da ouvidoria)

Cobertura das **1.676 unidades compradoras** da lista-alvo: 1.623 (97%) estão sob um CNPJ cuja linha tem e-mail ou telefone; 1.535 (92%) com e-mail. As 373 unidades do CNPJ raiz "Estado de Pernambuco" (secretarias, PM, universidades...) foram associadas à linha GOVPE com o contato da Ouvidoria-Geral (162 / 0800 281 2900 / ouvidoria@ouvidoria.pe.gov.br); as 14 filiais da UPE, 15 da SES (hospitais/GERES) e 9 da SEFAZ herdam o contato da matriz. A "17ª Vara Federal Petrolina" na lista é federal (ignorada).

## 3. APIs e portais (44 linhas em apis.jsonl)

Status dos testes: 42 "200 ok", 1 "bloqueado" (Detran-PE, Akamai 403 inclusive via Jina), 1 "erro" (BDE/CONDEPE timeout).

Destaques:
- **API do diretório oficial** `https://www.pe.gov.br/v1/department` e `/v1/category` - JSON aberto.
- **dados.pe.gov.br (CKAN 2.x)** - API completa sem chave: package_search (43 conjuntos), organization_list (8 organizações: SES 13, SCGE 10, SEFAZ 9, SEPLAG 6, SAD 5), package_show testado para remuneração de servidores (922 recursos JSON/CSV mensais desde 2012), despesas gerais, contratos/licitações PE-Integrado, obras públicas, OSS da saúde (milhares de CSV), emendas. DataStore inativo (404) - baixar por `resources[].url` (testado 200).
- **TCE-PE - API Dados Abertos** https://sistemas.tce.pe.gov.br/DadosAbertos/ - 72 métodos REST no padrão `<Metodo>!<json|xml|csv>?filtros` (receitas/despesas estaduais e municipais, fornecedores, sanções, contratos, convênios, licitações, obras, processos/decisões, ListaServidores, UnidadesJurisdicionadas, Remessa). Testados: TipoCredorEstadual, UnidadesJurisdicionadas, Sancoes, Contratos (44 MB sem filtro de UG), ListaServidores - todos 200.
- **ALEPE Dados Abertos** https://dadosabertos.alepe.pe.gov.br/api/v1/ (parlamentares, cargos, contratos, licitacoes, lotacoes, remuneracao, servidores) - JSON 200.
- **MPPE** - CKAN em dados.mppe.mp.br (5 conjuntos) + transparencia.mppe.mp.br.
- Portal da Transparência (WordPress + painéis; `wp-json` aberto), Rede de Ouvidorias (HTML com contatos), Ouve.PE, LAI, PE-Integrado (licitações), e-Fisco/SEFAZ, Diário Oficial (CEPE, SPA), SDS estatísticas criminais, APAC monitoramento, TJPE transparência (sem API própria), HubBI (login).
- WordPress REST aberto: SCGE, UPE, transparencia.pe.gov.br (SES bloqueia wp-json com 403).

## 4. O que não foi encontrado / limitações
- Sem site próprio ou fora do ar: Casa Civil (manutenção), Casa Militar, Vice-Governadoria, SEPE, SEHAB, SCJ, SESP, AGEFEPE, ITERPE (503), CEHAB (404), EPC ("em desenvolvimento"), SECULT ("temporariamente indisponível"), Copergás (não respondeu), SDA/agricultura.pe.gov.br ("em manutenção").
- Bloqueios a robôs: Detran-PE (Akamai), Compesa e Suape (JS; Jina lê a Compesa), Noronha/Hemope/UPE (proteção parcial - curl direto funcionou).
- TJPE não publica e-mail de contato (só telefone e formulário); FACEPE, IASSEPE/IRH, SEMOBI, SEPLAG, CIENT (Polícia Científica) só telefones nos sites; e-mails de ouvidoria vieram da rede de ouvidorias quando existentes.
- Endereços dos Poderes foram preenchidos a partir do site institucional (não extraídos automaticamente) - conferir antes de uso postal.
