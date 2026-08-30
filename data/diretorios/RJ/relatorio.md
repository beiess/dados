# Diretório oficial de órgãos e entidades do Governo do Estado do Rio de Janeiro + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl + Jina Reader). Somente páginas públicas; nenhum e-mail/telefone inventado — todo contato tem URL de origem (`fontes_emails`, `fontes_telefones`, `fontes_endereco`, `ouvidoria_fonte`).

Arquivos (JSON Lines, UTF-8):
- `~/.claude/jobs/diretorios-uf/RJ/orgaos.jsonl` — 107 órgãos/entidades (Executivo direto e indireto + ALERJ, TCE-RJ, TJRJ, EMERJ, MPRJ, DPRJ, PGE)
- `~/.claude/jobs/diretorios-uf/RJ/apis.jsonl` — 75 APIs/portais de dados testados com 1 GET real (70 "200 ok", 4 bloqueados por token, 1 erro)
- Trabalho intermediário em `~/.claude/jobs/diretorios-uf/RJ/_trabalho/` (estrutura_links.json, cge_contatos.json/xlsx, crawl_in/out.json, apis_rj.py). Nada gravado no Google Drive.

## 1. Fontes-mãe (diretórios oficiais)
- **https://www.transparencia.rj.gov.br/transparencia/estrutura-poder-executivo/** (Portal da Transparência/CGE) — "Estrutura do Poder Executivo" (Decreto 46.544/2019 e alterações até ago/2026): 31 órgãos da administração direta (Governadoria, Vice, SECC, SEGOV, SEPLAG, SEFAZ, SEDES, SEPM, SEPOL, SEPPENRJ, SEDEC, SES, SEEDUC, SETRAM, SEAS, SEAPPADI, SECEC, SEDSODH, SEEL, SETUR, CGE, GSI, SETRAB, SERGB, SETD, SEIOP, SEHIS, SEMPI, SECID, SEDCON, SESP, PGE) com link do site oficial, decretos de estrutura, órgãos colegiados, fundos e entidades vinculadas (~55 autarquias/fundações/empresas com site). Não traz e-mail/telefone.
- **https://cge.rj.gov.br/unidades-setorial-de-ouvidoria-uos/** (CGE — Rede de Ouvidorias e Transparência) → planilha oficial `Contatos_Rede_de_Ouvidorias_e_Transparencia___Agosto_2026.xlsx` (atualizada 14/08/2026): 84 Unidades de Ouvidoria Setoriais (31 direta + 53 indireta) com telefone, e-mail, endereço, horário e nome do(a) ouvidor(a); abas extras com sigla e vinculação (Cartas de Serviços).
- **https://www.rj.gov.br** — SPA React; backend `admin.rj.gov.br/api/cms/*` e `ouvidoria.rj.gov.br/api/*` exigem token (401). Os subsites Drupal `www.rj.gov.br/<orgao>` (planejamento, seas, secid, isp, ceperj, degase…) são legíveis e foram usados para contatos.
- **https://dadosabertos.rj.gov.br** — CKAN 2.10.1 (1.111 conjuntos, ~50 organizações) usado para o catálogo de APIs e `dados_abertos_urls`.
- Sites oficiais de cada órgão (home + até 6 páginas: ouvidoria, contato, fale-conosco, acesso à informação, institucional) — 104 sites lidos, 101 com HTTP 200 (UEZO 403; PMERJ e CASERJ sem resposta).

## 2. Cobertura — 107 órgãos/entidades
| Campo | Qtde |
|---|---|
| Site | 104 |
| E-mail institucional (≥1) | 95 |
| Telefone | 86 |
| Endereço | 92 |
| Ouvidoria (URL) | 66 |
| Ouvidoria (e-mail dedicado, planilha CGE) | 80 |
| Nome do(a) ouvidor(a) | 77 |
| Horário de atendimento da ouvidoria | 77 |
| Fale conosco (URL) | 69 |
| e-SIC / acesso à informação (URL) | 41 |
| Dados abertos / transparência (URLs) | 87 |
| Redes sociais | 83 |
| Casados com CNPJ da lista-alvo PNCP | 72 registros → 85 dos 87 CNPJs |

Tipos: 37 secretarias/órgãos centrais, 20 autarquias, 18 fundações, 15 empresas, 4 fundos, TCE, TJ+EMERJ, ALERJ, MP, 8 outros (conselhos, comissões, DPRJ).

