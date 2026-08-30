# Diretório oficial de órgãos e entidades - Rio Grande do Norte (RN) + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl + fallback Jina Reader). Somente páginas públicas; todo contato tem URL de origem.

Arquivos:
- `RN/orgaos.jsonl` - 61 linhas (45 do diretório oficial + Poderes + 10 complementos + CNPJ raiz)
- `RN/apis.jsonl` - 10 APIs/portais testados
- Área de trabalho: `RN/_trabalho/`

## 1. Fontes
- **https://www.transparencia.rn.gov.br/orgaos-do-governo** - "Órgãos do Governo (Cartas de Serviços)" do Portal da Transparência (CONTROL): 45 órgãos com titular, telefones, website, e-mail, horário e endereço - diretório-mãe.
- Sites dos órgãos (crawl de 45 sites): **maioria atrás de WAF** - 503 ao curl (SECULT, PROCON, PGE, IDEMA, EMATER, DETRAN, ARSEP, JUCERN, PMRN, IGARN, SAPE) ou só via Jina (SEAD, CONTROL, SIN, SETUR, SEPLAN, SEMJIDH, SEMARH, SEDRAF, SEDEC, FAPERN); mesmo assim SEFAZ (22 e-mails setoriais), FJA (60), CEASA (19), PCRN e Poderes renderam contatos extras.
- Poderes: ALRN (ouvidoriageral@al.rn.leg.br, protocolo@), TCE-RN (37 e-mails setoriais/49 tels na página de contatos), MPRN (ouvidoria@mprn.mp.br...), DPE-RN (defensoriapublica@dpe.rn.def.br); **TJRN 403 até no Jina** - único Poder sem contato coletado.

## 2. Cobertura (61 linhas)
- Com e-mail: 41 (163 e-mails) | Com telefone: 48 (125 números)
- Com site: 56 | Com endereço: 46 | Com titular: 45
- Tipos: {'outro': 12, 'secretaria': 18, 'autarquia': 14, 'empresa': 8, 'fundacao': 5, 'tribunal': 1, 'legislativo': 1, 'tce': 1, 'mp': 1}
- CNPJs-alvo casados: 68 de 69 - o único não casado é o CNPJ do DER de MATO GROSSO DO SUL (03983939001779) que veio na lista-alvo RN por erro de UF no PNCP.

## 3. APIs
- **TCE-RN API Dados Abertos (SIAI)**: apidadosabertos.tce.rn.gov.br - Swagger 2.0 em /swagger/docs/v1, 11 rotas GET (jurisdicionados+CNPJ, balanço orçamentário, licitações/dispensas, empenhos/liquidações/pagamentos, contratos) em json|csv|html, sem chave. Teste 200 (jurisdicionados).
- **API Remuneração RN** (api.remuneracao.rn.gov.br): /ExportarPorOrgao e /ExportarPorNome, sem chave, parâmetros obrigatórios (id, ano, mes).
- **CKAN dados.rn.gov.br**: no ar porém **vazio** (0 datasets, 20 organizações).
- API SIPAC Transparência (api.sipac.rn.gov.br): 503 na coleta.
- Portal da Transparência (HTML), e-SIC (sic.rn.gov.br), Fala.BR p/ ouvidoria; ALRN Transparência Legislativa (DataTables); TJRN bloqueado (403).

## 4. Faltas/limitações
- TJRN sem contatos (WAF). SEJUC e SEEL sem site localizado. SET/EMATER/SECULT com site fora do ar (503/timeout) - contatos só do diretório quando existentes.
- Muitos e-mails oficiais do RN são caixas Gmail institucionais (governodorn@gmail.com, gabseplan@gmail.com, rnsetur@gmail.com...) - registrados como publicados no diretório oficial.
