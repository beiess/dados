# Diretório oficial de órgãos e entidades do Governo do Estado de São Paulo + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl + Jina Reader). Somente páginas públicas; nenhum e-mail/telefone inventado - todo contato tem URL de origem (`fontes_emails`, `fontes_telefones`, `fontes_endereco`, `fonte_url`).

Arquivos gerados (JSON Lines, UTF-8):
- `~/.claude/jobs/diretorios-uf/SP/orgaos.jsonl` - 215 linhas = 107 órgãos/entidades + 108 unidades regionais com posto SIC (91 Diretorias de Ensino da SEDUC e 17 Departamentos Regionais de Saúde da SES; campo `categoria_diretorio` = "Unidade regional (SIC.SP)", `orgao_pai` = secretaria)
- `~/.claude/jobs/diretorios-uf/SP/apis.jsonl` - 117 APIs/portais de dados catalogados e testados com 1 GET real
- `~/.claude/jobs/diretorios-uf/SP/relatorio.md` - este relatório
- Trabalho intermediário em `~/.claude/jobs/diretorios-uf/SP/_trabalho/` (master.tsv, crawls, fontes brutas). Nada foi gravado no Google Drive.

## 1. Fontes-mãe (diretórios oficiais)

- **https://www.sp.gov.br/sp/institucional/estrutura** - "Estrutura" do portal oficial (CMS estadual): seções Secretarias (27), Autarquias (24), Fundações (15), Empresas (10), Poder Público (links para ALESP, TCE, TJSP, TJMSP, MPSP, DPE). Cada página `/estrutura/<secao>/<slug>` traz só o titular (nome + cargo) e biografia; **não publica site, e-mail nem telefone** (campo `responsavel_legal` das 27 secretarias veio daí).
- **https://fala.sp.gov.br/ouvidoria-sic** (Fala.SP / CGE) - "Lista de contatos das Ouvidorias": 65 cards com órgão, responsável, endereço, telefone e e-mail da ouvidoria. A aba "Serviços de Informação ao Cidadão" é carregada por Blazor interativo e não vem no HTML.
- **http://www.sic.sp.gov.br/Telefones.aspx e /Enderecos.aspx** (SIC.SP) - dropdown com 197 postos SIC; o botão "Download de Todos" (postback ASP.NET `ctl00$MainContent$linkDownload`) devolve planilha .xls (tabela HTML) com SIC central, subsetorial, endereço, CEP, município, telefone, horário, **e-mail e responsável** de todos os postos (inclui 91 Diretorias de Ensino, 17 DRS, Polícia Civil/Militar/Científica, Bombeiros, CEE, Arquivo Público, EFCJ, Fundo Social, agências de bacia).
- **https://www.transparencia.sp.gov.br/ANEXOS/HorarioAtendimento.pdf** (Portal da Transparência/CGE) - endereço da sede e horário de atendimento de 27 secretarias.
- **https://www.ouvidoria.sp.gov.br/Portal/ConsultaRedePaulista.aspx** - Rede Paulista de Ouvidorias (~150 entradas, inclui concessionárias); detalhe só por postback, não explorado.
- **https://dadosabertos.sp.gov.br** (CKAN) - 53 organizações publicadoras usadas para o campo `dados_abertos_urls` e para o catálogo de APIs.
- Sites oficiais de cada órgão (home + até 12 páginas institucionais/canais de comunicação/ouvidoria/dados abertos) e páginas específicas de contato (135 URLs extras). Cascata de acesso: curl com UA de navegador -> Jina Reader (sem UA; com UA o Jina devolve 403 do Cloudflare).
- RFB (minhareceita.org) para os 6 CNPJs da lista-alvo sem correspondência óbvia.

## 2. Cobertura - órgãos/entidades (107 linhas) e unidades (108 linhas)

| Campo | Órgãos (107) | Unidades SIC (108) |
|---|---|---|
| Site | 104 (HTTP 200 em 84) | herdam o da secretaria |
| E-mail | 95 | 108 |
| Telefone | 98 | 108 |
| Endereço | 88 | 108 |
| Horário | 29 | 104 |
| Responsável (titular) | 27 | - |
| Ouvidoria (URL) | 92 | 108 (Fala.SP) |
| Ouvidoria (e-mail dedicado) | 63 | - |
| SIC (e-mail) | 82 | 108 |
| SIC (telefone) | 82 | 108 |
| Fale conosco (URL) | 91 | - |
| Dados abertos (URLs) | 48 | - |
| Redes sociais | 29 | - |
| Casados com CNPJ da lista-alvo PNCP | 93 | 105 casadas a unidade PNCP (`unidade_pncp`/`codigo_unidade_pncp`) |

