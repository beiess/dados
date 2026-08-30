# Diretório de órgãos e entidades - Sergipe (SE) + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl + fallback Jina Reader). Só páginas públicas; todo contato tem URL de origem.

Arquivos: `SE/orgaos.jsonl` (62 linhas), `SE/apis.jsonl` (14), área de trabalho `SE/_trabalho/`.

## 1. Fontes
- **https://www.se.gov.br/orgaos** (Next.js, ?page=1..6) + perfis **https://www.se.gov.br/agencia/<sigla>** - diretório oficial dos 54 órgãos do Executivo (fonte principal); crawl de 74 URLs (perfis + sites próprios + Poderes).
- **https://www.transparencia.se.gov.br/EstruturaOrganizacional** - Secretarias (20), Secretarias Especiais (6), Entidades (33) e página "Responsáveis" com link de gestores por órgão; rodapé publica contato da CGE (portaltransparenciasergipe@cge.se.gov.br, (79) 3179-4989/4928).
- Poderes: TJSE (ouvidoria@tjse.jus.br; site principal só via Jina), ALESE, TCE-SE (ouvidoria@ e presidencia@tce.se.gov.br, 0800-0754300), MPSE (ouvidoria@mpse.mp.br), DPE-SE (51 telefones + 3 e-mails institucionais).
- Ouvidoria/e-SIC central: www.ouvidoria.se.gov.br (0800 079 0162).

## 2. Cobertura (62 linhas)
- Com e-mail: 38 (121 e-mails) | Com telefone: 45 (169)
- Com site/perfil: 61 | Com ouvidoria: 62
- Tipos: {'autarquia': 8, 'empresa': 10, 'secretaria': 23, 'outro': 10, 'fundacao': 7, 'tribunal': 1, 'legislativo': 1, 'tce': 1, 'mp': 1}
- **CNPJs-alvo casados: 65 de 65 (100%)** (fundos vinculados às pastas gestoras; filiais 13128798* no ente raiz).
- Maiores rendimentos: ITPS (35 e-mails), CBM (18), EMGETIS (13), CODERSE (9), IOSE (5), DPE-SE (3 e-mails/51 tels).

## 3. APIs
- **API de Dados Abertos da Transparência SE** (api.v1.transparencia.se.gov.br; OpenAPI 3 em /openapi.json, Swagger em /docs): 6 rotas GET paginadas (órgãos/UGs, receita prevista, despesas consolidadas, diárias, folha de pagamento, health) - sem chave; testes 200.
- Portal da Transparência (Next server-side, curl-friendly); Observatório de Sergipe; painéis Power BI (SEFAZ); IOSE (diário).
- **TCE-SE/SAGRES**: sagres.tce.se.gov.br não resolve e /sagres-producao redireciona a SPA de protocolo - consulta pública não alcançada por curl (**falta**; retestar via navegador). Transparência TCE-SE em SharePoint OK.
- ALESE/MPSE/TJSE: portais HTML (sem API documentada).

## 4. Faltas/limitações
- Sites 302 (redirecionam a domínio próprio, alguns capturados na 2ª tentativa): FAPITEC, FHS, FSPH, PMSE, SEAGRI - perfil /agencia sem contato; e-mails ausentes p/ BANESE, CEHOP, DESO, DETRAN, FUNESA, PC, SES (só telefones).
- Defeso eleitoral em curso: portal sem cores e possíveis conteúdos suspensos.
