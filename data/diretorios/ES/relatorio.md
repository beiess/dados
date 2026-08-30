# Diretório oficial de órgãos e entidades - Espírito Santo (ES) + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl com UA de navegador + fallback Jina Reader). Somente páginas públicas; nenhum e-mail/telefone inventado - todo contato tem URL de origem (`fontes_emails`, `fontes_telefones`, `fonte_url`). Esfera: estadual.

Arquivos gerados (JSON Lines, append):
- `~/.claude/jobs/diretorios-uf/ES/orgaos.jsonl` - 78 linhas (77 órgãos/entidades + 1 linha do CNPJ raiz do ente)
- `~/.claude/jobs/diretorios-uf/ES/apis.jsonl` - 32 APIs/portais catalogados, cada um testado com 1 GET real (campos `http`, `bytes`, `content_type`)
- `~/.claude/jobs/diretorios-uf/ES/relatorio.md` - este relatório
- Área de trabalho (HTML baixado, crawl, scripts): `~/.claude/jobs/diretorios-uf/ES/_trabalho/`

## 1. Fontes (diretórios oficiais)

- https://www.es.gov.br/estrutura-organizacional - "Estrutura Organizacional" do portal oficial, com organograma PDF (https://www.es.gov.br/media/Arquivos/ORGANOGRAMA%20ES%202025.pdf)
- https://www.es.gov.br/secretarias - 26 secretarias/órgãos centrais; cada página /secretarias/<sigla> publica titular, telefone(s), e-mail(s), endereço, horário e site
- https://www.es.gov.br/autarquias-e-orgaos - 27 autarquias/órgãos (páginas /autarquias-e-orgaos/<sigla> + /procon-es)
- https://www.es.gov.br/empresas-publicas - 5 empresas (BANDES, BANESTES, CEASA, CESAN, CETURB)
- Sites *.es.gov.br de cada órgão (home + contato/fale-conosco/ouvidoria/contatos)
- Complementos: ALES (al.es.gov.br/Administracao/Contatos), TCE-ES (tcees.tc.br), TJES, MPES (transparencia.mpes.mp.br), DPES, Dados ES (dados.es.gov.br - CKAN), Portal da Transparência (transparencia.es.gov.br)

Método: (1) leitura do diretório oficial e extração estruturada; (2) para cada órgão, visita ao site oficial (home) e às páginas candidatas de contato/ouvidoria (links com "ouvidoria", "fale conosco", "contato", "atendimento" + caminhos padrão), com 2ª passada em /contatos, /fale-com-a-secretaria, /fale-com-a-ra, /fale-conosco, /contato, /ouvidoria; (3) descoberta e teste das APIs/portais de dados; (4) casamento com `alvos_ES.csv` por nome/sigla + tabela manual de sucessores/fundos.

## 2. Cobertura - órgãos (78 linhas)

| Campo | Linhas com dado |
|---|---|
| Site | 75 (96%) (site respondeu HTTP 200: 73) |
| E-mail | 72 (92%) - 1777 e-mails no total, todos com URL de origem |
| Telefone | 77 (99%) - 1062 números |
| Endereço | 57 (73%) |
| Responsável/titular | 56 (72%) |
| Ouvidoria (URL) | 69 (88%) |
| Fale conosco (URL) | 57 (73%) |
| Redes sociais | 53 (68%) |
| Casados com CNPJ da lista-alvo (`cnpjs_pncp`) | 63 (81%) - cobrem 123 dos 128 CNPJs de `alvos_ES.csv` |

Por tipo (contrato): {'outro': 19, 'secretaria': 24, 'empresa': 7, 'autarquia': 22, 'fundacao': 2, 'legislativo': 1, 'tce': 1, 'tribunal': 1, 'mp': 1}. O campo extra `categoria_diretorio` guarda a seção original do diretório.

Rendimento por tipo (com e-mail / com telefone / com ouvidoria):
- secretaria (24): com e-mail 24 / com telefone 24 / com ouvidoria 24
- autarquia (22): com e-mail 21 / com telefone 22 / com ouvidoria 21
- outro (19): com e-mail 15 / com telefone 18 / com ouvidoria 15
- empresa (7): com e-mail 7 / com telefone 7 / com ouvidoria 6
- fundacao (2): com e-mail 2 / com telefone 2 / com ouvidoria 2
- legislativo (1): com e-mail 1 / com telefone 1 / com ouvidoria 0
- tce (1): com e-mail 0 / com telefone 1 / com ouvidoria 0
- tribunal (1): com e-mail 1 / com telefone 1 / com ouvidoria 1
- mp (1): com e-mail 1 / com telefone 1 / com ouvidoria 0

