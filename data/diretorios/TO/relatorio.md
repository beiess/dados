# Diretório oficial de órgãos e entidades do Governo do Estado do Tocantins + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl + Jina Reader). Somente páginas públicas; todo contato tem URL de origem.

ATENÇÃO — contexto da coleta: o portal www.to.gov.br exibe aviso oficial de **suspensão dos sites e redes sociais do Governo do Tocantins durante o período eleitoral** (a partir de 04/07/2026 até o fim das eleições). A home redireciona para servicos.to.gov.br, mas os subsites www.to.gov.br/<slug> continuam respondendo e foram usados.

Arquivos (JSON Lines, UTF-8):
- `~/.claude/jobs/diretorios-uf/TO/orgaos.jsonl` — 54 órgãos/entidades
- `~/.claude/jobs/diretorios-uf/TO/apis.jsonl` — 17 portais/APIs testados (15 "200 ok", 2 erro 404)
- Trabalho em `~/.claude/jobs/diretorios-uf/TO/_trabalho/` (esic_contatos.json, servicos_list.json, crawl_in/out.json). Nada no Google Drive.

## 1. Fontes-mãe
- **https://www.to.gov.br/cge/relacao-dos-responsaveis-pelo-e-sic-dos-orgaos-e-entidades-do-poder-executivo/26kgtfjpk4qj** (CGE-TO) — tabela oficial com 45 órgãos: titular do e-SIC/ouvidoria, WhatsApp, e-mail e endereço (muitos e-mails oficiais são @gmail publicados pela própria CGE — mantidos).
- **https://servicos.to.gov.br/** — Portal de Serviços com lista de 32 órgãos (fichas detalhar_orgao.aspx?cod_empresa=N; fichas individuais muito lentas — download interrompido por tempo).
- **www.to.gov.br/<slug>** — subsites institucionais (saude, secad, seduc, cge, sefaz…), usados pelo crawler (home + páginas de contato/ouvidoria linkadas).
- Poderes: AL-TO, TCE-TO (tceto.tc.br), TJTO, MPTO, DPE-TO.

## 2. Cobertura — 54 órgãos/entidades
Site 44 · E-mail 35 · Telefone 29 · Endereço 48 · E-mail de ouvidoria/e-SIC 40 · Nome do responsável (ouvidor/e-SIC) 44 · CNPJs da lista-alvo casados: **80 de 81** (único não casado: "Associação de Apoio ao Colégio Estadual Bernardo Sayão", entidade privada de apoio escolar, não é órgão estadual).

Fundos sem estrutura própria foram anexados ao órgão gestor com nota em `observacoes` (PM/CBM→fundos de fardamento/modernização/FUNPDEC; SEFAZ→fundo fazendário; SEMARH→recursos hídricos/meio ambiente; SECIJU→drogas/criança/consumo/FUNPES; SETAS→FEAS/pobreza/solidariedade/economia solidária; SECIHD→moradia popular; ADAPEC→FUNPEC). O CNPJ 01612497000102 "ESTADO DO TOCANTINS" (milhares de unidades em `alvos_TO_unidades.csv`: escolas, hospitais, quartéis) herda os contatos dos órgãos-pai listados.

## 3. Catálogo de APIs (17)
- **Portal da Transparência TO** é aplicação **Vaadin 8 server-side** — sem endpoints REST públicos; **não há CKAN estadual** (dados.to.gov.br não responde). Essa é a principal lacuna de dados abertos do estado.
- TCE-TO: portal de transparência próprio (licitações, contratos, remuneração, LRF, /lgpd/dadosAbertos); api.tceto.tc.br responde JSON mas sem rotas documentadas (404).
- AL-TO: transparência (contratos, PCA, fiscais) + licitações. TJTO: transparencia.tjto.jus.br. MPTO: SPA Flutter. DPE-TO: portal próprio.
- Diário Oficial (diariooficial.to.gov.br), Fala.BR/CGU para ouvidoria-LAI, Painel de Monitoramento da Ouvidoria (CGE).

## 4. Faltas/limitações
- Sites em suspensão eleitoral: pouco conteúdo novo; telefones gerais escassos (29/54).
- Fichas do Portal de Serviços não raspadas (timeout; lista salva em servicos_list.json para retomada).
- REDESAT, AGETEC e Fundação de Medicina Tropical: sem contato localizado (registros com CNPJ e nota).
