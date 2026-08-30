# Diretório oficial de órgãos e entidades do Governo do Estado do Paraná + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl + Jina Reader). Somente páginas públicas; todo contato tem URL de origem.

Arquivos (JSON Lines, UTF-8):
- `~/.claude/jobs/diretorios-uf/PR/orgaos.jsonl` — 87 órgãos/entidades
- `~/.claude/jobs/diretorios-uf/PR/apis.jsonl` — 23 portais/APIs testados (20 "200 ok"; 2 domínios legados com DNS morto; Compras Paraná 403)
- Trabalho em `~/.claude/jobs/diretorios-uf/PR/_trabalho/` (agentes_ouv/transp.json, extras.json, crawl_in/out.json). Nada no Google Drive.

## 1. Fontes-mãe
- **https://www.cge.pr.gov.br/Pagina/Agentes-de-Transparencia** — 69 órgãos com agente de transparência/e-SIC: nome, telefone, **e-mail**, endereço, horário e site.
- **https://www.cge.pr.gov.br/Pagina/Agentes-de-Ouvidoria** — 70 órgãos com agente de ouvidoria: nome, telefone, endereço, horário e site.
- **https://www.parana.pr.gov.br/Pagina/Orgaos-e-Entidades** — links dos Poderes e da Estrutura Organizacional no PTE (transparencia.pr.gov.br /pte/assunto/6/18).
- Sites oficiais (padrão www.<tema>.pr.gov.br) de 86 órgãos rastreados pelo crawler (home + contato/ouvidoria).

## 2. Cobertura — 87 órgãos/entidades
Site 87 · E-mail 82 · Telefone 85 · Endereço 83 · Ouvidoria URL 75 · Nome do agente (ouvidoria) 74 · Dados abertos/transparência 76 · Redes sociais 67.
CNPJs da lista-alvo: **79 de 81 casados**. Fora de escopo: "EMP TESTE 5" (cadastro de teste no PNCP) e "Assembleia Legislativa de Rondônia" (linha de outra UF na lista). Anexações com nota: FUNSAUDE→SESA, FUNREFISCO→SEFA, FEPGE→PGE, Fundo Combate à Corrupção→CGE, FEMA→SEDEST, Fundo Penitenciário→DEPPEN, FAASP=FUNDASEG, SEIMT→SEIA, SEJUF→SEJU, Sec. Comunicação Social e Cultura (antiga)→SEEC, Desenvolvimento Urbano (antiga)→SECID, campi UNIOESTE agrupados. CNPJ 76416940000128 "ESTADO DO PARANA" casa com o registro do Governo/portal; unidades compradoras herdam contatos dos órgãos-pai.

## 3. Catálogo de APIs (23)
- **MUDANÇA IMPORTANTE**: `dadosabertos.pr.gov.br` e `transparencia.download.pr.gov.br` (fonte antiga do ZIP de remuneração) **não resolvem mais no DNS**. O portal de dados abertos atual é **www.dados.pr.gov.br** (IPARDES+Celepar; não é CKAN — /api/3 dá 404; acesso via BDEweb/IPARDES, catálogo em PDF).
- **PTE — Portal da Transparência** (transparencia.pr.gov.br/pte): JBoss/JSF com jsessionid; páginas por assunto (/pte/assunto/<a>/<b>) e por órgão (/pte/orgao=<SIGLA>); Estrutura Organizacional em /pte/assunto/6/18.
- **TCE-PR**: Dados Abertos municipais em pit.tce.pr.gov.br/Dados/DadosConsulta/Consulta (arquivos por município/ano: licitações, contratos, despesas, relacionamentos) + transparência própria.
- Poderes: ALEP (transparencia.assembleia.pr.leg.br + consultas.assembleia.pr.leg.br), TJPR /transparencia, MPPR /transparencia, DPE-PR /Transparencia.
- Outros: DIOE (diário oficial), legislacao.pr.gov.br, PIA (serviços digitais), Consulta Escolas (SEED), IPARDES, Celepar. Compras Paraná: WAF 403; GMS exige login Identidade Digital.

## 4. Faltas/limitações
- e-SIC como URL dedicada é raro (o acesso à informação é centralizado no PIA/eProtocolo); campo esic_url baixo (9).
- BDEweb do IPARDES não respondeu na coleta (bdeweb.ipardes.pr.gov.br); retestar.
- Compras/GMS sem consulta anônima ampla — rota alternativa: PNCP e TCE-PR.
