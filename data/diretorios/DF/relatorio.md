# Diretório oficial de órgãos e entidades - Distrito Federal (DF) + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl com UA de navegador + fallback Jina Reader). Somente páginas públicas; nenhum e-mail/telefone inventado - todo contato tem URL de origem (`fontes_emails`, `fontes_telefones`, `fonte_url`). Esfera: distrital.

Arquivos gerados (JSON Lines, append):
- `~/.claude/jobs/diretorios-uf/DF/orgaos.jsonl` - 118 linhas (117 órgãos/entidades + 1 linha do CNPJ raiz do ente)
- `~/.claude/jobs/diretorios-uf/DF/apis.jsonl` - 39 APIs/portais catalogados, cada um testado com 1 GET real (campos `http`, `bytes`, `content_type`)
- `~/.claude/jobs/diretorios-uf/DF/relatorio.md` - este relatório
- Área de trabalho (HTML baixado, crawl, scripts): `~/.claude/jobs/diretorios-uf/DF/_trabalho/`

## 1. Fontes (diretórios oficiais)

- https://www.df.gov.br/informacoes-orgaos - tabela oficial "Informações Órgãos" (70 linhas: 35 secretarias/casas/CGDF + 35 Administrações Regionais) com titular, telefone institucional, e-mail institucional, endereço e horário (atualizada 27/08/2026)
- https://www.df.gov.br/carta-de-servicos - tabela "Carta de Serviços" com tipo de órgão, nome e link (100 linhas: 35 RAs, 10 autarquias, 8 órgãos autônomos/especializados, 9 empresas públicas, 6 fundações, 31 secretarias) -> usada para obter o site oficial de cada entidade
- https://www.df.gov.br/organograma - organograma (imagem, sem dados extraíveis)
- Sites *.df.gov.br de cada órgão (home + /contatos, /fale-com-a-secretaria, /fale-com-a-ra, /fale-conosco, /contato, /ouvidoria) - padrão Liferay do GDF
- Complementos: TCDF (tc.df.gov.br + ouvidoria.tc.df.gov.br), CLDF (cl.df.gov.br + dados.cl.df.gov.br), TJDFT (tjdft.jus.br), MPDFT (mpdft.mp.br), Metrô-DF, Adasa, IgesDF, Ouvidoria-Geral (ouvidoria.df.gov.br), Portal de Dados Abertos (dados.df.gov.br)

Método: (1) leitura do diretório oficial e extração estruturada; (2) para cada órgão, visita ao site oficial (home) e às páginas candidatas de contato/ouvidoria (links com "ouvidoria", "fale conosco", "contato", "atendimento" + caminhos padrão), com 2ª passada em /contatos, /fale-com-a-secretaria, /fale-com-a-ra, /fale-conosco, /contato, /ouvidoria; (3) descoberta e teste das APIs/portais de dados; (4) casamento com `alvos_DF.csv` por nome/sigla + tabela manual de sucessores/fundos.

## 2. Cobertura - órgãos (118 linhas)

| Campo | Linhas com dado |
|---|---|
| Site | 108 (92%) (site respondeu HTTP 200: 104) |
| E-mail | 104 (88%) - 817 e-mails no total, todos com URL de origem |
| Telefone | 104 (88%) - 603 números |
| Endereço | 71 (60%) |
| Responsável/titular | 70 (59%) |
| Ouvidoria (URL) | 101 (86%) |
| Fale conosco (URL) | 90 (76%) |
| Redes sociais | 83 (70%) |
| Casados com CNPJ da lista-alvo (`cnpjs_pncp`) | 93 (79%) - cobrem 120 dos 130 CNPJs de `alvos_DF.csv` |

Por tipo (contrato): {'secretaria': 35, 'outro': 46, 'fundo': 2, 'autarquia': 14, 'empresa': 10, 'fundacao': 7, 'legislativo': 1, 'tce': 1, 'tribunal': 1, 'mp': 1}. O campo extra `categoria_diretorio` guarda a seção original do diretório.

Rendimento por tipo (com e-mail / com telefone / com ouvidoria):
- outro (46): com e-mail 41 / com telefone 41 / com ouvidoria 38
- secretaria (35): com e-mail 35 / com telefone 34 / com ouvidoria 30
- autarquia (14): com e-mail 11 / com telefone 10 / com ouvidoria 13
- empresa (10): com e-mail 6 / com telefone 8 / com ouvidoria 8
- fundacao (7): com e-mail 6 / com telefone 5 / com ouvidoria 6
- fundo (2): com e-mail 2 / com telefone 2 / com ouvidoria 2
- legislativo (1): com e-mail 1 / com telefone 1 / com ouvidoria 1
- tce (1): com e-mail 1 / com telefone 1 / com ouvidoria 1
- tribunal (1): com e-mail 1 / com telefone 1 / com ouvidoria 1
- mp (1): com e-mail 0 / com telefone 1 / com ouvidoria 1

Órgãos com mais e-mails publicados: Serviço de Limpeza Urbana (77); Secretaria de Estado de Transporte e Mobilida (59); Secretaria de Estado de Obras e Infraestrutur (45); Administração Regional de Arapoanga - RA XXXI (35); Secretaria de Estado de Desenvolvimento Urban (33); Secretaria de Estado de Cultura e Economia Cr (32); Administração Regional de Taguatinga - RA III (29); Secretaria de Estado de Desenvolvimento Socia (27)

## 3. APIs e portais de dados (39 linhas em apis.jsonl)

Status dos testes (1 GET cada): {'200 ok': 34, 'erro': 4, 'bloqueado': 1}.

