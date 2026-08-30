# Diretório oficial de órgãos e entidades - Ceará (CE) + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl com UA de navegador + fallback Jina Reader). Somente páginas públicas; nenhum e-mail/telefone inventado - todo contato tem URL de origem (`fontes_emails`, `fontes_telefones`, `fonte_url`). Esfera: estadual.

Arquivos gerados (JSON Lines, append):
- `~/.claude/jobs/diretorios-uf/CE/orgaos.jsonl` - 82 linhas (73 do diretório oficial + 5 Poderes/órgãos autônomos + Vice-Governadoria + FUNSAUDE + FDID + 1 linha do CNPJ raiz do ente)
- `~/.claude/jobs/diretorios-uf/CE/apis.jsonl` - 25 APIs/portais catalogados, cada um testado com 1 GET real (campo `http`)
- `~/.claude/jobs/diretorios-uf/CE/relatorio.md` - este relatório
- Área de trabalho (HTML baixado, crawl, scripts): `~/.claude/jobs/diretorios-uf/CE/_trabalho/`

## 1. Fontes (diretórios oficiais)

- **https://cearatransparente.ce.gov.br/portal-da-transparencia/paginas/enderecos-e-telefones** - "Endereços e telefones" do Ceará Transparente (CGE), atualizado 19/05/2026: 73 órgãos e entidades do Poder Executivo com titular, endereço, telefone, horário, **ouvidor responsável + telefone + e-mail**, **responsável pelo SIC + telefone + e-mail** e site. É a fonte-mãe (única página do Ceará Transparente que respondeu ao curl; as demais rotas caem em desafio JS anti-bot - ver §3).
- https://www.ce.gov.br/o-governo/organograma-estadual/ - Organograma Estadual (Lei 16.710/2018): lista os 43 órgãos da Administração Direta (usada para classificar `tipo`); as listas de autarquias/fundações/empresas são carregadas por AJAX (`admin-ajax.php?action=filter_orgaos_by_setor`) que o WAF F5 rejeita fora do navegador ("The requested URL was rejected") - classificação de autarquia/fundação/empresa feita por nome/sigla.
- https://www.ce.gov.br/wp-json/cegovbr/v1/sites - lista dos 113 subsites WordPress dos órgãos (secretarias, hospitais, CREDEs).
- Sites de cada órgão (home + páginas de contato/ouvidoria/fale-conosco) - a maioria migrou para `www.ce.gov.br/<sigla>/` (multisite); os antigos `www.<sigla>.ce.gov.br` redirecionam.
- Poderes: TJCE (tjce.jus.br/contato, /ouvidoria), ALECE (al.ce.gov.br, transparencia.al.ce.gov.br, canalalece), TCE-CE (ouvidoria/contate-a-ouvidoria, SIC), MPCE (institucional/contatos, telefones-uteis, ouvidoria-geral), DPGE (informacoes-ao-cidadao/ouvidoria).

Método: (1) leitura e parsing do diretório oficial; (2) crawl do site de cada órgão (home + até 5 páginas candidatas de contato/ouvidoria, 8 threads); (3) descoberta e teste das APIs; (4) casamento com `alvos_CE.csv` por tabela sigla→CNPJ (manual, 100% revisada) + nome.

## 2. Cobertura - órgãos (82 linhas)

| Campo | Linhas com dado |
|---|---|
| E-mail | 78 (95%) - 419 e-mails no total, todos com URL de origem |
| Telefone | 78 (95%) - 499 números |
| Site | 79 (96%) |
| Endereço | 72 (87%) |
| Responsável/titular | 73 (89%) |
| Ouvidor nomeado + e-mail da ouvidoria | 73 |
| Responsável SIC + e-mail | 66 |
| Ouvidoria (URL) | 82 (100%) |
| Fale conosco (URL) | 43 (52%) |
| Redes sociais | 70 (85%) |
| Casados com CNPJ da lista-alvo (`cnpjs_pncp`) | 64 linhas cobrindo 80 dos 80 CNPJs de `alvos_CE.csv` (100%) |

Por tipo (contrato): {'outro': 17, 'autarquia': 12, 'empresa': 11, 'fundacao': 9, 'secretaria': 28, 'tribunal': 1, 'legislativo': 1, 'tce': 1, 'mp': 1, 'fundo': 1}. O campo extra `categoria_diretorio` guarda a seção (Administração Direta, Autarquias, Fundações, Empresas, Poderes).

Rendimento por tipo (total / com e-mail / com telefone / com ouvidoria):
- outro: 17 / 15 / 16 / 17
- autarquia: 12 / 12 / 12 / 12
- empresa: 11 / 11 / 11 / 11
- fundacao: 9 / 8 / 8 / 9
- secretaria: 28 / 28 / 27 / 28
- tribunal: 1 / 1 / 1 / 1
- legislativo: 1 / 1 / 1 / 1
- tce: 1 / 1 / 1 / 1
- mp: 1 / 1 / 1 / 1
- fundo: 1 / 0 / 0 / 1

Órgãos com mais e-mails publicados: Polícia Civil (75); Academia Estadual de Segurança Pública do Cea (47); Secretaria do Esporte (39); Agência de Desenvolvimento do Estado do Ceará (24); Fundação Cearense de Apoio ao Desenvolvimento (24); Fundação de Previdência Social do Estado do C (15); Fundação de Teleducação do Ceará (13); Instituto do Desenvolvimento Agrário do Ceará (8).

