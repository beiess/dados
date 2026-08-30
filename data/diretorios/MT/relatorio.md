# Diretório de órgãos e entidades - Mato Grosso (MT) + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl + fallback Jina Reader). Só páginas públicas; todo contato tem URL de origem.

Arquivos: `MT/orgaos.jsonl` (46 linhas), `MT/apis.jsonl` (12), área de trabalho em `MT/_trabalho/`.

## 1. Fontes
- **Sites dos órgãos** (www.<sigla>.mt.gov.br) - 58 URLs em 2 rodadas de crawl; o diretório central do governo é o catálogo xvia https://portal.mt.gov.br/app/catalog/orgao (SPA sem API descoberta - backend devolve 500 "Api not found"), então o diretório foi montado órgão a órgão.
- **Achado-chave**: a página de contatos da SECOM (www.secom.mt.gov.br/contatos) publica um diretório de assessorias de comunicação de TODOS os órgãos - 217 e-mails e 185 telefones nominais capturados numa página só.
- Rendimentos altos também em: SETASC (66 e-mails), SEAF (47), CGE (42), SEMA (22), FAPEMAT (22), SES (16), SEJUS (10), SINFRA (9).
- Poderes: ALMT (ouvidoria@al.mt.gov.br, (65) 3313-6900), MPMT (ouvidoria@mpmt.mp.br + endereços/telefones por unidade na transparência), DPE-MT (via Jina), TJMT e TCE-MT são SPA - sem contato em HTML estático (falta).
- Ouvidoria central: ouvidoria.cge.mt.gov.br (Fale Cidadão); e-SIC: cge.mt.gov.br/acesso-a-informacao.

## 2. Cobertura (46 linhas)
- Com e-mail: 24 (477 e-mails) | Com telefone: 29 (421)
- Com site: 46 | Com ouvidoria própria/central: 46
- Tipos: {'secretaria': 16, 'outro': 8, 'autarquia': 8, 'empresa': 7, 'fundacao': 3, 'tribunal': 1, 'legislativo': 1, 'tce': 1, 'mp': 1}
- **CNPJs-alvo casados: 67 de 67 (100%)** - inclui as filiais 03507415* (ESTADO DE MATO GROSSO) na linha do ente raiz.

## 3. APIs
- **CKAN dadosabertos.mt.gov.br**: 26 datasets / 11 órgãos (testes 200).
- Dados MT (hub), GeoDados (ArcGIS), Anuário - 200.
- ALMT: API RESTful documentada mas com OAuth2 (401 sem credencial).
- TCE-MT: site SPA; dadosabertos.tce.mt.gov.br / api.tce.mt.gov.br / aplic.tce.mt.gov.br fora do ar na coleta - **falta** (retestar; APLIC é a fonte de contas).
- Sem contato coletado: SESP (só via Jina, sem e-mail), PMMT/CBMMT (SPA GovMT sem contatos estáticos), POLITEC/SEDUVI/CEASA/SECITECI (sites fora do ar), TJMT/TCE-MT (SPA).

## 4. Faltas
- E-mails de DETRAN, IPEM, MTPREV, SEFAZ, SEPLAG, SECEL (sites no ar mas sem e-mail publicado em HTML).
- TCE-MT/TJMT contatos e dados abertos; retestar fora do horário/via navegador.