Totais: **811 e-mails** e **1000 telefones** com URL de origem.

Por tipo (contrato) - linhas / com e-mail / com telefone / com ouvidoria:
- secretaria: 27 / 26 / 26 / 26
- autarquia: 28 / 24 / 26 / 24
- fundacao: 17 / 16 / 16 / 15
- empresa: 17 / 11 / 12 / 12
- outro: 11 / 11 / 11 / 9
- legislativo: 1 / 1 / 1 / 1
- tce: 1 / 1 / 1 / 1
- mp: 2 / 2 / 2 / 1
- tribunal: 2 / 2 / 2 / 2
- fundo: 1 / 1 / 1 / 1

Maiores rendimentos de e-mail: SEMIL (91), DER-SP (60), MPSP (50), FAMERP (43), HCFMUSP (30), SP ÁGUAS (26), SAP (21), CEETEPS (19), IPT (19), FOSP (17), SP-PREVCOM (17), CPTM (13).

Sem e-mail publicado: SPE, UNESP, USP, EMTU, EMAE, CESP, CTEEP/ISA, DERSA, CPETUR, FB, SUCEN, DAESP. Sem telefone: SPE, EMTU, EMAE, CTEEP/ISA, DERSA, CPETUR, FPZSP, SUCEN, DAESP. (SPE é secretaria nova com site-stub; USP e Unesp publicam só formulário/telefone na ouvidoria; as demais são empresas privatizadas ou entidades extintas mantidas por constarem na lista PNCP.)

Casamento com `alvos_SP.csv`: **233 de 234 CNPJs** casados (2.559 das 2.562 unidades). Excluído por não ser de SP: 22217896000106 "Secretaria de Estado de Transporte e Desenvolvimento Urbano" (RFB: Maceió/AL). Reclassificações via RFB: 08678541000185 (PNCP "Desenvolvimento Metropolitano") é hoje a **SCTI**; 34129394000102 (Relações Internacionais, baixado) -> SGRI; 46385100000184 (Emprego e Relações do Trabalho, extinta) -> SDE; 46375200000120 (Logística e Transportes) -> SEMIL; 18174562000117 (Administração Geral do Estado) e 53378154000188 (Escritório de Representação) -> linha "Estado de São Paulo". O CNPJ raiz 46379400000150 (1.020 unidades) tem ~600 unidades que são **prefeituras, câmaras, consórcios, fundos municipais e entidades privadas** que compram via BEC sob o CNPJ do Estado - não são órgãos estaduais. As 15 filiais do DER, 79 da USP e 37 da Unesp foram agrupadas nas linhas DER/USP/Unesp (`cnpjs_pncp` lista todos).

## 3. APIs e portais de dados (117 linhas em apis.jsonl)

Status dos testes (1 GET cada, range 0-4000 quando arquivo): {'200 ok': 115, 'erro': 1, 'bloqueado': 1}. Tipos: {'CKAN': 45, 'CSV/ZIP': 15, 'portal-html': 45, 'REST': 8, 'outro': 2, 'DKAN': 2}.

