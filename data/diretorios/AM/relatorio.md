# Diretório oficial de órgãos e entidades - Amazonas (AM) + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl com UA de navegador + fallback Jina Reader). Somente páginas públicas; nenhum e-mail/telefone inventado - todo contato tem URL de origem (`fontes_emails`, `fontes_telefones`, `fonte_url`). Esfera: estadual.

Arquivos gerados (JSON Lines, append):
- `~/.claude/jobs/diretorios-uf/AM/orgaos.jsonl` - 92 linhas (91 órgãos/entidades + 1 linha do CNPJ raiz do ente)
- `~/.claude/jobs/diretorios-uf/AM/apis.jsonl` - 30 APIs/portais catalogados, cada um testado com 1 GET real (campos `http`, `bytes`, `content_type`)
- `~/.claude/jobs/diretorios-uf/AM/relatorio.md` - este relatório
- Área de trabalho (HTML baixado, crawl, scripts): `~/.claude/jobs/diretorios-uf/AM/_trabalho/`

## 1. Fontes (diretórios oficiais)

- https://www.transparencia.am.gov.br/estrutura-organizacional/ - "Estrutura Organizacional" do Portal da Transparência (CGE), atualizada 31/07/2026: 74 órgãos (Governadoria, 38 da administração direta, 12 autarquias, 15 fundações, 7 empresas/sociedades, 2 serviços sociais autônomos) com titular, endereço, fones, e-mail, site e horário (Leis Delegadas 122 e 123/2019)
- https://www.amazonas.am.gov.br/ - portal do governo (fale-conosco, órgãos/entidades)
- Sites *.am.gov.br de cada órgão (home + contato/fale-conosco/ouvidoria/contatos/portal/contato)
- Complementos: ALEAM (aleam.gov.br/contato), TCE-AM (tce.am.gov.br, transparencia.tceam.tc.br, ouvidoria.tce.am.gov.br, econtasapi.tce.am.gov.br), TJAM, MPAM (contatos-do-mpam + PDF de contatos), DPE-AM, Portal da Transparência (transparencia.am.gov.br) e API de Dados Abertos

Método: (1) leitura do diretório oficial e extração estruturada; (2) para cada órgão, visita ao site oficial (home) e às páginas candidatas de contato/ouvidoria (links com "ouvidoria", "fale conosco", "contato", "atendimento" + caminhos padrão), com 2ª passada em /contatos, /fale-com-a-secretaria, /fale-com-a-ra, /fale-conosco, /contato, /ouvidoria; (3) descoberta e teste das APIs/portais de dados; (4) casamento com `alvos_AM.csv` por nome/sigla + tabela manual de sucessores/fundos.

## 2. Cobertura - órgãos (92 linhas)

| Campo | Linhas com dado |
|---|---|
| Site | 85 (92%) (site respondeu HTTP 200: 76) |
| E-mail | 83 (90%) - 365 e-mails no total, todos com URL de origem |
| Telefone | 82 (89%) - 396 números |
| Endereço | 75 (82%) |
| Responsável/titular | 74 (80%) |
| Ouvidoria (URL) | 74 (80%) |
| Fale conosco (URL) | 61 (66%) |
| Redes sociais | 62 (67%) |
| Casados com CNPJ da lista-alvo (`cnpjs_pncp`) | 68 (74%) - cobrem 126 dos 128 CNPJs de `alvos_AM.csv` |

Por tipo (contrato): {'outro': 17, 'secretaria': 31, 'empresa': 11, 'fundo': 2, 'autarquia': 12, 'fundacao': 15, 'legislativo': 1, 'tce': 1, 'tribunal': 1, 'mp': 1}. O campo extra `categoria_diretorio` guarda a seção original do diretório.

Rendimento por tipo (com e-mail / com telefone / com ouvidoria):
- secretaria (31): com e-mail 30 / com telefone 30 / com ouvidoria 25
- outro (17): com e-mail 13 / com telefone 11 / com ouvidoria 14
- fundacao (15): com e-mail 12 / com telefone 12 / com ouvidoria 11
- autarquia (12): com e-mail 12 / com telefone 12 / com ouvidoria 9
- empresa (11): com e-mail 10 / com telefone 11 / com ouvidoria 10
- fundo (2): com e-mail 2 / com telefone 2 / com ouvidoria 2
- legislativo (1): com e-mail 1 / com telefone 1 / com ouvidoria 1
- tce (1): com e-mail 1 / com telefone 1 / com ouvidoria 0
- tribunal (1): com e-mail 1 / com telefone 1 / com ouvidoria 1
- mp (1): com e-mail 1 / com telefone 1 / com ouvidoria 1

Órgãos com mais e-mails publicados: ALEAM - Assembleia Legislativa do Estado do A (38); Companhia de Desenvolvimento do Estado do Ama (34); Secretaria de Estado de Administração e Gestã (23); Agência de Defesa Agropecuária e Florestal do (23); Fundação de Amparo à Pesquisa do Estado do Am (22); Processamento de Dados do Amazonas – PRODAM (16); Instituto de Proteção Ambiental do Amazonas – (15); Superintendência de Habitação – SUHAB (11)

## 3. APIs e portais de dados (30 linhas em apis.jsonl)

Status dos testes (1 GET cada): {'200 ok': 28, 'bloqueado': 2}.