Principais achados:
- **dados.df.gov.br** não é CKAN: é Liferay com API headless própria `/o/dados-abertos/v1.0` (OpenAPI em `/openapi.json`): `datasets` (179 conjuntos, paginado), `datasets/{id}` (+`/download`, `/resources/{id}`, `/dictionary`), `sources` (28 órgãos publicadores), `themes`, `stats`, `autocomplete` - tudo sem chave (200). Maiores publicadores: SEEC/Economia 30 (despesa, receita, servidores, remuneração, licitações), IPREV 13, Zoológico 12, Detran 11, CGDF 10, SLU 10, DER 9, Cidades 9.
- **Portal da Transparência DF** (SPA Angular): sem API pública; o único endpoint do bundle exige `x-client-id` e devolve 404; downloads via `novoportal.transparencia.df.gov.br/api/download/arquivos/<NOME>` (testado).
- **TJDFT** expõe APIs REST abertas: `rest-rh.tjdft.jus.br/api/transparencia/*` (estagiários, cedidos, TLP, matriz de cargos) e `sicomp.tjdft.jus.br/sicomp/api/csv/*` (contratos 1,4 MB, licitações, contratações diretas, penalidades...) - 200.
- **CLDF**: CKAN próprio `dados.cl.df.gov.br` (28 conjuntos) - 200.
- **TCDF**: e-Gesp (pessoal), Transparência Fiscal (painel SISCOEX), dados abertos de distribuição de processos (API Platform exige JWT - 401), ouvidoria WordPress.
- Órgãos do Executivo (SES, SSP, Detran, PCDF, CBMDF, IPEDF/InfoDF, IgesDF, SEDUH/IDE-DF) publicam painéis/documentos HTML; nenhum expõe REST próprio além do portal central.

## 4. Não casados com a lista-alvo e limitações

- Não são órgãos do DF (CNPJ com município Brasília na RFB, mas de outros entes): ADAF-AM (16834893000100, 108 unidades - Agência de Defesa Agropecuária do Amazonas, casada no lote AM), Estado do Amapá, Estado de Mato Grosso, Piauí/Secretaria de Governo, Paraíba (escritório de representação), Tocantins (representação), Paraná (representação), "Secretaria Extraordinária de Representação do Governo em Brasília - SERGB" (representação de outro estado), "SCG" (67535043000142, não identificado) e "Teste Felipe Daniel" (registro de teste no PNCP).
- Órgãos extintos casados ao sucessor: SEPLAG e Sec. de Gestão Administrativa -> SEEC (Economia); AGEFIS -> DF Legal; DFTRANS -> SEMOB; Fundação Hospitalar do DF, Fundo de Saúde e Superintendências de Região de Saúde -> SES-DF; FUNAM -> SEMA; SERIDF (Representação Institucional) -> SERINS; Sec. de Trabalho -> SEDET.
- "DISTRITO FEDERAL" (00394601000126, 176 unidades) e "SECRETARIA DE ESTADO DE ECONOMIA" (00394684000153, 177 unidades) são os CNPJs-guarda-chuva sob os quais as RAs, secretarias e fundos compram no PNCP; as unidades herdam o contato do órgão correspondente nesta base (as 35 RAs têm linha própria com e-mail/telefone oficiais).
- A SES-DF publica contatos setoriais numa página renderizada em JS (contatos-de-sesdf) que nem curl nem Jina conseguiram extrair; o e-mail de gabinete veio do diretório oficial.
- Sites que não responderam: paranoa.df.gov.br (504), funab.df.gov.br (não resolve), adasa.df.gov.br (home 404 mas com e-mails publicados), caesb.df.gov.br ("Request Rejected" - WAF). Cesan-like bloqueios não ocorreram no DF.
- Portal da Transparência do DF é SPA sem API pública documentada (exige x-client-id e mesmo assim 404); a fonte estruturada é o Portal de Dados Abertos (API headless Liferay, 179 conjuntos).

CNPJs-alvo sem casamento (10): 16834893000100 AGENCIA DE DEFESA  AGROPECUARIA E FLORESTAL DO EST; 00394577000206 ESTADO DO AMAPA; 03507415003917 ESTADO DE MATO GROSSO; 06553499000302 PIAUI SECRETARIA DE GOVERNO; 67535043000142 SCG; 00718056000186 GOV EST PARAIBA SECR EXT COORD ESCRIT REPRE NOS ES; 03908372000109 GOVERNO DO ESTADO DO TOCANTINS - SECRETARIA DE REP; 00369942000141 REPRESENTACAO DO GOVERNO DO ESTADO DO PARANA; 36024093000131 SECRETARIA EXTRAORDINARIA DE REPRESENTACAO DO GOVE; 17331629000117 Teste Felipe Daniel

Órgãos sem e-mail nem telefone publicados em texto (só formulário web / site fora do ar): Instituto de Defesa do Consumidor; Junta Comercial; Polícia Civil do Distrito Federal; Polícia Militar do Distrito Federal; Companhia de Desenvolvimento Habitacional; Companhia de Saneamento do Distrito Federal; Instituto de Gestão Estratégica de Saúde do D; Fundação Universidade Aberta do Distrito Fede; Distrito Federal (CNPJ raiz do GDF).

## 5. Próximos passos sugeridos

- Carregar `orgaos.jsonl` na tabela de cadastro institucional (só-nulos, idempotente) usando `cnpjs_pncp` como chave e `fontes_*` como proveniência.
- Unidades compradoras do PNCP (hospitais, RAs, fundos) herdam o contato do órgão-pai desta base; contatos por unidade hospitalar exigem LAI/e-SIC.
- Agendar coleta incremental das APIs abertas (ver `apis.jsonl`, status "200 ok") no framework de ingestão.