Principais achados:
- **dadosabertos.sp.gov.br (CKAN 2.x)** - API aberta sem chave: package_search/package_show/organization_show/group_list (200). 439 conjuntos em 53 organizações; `organization_list` pagina de 25 em 25 (usar offset). DataStore inativo (404) - baixar por `resources[].url` (muitos apontam para arquivos nos sites dos órgãos: DER, Infosiga/Detran, blob da SEMIL, SEFAZ, CGE...). Catalogada 1 linha por organização com `fq=organization:<slug>` (36 com conjuntos: DER 44, SP Águas 33, SEFAZ 32, SEADE 26, SEMIL 24, CPS 24, Detran 20, Cultura 20, ARTESP 20, SAA 19, AGEMCAMP 18, AGEM 17, HCFMUSP 17, SES 14, Turismo 13, STM 11, SGRI 11, Procon 11, SEDUC 10, CGE 10 ...). Teste de 1 recurso por organização registrado em `obs`.
- **Portal da Transparência SP** - downloads diretos sem API: Remuneração mensal completa (CSV 237 MB + histórico mensal zip ids 30-69), Licitações.zip, Contratos.zip, PlanoContratacaoAnual.zip (todos 200/206) com dicionários xlsx; painéis HTML de despesas, obras, convênios, emendas, diárias, sanções.
- **SIGEO Lei 131 (SEFAZ)** - consultas ASP.NET de despesa/receita (200); sem REST. BEC/SP consulta de pregões (200, ASP.NET).
- **DOE-SP** - backend REST do novo Diário Oficial: `https://do-api-web-search.doe.sp.gov.br/v2/advanced-search/publications` (200 JSON). Busca legada da Imprensa Oficial (200).
- **TCE-SP Transparência Municipal** - API REST documentada em /apis: `/api/{json|xml}/despesas/{municipio}/{ano}/{mes}`, `/receitas/...`, `/municipios` (200); conjuntos Audesp completos em zip/csv (despesas 2008-2025 ~2 GB/ano, receitas, RCL, dívida ativa, licitações/ajustes mensais 2018-2025, pareceres, planejamento municipal) - 206.
- **ALESP Dados Abertos** - catálogo em /dados-abertos (grupos: processo legislativo 16 recursos, deputados 3, administração 4, legislação 5, agenda 1); XML/ZIP em /repositorioDados/ (deputados.xml, despesas_gabinetes.xml, partidos.xml, proposituras.zip, naturezasSpl.xml - 200/206).
- **SEADE** - repositório CKAN próprio (86 conjuntos, CSV/XLSX/SHP) - 200; Painel SEADE (SPA); IMP não respondeu.
- **SEDUC** - portal DKAN dados.educacao.sp.gov.br: `api/3/action/package_list` (200) e catálogo DCAT `data.json` (66 conjuntos: matrículas, SARESP, IEE, diplomas, profissionais, orçamento).
- **ARTESP** - CKAN próprio (package_list 200; package_search exige POST).
- **Detran** - Infosiga: CSVs mensais de sinistros em blob (206). **SSP** - planilhas mensais de dados criminais (206; página é SPA). **Jucesp** - CSV mensal de registros (206). **DER** - xlsx de contratos/obras (206). **SP Águas**, **SEMIL**, **CGE**, **SGRI**, **PGE**, **IAMSPE**, **Famerp** - recursos CSV/XLSX/XML testados 200/206.
- **CETESB** - QUALAR exige login para exportar (marcado `auth: login`); página de dados abertos (200). **MPSP** - transparência bloqueada para curl (403 WAF; Jina lê). **TJSP** - e-SAJ (HTML); dados estruturados só via DataJud/CNJ. **HCFMUSP**, Metrô, CPTM, Sabesp, Prodesp, CPS, USP, Unicamp, Unesp, Fapesp e 13 páginas padrão "transparencia/dados-abertos" do CMS estadual - portais HTML (200), sem API.
- **SIC.SP "Download de Todos"** - registrado como fonte estruturada (POST, 200, xls).

## 4. O que não foi encontrado / limitações

- Aba SIC do Fala.SP (Blazor interativo) não é lida por curl/Jina; suprida pelo download do SIC.SP.
- Sites que curl não acessa (Cloudflare/WAF): tjmsp.jus.br, mpsp.mp.br, policiacivil.sp.gov.br, desenvolvesp.com.br, fundacaobutantan.org.br, detran.sp.gov.br - lidos via Jina (sem UA). hcfmb.unesp.br não respondeu nem ao Jina (timeout) e emtu.sp.gov.br redireciona para a ARTESP.
- Sites estaduais no CMS padrão (sp.gov.br) publicam pouco e-mail: contatos concentrados em Fala.SP/SIC.SP; e-mails setoriais existem em SEMIL (71), MPSP (50), SAP (21), SP Águas (23), IPT, CDHU, SPPREV, FUNAP, FURP, Cultura.
- Poder Público (TJSP, MPSP, ALESP, TCE, DPE, TJMSP) não consta no Fala.SP/SIC.SP; contatos vieram dos próprios sites.
- Rede Paulista de Ouvidorias (ouvidoria.sp.gov.br) tem detalhe por postback e inclui concessionárias privadas - não explorado.
- Entidades privatizadas/extintas da lista PNCP (CESP, CTEEP, EMAE, Dersa, CPETUR, SUCEN, DAESP, Fundação Zoológico) ficaram com linha mínima e `obs` explicativa.
- Portal de Compras/e-negócios (compras.sp.gov.br, enegociospublicos.com.br) e esancoes.sp.gov.br não responderam (DNS/timeout).