Órgãos com mais e-mails publicados: IDAF - Instituto de Defesa Agropecuária e Flo (120); INCAPER - Instituto Capixaba de Pesquisa, Ass (120); ALES - Assembleia Legislativa do Estado do Es (120); DER – Departamento de Edificações e de Rodovi (107); IOPES - Instituto de Obras Públicas do ES (ex (107); SEGER - Secretaria de Gestão e Recursos Human (74); CBMES - Corpo de Bombeiros Militar do Espírit (72); SEAG - Secretaria da Agricultura, Abastecimen (66)

## 3. APIs e portais de dados (32 linhas em apis.jsonl)

Status dos testes (1 GET cada): {'200 ok': 30, 'erro': 1, 'bloqueado': 1}.

Principais achados:
- **Dados ES (dados.es.gov.br)** é CKAN completo, sem chave: 509 conjuntos em 43 organizações; `package_search` com `fq=organization:<slug>` (200) e **DataStore ativo** (`datastore_search` 200) - permite consulta por recurso sem baixar CSV. Maiores publicadores: SESP 43 (criminalidade), PCES 38, IJSN 37, SEDU 32, SEJUS 28, TCEES 28, PGE 27, CBMES 18, IDAF/SEAG 17, SEDES/SETUR 16, SETADES 14, SEP 11, Detran/Incaper/SEAMA 10.
- **Portal da Transparência ES** (SECONT, ASP.NET) publica suas bases no Dados ES (datasets `portal-da-transparencia-*`, ex.: pessoal) - a rota estruturada é o CKAN.
- **TCE-ES**: 28 conjuntos no Dados ES (responsáveis com contas irregulares, inabilitados, proibidos de contratar, empresas inidôneas, servidores, licitações, contratos, obras); Painel de Controle é SPA sem endpoint documentado.
- **ALES**: seção "Dados Abertos" com rotas `/DadosAbertos/{Acoes,Agenda,CotasParlamentares,DespesaPorFavorecido,ContratosAditivos...}` (HTML/grid, sem export JSON detectado); página de contatos com 200+ e-mails setoriais.
- **MPES**: `dadosabertos.mpes.mp.br` com Swagger em `/api-docs` (200) e portal de transparência; DPES tem portal próprio.
- **Geobases/IJSN**: GeoNode com **GeoServer WFS/WMS aberto** em `ide.geobases.es.gov.br/geoserver` (GetCapabilities 771 KB, camadas `geonode:*`).
- CESAN bloqueia curl (403 - WAF); demais empresas (Banestes, Bandes, Ceturb, Ceasa) só páginas HTML.

## 4. Não casados com a lista-alvo e limitações

- Companhia Docas do Espírito Santo (CODESA - federal/privatizada) e Conselho Regional de Educação Física (autarquia federal) não são entes estaduais.
- Fundos estaduais (36 CNPJs de 1-2 unidades) foram casados à secretaria gestora pelo nome (FES -> SESA, FEAS/FET -> SETADES, Fundo de Cultura -> SECULT, FUNPEN/rotativo -> SEJUS, FUNDEMA -> SEAMA, FUNDÁGUA -> AGERH, FEHIS -> SEDURB, fundos de reequipamento -> PC/PM/CBM, FADEPES -> DPES, FUNEPJ -> TJES, Fundo do MPES -> MPES, Fundo Previdenciário -> IPAJM, Fundo Dívida Ativa -> PGE, FUNCITEC -> SECTI, FEAC/PEDRS -> SEAG, Fundo de Combate à Corrupção -> SECONT, FIA -> SEDH, Fundo de Turismo -> SETUR, Fundo Fazendário -> SEFAZ, SUPPIN -> SEDES). Três ficaram sem casamento por não haver gestor inequívoco: FUNCOP (combate à pobreza), Fundo sobre Drogas e FUMDEVIT (metropolitano).
- "ESTADO DO ESPIRITO SANTO" (27080530000143, 311 unidades + 4 filiais) é o CNPJ-guarda-chuva das unidades compradoras; linha "Estado do Espírito Santo (CNPJ raiz)" registra endereço/telefone do Palácio.
- 18 filiais da SESA (27080605xxxx: hospitais e superintendências regionais) e 4 filiais do IESP herdam o contato da SESA/IESP; o diretório não publica contato por unidade hospitalar.
- Sites que não responderam: direitoshumanos.es.gov.br (SEDH usa sedh.es.gov.br), hemoes/lacen/crefes/iesp (.saude.es.gov.br e .es.gov.br não resolvem - unidades da SESA), policiapenal.es.gov.br; cesan.com.br devolve 403 (WAF). Cerimonial e Chefia de Gabinete do Governador não têm site próprio (contato só no diretório).

CNPJs-alvo sem casamento (5): 27316538000166 COMPANHIA DOCAS DO ESPIRITO SANTO; 49846393000148 CONSELHO REGIONAL DE EDUCAÇAO FISICA/ES; 15833032000145 FUNDO ESTADUAL DE COMBATE E ERRADICACAO DA POBREZA; 20604213000130 FUNDO ESTADUAL SOBRE DROGAS; 20354589000133 FUNDO METROPOLITANO DE DESENVOLVIMENTO DA GRANDE V

Órgãos sem e-mail nem telefone publicados em texto (só formulário web / site fora do ar): nenhum.

## 5. Próximos passos sugeridos

- Carregar `orgaos.jsonl` na tabela de cadastro institucional (só-nulos, idempotente) usando `cnpjs_pncp` como chave e `fontes_*` como proveniência.
- Unidades compradoras do PNCP (hospitais, RAs, fundos) herdam o contato do órgão-pai desta base; contatos por unidade hospitalar exigem LAI/e-SIC.
- Agendar coleta incremental das APIs abertas (ver `apis.jsonl`, status "200 ok") no framework de ingestão.
