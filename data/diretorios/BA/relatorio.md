# Diretório oficial de órgãos e entidades do Governo do Estado da Bahia + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl + Jina Reader). Somente páginas públicas; todo contato tem URL de origem (`fontes_emails`, `fontes_telefones`, `fontes_endereco`, `ouvidoria_fonte`).

Arquivos (JSON Lines, UTF-8):
- `~/.claude/jobs/diretorios-uf/BA/orgaos.jsonl` — 102 órgãos/entidades (Executivo direto/indireto, hospitais/ouvidorias especializadas + ALBA, TCE-BA, TCM-BA, TJBA, MPBA, DPE-BA)
- `~/.claude/jobs/diretorios-uf/BA/apis.jsonl` — 36 APIs/portais testados com 1 GET real (34 "200 ok"; TCM portaltcm-api 500 na raiz; e-TCM rest 404 na raiz)
- Trabalho intermediário em `~/.claude/jobs/diretorios-uf/BA/_trabalho/` (rede_ouv_nodes/contatos.json, crawl_in/out.json, apis_ba.py). Nada no Google Drive.

## 1. Fontes-mãe
- **https://www.ba.gov.br/ouvidoria/8/rede-de-ouvidorias** (Ouvidoria Geral do Estado, Drupal 10; atualizada 17/07/2026) — 93 páginas-nó, uma por órgão/entidade, com nome do(a) ouvidor(a) titular/adjunto, telefone, e-mail, horário e endereço (inclui hospitais estaduais, maternidades, policlínicas, núcleos regionais de saúde e ouvidorias dos Poderes TJ/TCE/TCM/TRE/ALBA/DPE/MP).
- **https://www.transparencia.ba.gov.br/EstruturaOrganizacional** → **https://perfiladministracaopublica.ba.gov.br/** (Perfil da Administração Pública/SAEB): diretório oficial com organograma e fichas por categoria (secretarias, órgãos subordinados ao governador, regime especial, autarquias, fundações públicas/privadas, empresas, sociedades de economia mista, colegiados); conteúdo das fichas carregado por JS (não raspado ficha a ficha).
- **www.ba.gov.br/<slug>** — portal unificado Drupal: os antigos domínios www.<sigla>.ba.gov.br redirecionam (ex.: saeb→/administracao, sec→/educacao, sesab→/saude); home + /contato|/ouvidoria de ~74 subsites lidos.
- **https://dados.ba.gov.br** — CKAN (21 conjuntos, 3 organizações) para catálogo de APIs.
- Sites próprios remanescentes: sefaz.ba.gov.br, bahiagas.com.br, embasa.ba.gov.br, desenbahia.ba.gov.br, cbpm.ba.gov.br, tca.ba.gov.br, universidades (uneb.br, uefs.br, uesb.br, uesc.br) e Poderes.

## 2. Cobertura — 102 órgãos/entidades
| Campo | Qtde |
|---|---|
| Site | 90 |
| E-mail (≥1) | 71 |
| Telefone | 93 |
| Endereço | 81 |
| Ouvidoria (URL) | 52 |
| Ouvidoria (e-mail dedicado) | 64 |
| Nome do(a) ouvidor(a) | 84 |
| Fale conosco (URL) | 52 |
| e-SIC (URL) | 48 |
| Dados abertos/transparência (URLs) | 51 |
| Redes sociais | 54 |
| CNPJs da lista-alvo casados | 84 de 84 (67 registros com CNPJ) |

Todos os 84 CNPJs de `alvos_BA.csv` foram casados (12 por override manual: SSP, FAPESB, FPC, SEINFRA, UESB/Autarquia Universidade do Sudoeste, Planserv/Fundo de Custeio, AGERBA, FERFA→SEMA, FEAS→SEADES, FERHBA→INEMA, Vice-Governadoria, Central de Licitações→SAEB). O CNPJ 13937032000160 "ESTADO DA BAHIA" (2.878 unidades compradoras — secretarias, hospitais, escolas, delegacias) casa com o registro "Gabinete do Governador"; contato do órgão-pai vale para as unidades (`alvos_BA_unidades.csv`).

## 3. Catálogo de APIs (36 entradas)
- **CKAN dados.ba.gov.br**: 21 conjuntos (SEFAZ 18 — despesas, receitas, pagamentos, contratos, licitações, diárias, obras, NF-e de compras, emendas, convênios, dados de servidores, terceirizados, bens imóveis, repasses a municípios; SESAB 2 — covid; SSP 1 — mortes violentas). CSVs diretos em resources[].url.
- **Portal da Transparência BA** (ASP.NET MVC, iso-8859-1): 11 painéis (servidores/remuneração, empenhos, pagamentos, receita, dívida ativa, convênios, contratos, obras, licitações, emendas, segurança pública).
- **Perfil da Administração Pública** (diretório oficial) + organograma.
- **TCE-BA**: transparência via BI Mirante (tcebiprdl) com export CSV; /dados-abertos com erro 500.
- **TCM-BA**: SPA portaltcm com backends REST não documentados (portaltcm-api, conteudopost-api, ouvidoria-api, scr-api 401, barbosa-api); e-TCM (prestação de contas municipais); WP REST ok.
- **ALBA** transparência + licita.alba.ba.gov.br; **TJBA** transparência (+/portal/api/); **MPBA** portaltransparencia; **DPE-BA** em portal.io.org.br.
- Outros: TAG Ouvidoria (consulta aberta), Legislabahia, Diário Oficial DOOL/EGBA, Comprasnet.BA (editais/RP/fornecedores), SEI (Bahia Análise de Dados), GeoBahia e Sala de Situação (INEMA), SEFAZ finanças públicas.

## 4. Faltas/limitações
- Fichas do Perfil da Administração carregam por JS (sem endpoint JSON visível no HTML); usar como referência estrutural.
- SEAP, SEMA, JUCEB, AGERSA, SDR, SEADES e alguns outros: rede de ouvidorias sem e-mail publicado (só telefone/endereço) — não inventamos e-mail.
- Sites que não abriram: geobahia https (usar http), alguns subsites ba.gov.br/<sigla> com slug diferente (vice-governadoria, svponte etc. sem página própria).
- Hospitais/maternidades/policlínicas foram mantidos como registros agregados (contatos das ouvidorias especializadas da SESAB).