Principais achados:
- **TCE-AM eContas API (`econtasapi.tce.am.gov.br`)** - OpenAPI 3 ("DADOS ABERTOS 2.0", `/v3/api-docs`, Swagger UI). Sem autenticação nos endpoints `/transparencia/dados-abertos/*`: `unidades` (todas as UGs estaduais e municipais com CNPJ - chave para os demais), `receitasPrevistas|receitasArrecadadas/{ug}/{ano}`, `pagamentos|empenhos|movimentacoesContabeis/{ug}/{ano}/{mes}`, `dotacoes|licitacoes|contratos|adesoesAta|dispensaInexigibilidadeLicitacao/{ug}/{ano}`, `lotaciograma`, `passagens`, `estagiarios`, `julgamentos/sessao`. Os grupos `/consulta/*` (receita/despesa por município) e `/audicop/*` devolvem 403 (exigem `POST /auth`).
- **Portal da Transparência AM** (CGE, WordPress): não tem CKAN; publica inventário XLSX + manual e uma **API de Remuneração de Servidores** (OpenAPI `api-11.yaml`): `GET admin-ajax.php?action=get_orgaos` (lista de órgãos com id) e `POST action=get_meses_docs&orgao_id=&ano=` (URLs dos CSV/PDF mensais da folha) - ambos 200. Solicitação de novas bases via Fala.BR.
- **Portal da Transparência Fiscal (SEFAZ)** é SPA React sem backend documentado; links citados na página da API (`sgc-am/api/v1/contrato.do`, `e-compras.../api_transparencia_licitacoes_todas.asp`) respondem HTML, não JSON.
- FVS-RCP publica painéis Power BI (`/ver_painel/{n}`); IPAAM publica licenças concedidas em HTML; ALEAM/TJAM/MPAM têm portais de transparência HTML (TJAM remete ao DataJud/CNJ).

## 4. Não casados com a lista-alvo e limitações

- Todos os 128 CNPJs-alvo casaram, exceto Fundo Estadual do Trabalho (FET/AM) e Fundo Estadual Antidrogas, sem secretaria gestora inequívoca no diretório vigente. Os 39 CNPJs "SECRETARIA DE ESTADO DA SAUDE - SUSAM" (matriz + 38 filiais: hospitais, maternidades, UPAs, policlínicas, CEMA, Instituto da Mulher) foram casados à SES-AM; o diretório não publica contato por unidade hospitalar.
- Fundos casados ao gestor pelo nome (FUNESBOM -> CBMAM, FEAS -> SEAS, FEDC -> Procon, FERF -> SECT, FUNDPGE -> PGE, FIA/Idoso -> SEJUSC, FEC -> SEC, FEH -> SUHAB, FESP/reserva de inteligência -> SSP, FMF -> SEFAZ, FUPEAM/Coord. Penitenciária -> SEAP, Fundo da DPE -> DPE-AM, FERMM -> SEDURB, FEAPD -> SEPCD, FEEL -> SEDEL, FERH/FEMA -> SEMA, FES -> SES, FDCT -> SEDECTI, FPS -> Secretaria Executiva do FPS).
- "ESTADO DO AMAZONAS" (04312369000190, 237 unidades) é o CNPJ-guarda-chuva das unidades compradoras.
- Sites do diretório que não respondem: seduc.am.gov.br (vigente: educacao.am.gov.br), imprensaoficial.am.gov.br (302 sem destino), fapeam.am.gov.br (http) e adaf.am.gov.br (http) - resolvidos via https na 2ª passada; segov, faar, cema, fhcfm, funtec/tveradioencontrodasaguas não resolvem; aadesam.org.br e agenciacultural.org.br 503. TJAM e ALEAM não publicam e-mail institucional geral na página de contato (ALEAM publica ouvidoria@aleam.gov.br e e-mails dos 36 gabinetes).
- O diretório oficial publica alguns e-mails pessoais/gmail como contato institucional (ex.: PGE selmaym@bol.com.br, SECOM redacaosecomam@gmail.com); foram mantidos por serem a publicação oficial, com a URL de origem.

CNPJs-alvo sem casamento (2): 33788681000153 FUNDO ESTADUAL DO TRABALHO DO ESTADO DO AMAZONAS -; 05754463000162 FUNDO ESTADUAL ANTIDROGAS

Órgãos sem e-mail nem telefone publicados em texto (só formulário web / site fora do ar): SEGOV - Secretaria de Governo; FHCFM - Fundação Hospital do Coração Francisc; FAAR - Fundação Amazonas de Alto Rendimento; CEMA - Central de Medicamentos (SES); FUNTEC - Fundação Televisão e Rádio Cultura d; Portal da Transparência AM (CGE); Estado do Amazonas (CNPJ raiz).

## 5. Próximos passos sugeridos

- Carregar `orgaos.jsonl` na tabela de cadastro institucional (só-nulos, idempotente) usando `cnpjs_pncp` como chave e `fontes_*` como proveniência.
- Unidades compradoras do PNCP (hospitais, RAs, fundos) herdam o contato do órgão-pai desta base; contatos por unidade hospitalar exigem LAI/e-SIC.
- Agendar coleta incremental das APIs abertas (ver `apis.jsonl`, status "200 ok") no framework de ingestão.
