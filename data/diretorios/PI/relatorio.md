# Diretório de órgãos e entidades - Piauí (PI) + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl UA-navegador + fallback Jina Reader). Somente páginas públicas; nenhum contato inventado - cada e-mail/telefone tem URL de origem (`fontes_emails`/`fontes_telefones`).

Arquivos:
- `~/.claude/jobs/diretorios-uf/PI/orgaos.jsonl` - 45 linhas (44 órgãos + 1 linha do CNPJ raiz)
- `~/.claude/jobs/diretorios-uf/PI/apis.jsonl` - 17 APIs/portais testados
- Área de trabalho: `~/.claude/jobs/diretorios-uf/PI/_trabalho/`

## 1. Contexto crítico da coleta
O portal www.pi.gov.br está em **modo "Período Eleitoral"** (Decreto Estadual 24.400/2026 + Lei 9.504/1997 art. 73 VI b): o diretório "Buscar Órgãos" exibe apenas logos, sem contatos, e **dados.pi.gov.br está suspenso** ("Serviço Temporariamente Indisponível...", contato gabinete@seplan.pi.gov.br). O Portal da Transparência (transparencia.pi.gov.br) é SPA e **não tem página de estrutura organizacional com contatos**. Resultado: o diretório foi reconstruído órgão a órgão pelos sites www.<sigla>.pi.gov.br (55 sites tentados em 2 rodadas de crawl).

## 2. Fontes
- Sites oficiais dos órgãos (www.<sigla>.pi.gov.br, home + contato/ouvidoria) - 44 tentados, 33 responderam
- https://www.pi.gov.br/central-de-servicos-links-e-telefones/ - central de serviços (endereço do Palácio de Karnak, Ouvidoria-Geral 162 / (86) 3326-2001 / atendimento@ouvidoriageral.pi.gov.br)
- Poderes: TJPI (portaltjpi + ouvidoria), ALEPI (al.pi.leg.br + transparencia + SAPL), TCE-PI (tcepi.tc.br + ouvidoria), MPPI (contatos-mppi + telefones-uteis + ouvidoria), DPE-PI (contatos-atendimento, fale-conosco)
- e-OUV Piauí (eouv.pi.gov.br) = canal único de ouvidoria/e-SIC do Executivo

## 3. Cobertura - órgãos (45 linhas)
- Com e-mail: 26 (143 e-mails; SEDUC sozinha publica 100 - inclui as 21 GREs)
- Com telefone: 32
- Com site: 45 (responderam 200: 38)
- Com URL de ouvidoria: 45
- CNPJs-alvo casados: 47 de 71 (66%)
- Tipos: {'secretaria': 16, 'outro': 8, 'autarquia': 11, 'empresa': 2, 'fundacao': 4, 'tribunal': 1, 'legislativo': 1, 'tce': 1, 'mp': 1}

Limitações de contato: muitos órgãos do PI publicam como e-mail apenas o da Ouvidoria-Geral central (atendimento@ouvidoriageral.pi.gov.br); SEADPREV/SASC/IASPI/DETRAN/ADH/UESPI/SEMARH/SESAPI não publicam e-mail no site. Sites fora do ar na coleta (DNS/timeout): ATI, AGESPISA, CBMEPI, AGRESPI, SDR, FUNDESPI, SETRANS, + 9 candidatos da 2ª rodada (cidades, sde, ccom, sia, mulheres, esporte, fepiserh, semper, sada, juventude). CNPJs não casados (24): órgãos sem site localizável no tempo disponível (coordenadorias, secretarias novas - Defesa Civil OK; Transportes/SETRANS fora do ar; Cidades, Mineração, Desenvolvimento Econômico, Esportes, Mulheres, Relações Sociais, Inteligência Artificial, FEPISERH, TV/Rádio, fundos etc.) - rota alternativa: e-OUV/LAI após o período eleitoral.

## 4. APIs (17 linhas)
- **API Transparência PI** (api.transparencia.pi.gov.br, OpenAPI 3 v1.3.132 em /docs/ + /schema/): 162 rotas/26 grupos (admissões, contratos, fiscais, licitações, obras, receitas/despesas/diárias/servidores V2, emendas, dívida ativa, sanções, ordem cronológica...), sem chave; testes 200 em contratos/receitas/licitações/obras/despesas-v2. Downloads CSV pelos endpoints /download/.
- **TCE-PI - API Portal da Cidadania** (sistemas.tce.pi.gov.br/api/portaldacidadania, apidoc em /docs/): /prefeituras (224 municípios com URLs de prefeitura/câmara), /orgaos/lista/{exercicio}, despesas/receitas/licitações/servidores/credores por unidade gestora (variantes /estado/). Testes 200.
- dados.pi.gov.br: **suspenso** (eleitoral). dados-abertos.etipi.pi.gov.br responde um "Dashboard de Logs" (não é portal público).
- ALEPI: SAPL 503 no /api/ (portal HTML ok); transparencia.al.pi.leg.br HTML.
- TJPI: transparencia.tjpi.jus.br HTML (processual = DataJud/CNJ). MPPI: transparencia.mppi.mp.br HTML.

## 5. Pendências
- Reprocessar após o período eleitoral: dados.pi.gov.br, diretório "Buscar Órgãos" do pi.gov.br, SAPL /api/.
- Sites fora do ar listados acima; contatos dos 26 CNPJs não casados via e-OUV/LAI.