Casamento com a lista-alvo (`alvos_RJ.csv`, 87 CNPJs): 85 casados. Não casados: SENAC-AR/RJ (Sistema S, não é órgão estadual) e Indústrias Nucleares do Brasil (empresa federal). O CNPJ 42498600000171 "ESTADO DO RIO DE JANEIRO" (615 unidades compradoras: secretarias, hospitais, DER, PM, fundos…) foi anexado ao registro "Governadoria do Estado"; os contatos de cada órgão-pai valem para as unidades. Fundos sem site próprio foram anexados ao órgão gestor (FEAS→SEDSODH, FEFOSP→SESP, Fundo Adm. Fazendária→SEFAZ, FDM→IRM, Subsecretaria Militar→GSI, SEDIPAF→SEAPPADI, SEAP→SEPPENRJ), com nota em `observacoes`.

Ruído removido: telefones e endereço do rodapé padrão dos subsites Drupal rj.gov.br (2276-6556 / 2332-8611 / 2334-7910 e "Alameda São Boaventura, 770") que aparecem em ≥4 sites foram descartados; e-mails pessoais (gmail/hotmail) foram registrados só em `observacoes` como "não institucional".

## 3. Catálogo de APIs (75 entradas)
- **CKAN estadual** (`dadosabertos.rj.gov.br/api/3/action/...`): package_search, organization_list, facetas, group_list + 20 consultas por organização (SECC 287, SEPLAG 54, RIOPREV 48, AGETRANSP 46, IEEA 36, SEEL 34, RJPREV 28, EMOP 27, DRM 26, SEFAZ 26, CEPERJ 24, FIPERJ 24, SEDEC 24, SETRAM 22, CGE 19…). Formatos: PDF 338, JSON 289, CSV 208, XLSX 171.
- **TCE-RJ Dados Abertos** (`dados.tcerj.tc.br/api/v1`, OpenAPI em /api/v1/openapi.json, docs em /api/v1/docs): 41 rotas REST JSON sem chave (estado: contratos, compras diretas/covid, convênios, receitas, empenho, dotação, situação funcional, obras paralisadas, penalidades; municípios: licitações, licitantes, gastos com pessoal, despesas/indicadores de saúde e educação, receitas, concessões; próprio TCE: terceirizados, cargos, estagiários, diárias, obras, duodécimo). 7 rotas testadas, todas 200 (respostas grandes: `limit` não é respeitado).
- **Portal da Transparência RJ** (WordPress): páginas temáticas + WP REST `/wp-json/wp/v2/pages`; RH via painel Qlik SUBGEP e consulta rj.gov.br/remuneracao.
- **ISPDados** (Instituto de Segurança Pública): ~20 CSVs abertos (BaseDPEvolucaoMensalCisp, BaseMunicipioMensal, séries históricas, feminicídio, armas…).
- **OuveRJ** (`ouvidoria.rj.gov.br/api`): raiz pública lista rotas; assuntos/orgaos/esic-transparencia exigem token (401). CMS do portal (`admin.rj.gov.br/api/cms/*`) idem.
- Poderes: TJRJ (dados abertos Res. CNJ 215, xlsx), MPRJ (transparencia.mprj.mp.br), DPRJ (Transparência/Verde em Dados), ALERJ (Transparência ASP.NET com cookie obrigatório; legislação Lotus Notes).
- Outros: SIGA compras.rj.gov.br (busca de editais), SEFAZ transparência, SES TabNet, SEEDUC Google Sites, IOERJ (D.O.), INEA dados abertos/GeoINEA, CEPERJ, UERJ.

## 4. O que não foi encontrado / limitações
- Não há página oficial com e-mail/telefone GERAL de cada secretaria (o diretório do Executivo só publica ouvidorias); e-mails de gabinete vieram dos sites (rodapé/contato).
- SEEDUC, SEFAZ, DEGASE, FMIS, IOERJ, EMERJ, IPALERJ, SEENEMAR, SECTI, SEVIT: site sem e-mail/telefone no HTML (SPA ou só formulário); a ouvidoria da planilha CGE cobre SEEDUC/SEFAZ/DEGASE/FMIS/IOERJ.
- PMERJ (www.pmerj.rj.gov.br) e CASERJ não responderam; UEZO devolve 403 (mantidos com contatos da planilha CGE quando existentes).
- APIs do OuveRJ e do CMS rj.gov.br exigem token — registradas como "bloqueado"; rota alternativa: e-SIC (www.rj.gov.br/esic).
- Não há DataStore CKAN testado (recursos são arquivos hospedados).