Observações sobre os contatos:
- Os e-mails do diretório oficial são em grande parte **nominais** (ouvidor e responsável pelo SIC: `nome.sobrenome@orgao.ce.gov.br`), além de caixas institucionais (`ouvidoria@aesp.ce.gov.br`, `ouvidoria@adagri.ce.gov.br`, `csai@adece.ce.gov.br`, `ouvidor@arce.ce.gov.br`...). Campos `emails_ouvidoria`, `emails_sic`, `ouvidor`, `sic_responsavel` preservam o papel.
- Sites no multisite ce.gov.br quase nunca publicam e-mail; o telefone da home é o geral e a ouvidoria remete ao Ceará Transparente (canal único: 155 / plataforma).
- Poderes: TJCE (ouvidoriageral@tjce.jus.br, (85) 3207-7000), TCE-CE (ouvidoria@tce.ce.gov.br, 0800 079 6660), ALECE (ouvidoria@al.ce.gov.br, (85) 3277.2500), MPCE (só telefones em "telefones úteis" + mediacaocomunitaria@; Ouvidoria por formulário), DPGE (transparencia@defensoria.ce.def.br, (85) 3194-5000).
- Não casados/limitações: FUNSAUDE (site HTTP 410, fundação absorvida pela SESA), FDID (fundo sem site; vinculado ao PROCON/SPS por inferência), Secretaria da Pesca e Aquicultura (sem site no diretório; só telefone do diretório), SEM/SEPA (sites recém-criados, sem e-mail). O CNPJ raiz "ESTADO DO CEARA" (1.910 unidades PNCP: escolas EEEP/EEF/EEMTI, CREDEs, hospitais, CRES) foi registrado numa linha própria - as unidades devem ser roteadas pelo órgão-pai (SEDUC/SESA).

## 3. APIs e portais de dados (25 linhas em apis.jsonl)

Status dos testes (1 GET cada): {'200 ok': 21, 'erro': 2, 'bloqueado': 2}.

Principais achados:
- **API de Dados Abertos Ceará Transparente** (`api-dados-abertos.cearatransparente.ce.gov.br`, Swagger em /api-docs, spec /api-docs/v1/swagger.yaml): sem autenticação; `/transparencia/contratos/contratos` (622 mil contratos, 100/pág, filtros por data de assinatura, detalhe por isn_sic) e `/transparencia/contratos/convenios` (35 mil) respondem 200; `/transparencia/servidores/salarios` devolve **HTTP 500** em todas as combinações (documentado mas quebrado).
- **Ceará Transparente (portal)**: home e páginas estáticas (/paginas/*) abrem com curl; **todas as rotas de consulta** (despesas, receitas, servidores, terceirizados, conjuntos-de-dados, estrutura-organizacional, canais-atendimento) devolvem um desafio JavaScript anti-bot de ~252 KB e o Jina Reader falha ("Unexpected empty file") - consistente com bloqueio a IP/robô fora do BR. Registrado como `bloqueado`; rota alternativa: navegador real ou e-SIC.
- **TCE-CE - API de Dados Abertos do SIM 2.0** (`api-dados-abertos.tce.ce.gov.br/sim`, OpenAPI em /openapi_prod.yaml, Denodo): 60+ rotas GET sem autenticação cobrindo orçamento, balancetes, contratos, licitantes, obras/medições, agentes públicos, diárias, parcerias OSC e transferências **dos municípios cearenses** (não do Estado); paginação `$start_index/$count`, `$format=json|xml`. O backend legado `api.tce.ce.gov.br` (usado pelo portal municipios-transparencia) está com erro 500 de proxy/SSL.
- **ALECE - API Portal da Transparência** (`transparencia.al.ce.gov.br/api`, OpenAPI 3 em /docs?api-docs.json): /api/contratos, /api/licitacoes, /api/termos-credenciamento - JSON, 20 registros por requisição, sem chave.
- **SESA - IntegraSUS API** (`integrasus.saude.ce.gov.br/api/`): HATEOAS aberta (municípios, macrorregiões, unidades, atendimentos ambulatório/emergência, grupos, formas de organização).
- **FUNCEME API** (`api.funceme.br`): REST/RPC; `/rest/acude/volume` aberto (2,4 mi registros paginados); `/rest/pcd/dados-recentes` exige token (401). Portal Hidrológico (`hidro.ce.gov.br/downloads`) publica arquivos de açudes/chuvas/barragens.
- Outros: IPECE Data (JSF, sem API), SSPDS estatísticas (XLSX/PDF mensais), portal ce.gov.br (WP REST com lista de 113 subsites), TJCE dados abertos (remete ao DataJud), MPCE transparência (HTML), TCE Transparência Ativa (WP REST).

## 4. Não encontrado / limitações
- Nenhum CKAN estadual (dados.ce.gov.br não resolve); o catálogo "conjuntos de dados" do Ceará Transparente só é acessível via navegador.
- Organograma: categorias de autarquias/fundações/empresas não obtidas (WAF); e-mails de autarquias/empresas vêm do diretório (ouvidoria/SIC) e das páginas de contato dos sites.
- Não foram visitadas as ~1.900 unidades compradoras sob o CNPJ raiz (escolas, hospitais) - fora do escopo de 15 min; os subsites `ce.gov.br/crede01-seduc ... crede20-seduc`, hospitais (hgf, hsm, hm, hias, hsj, hmjma, hgcc) e `samu`, `lacen`, `hemoce` constam em `wp-json/cegovbr/v1/sites` e podem ser crawleados depois com o mesmo script.
