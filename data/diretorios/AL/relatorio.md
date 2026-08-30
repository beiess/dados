# Diretório oficial de órgãos e entidades - Alagoas (AL) + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl com UA de navegador + fallback Jina Reader). Somente páginas públicas; nenhum e-mail/telefone inventado - todo contato tem URL de origem (`fontes_emails`, `fontes_telefones`, `fonte_url`). Esfera: estadual.

Arquivos (JSON Lines, append):
- `~/.claude/jobs/diretorios-uf/AL/orgaos.jsonl` - 71 linhas (66 do diretório oficial + TJAL, ALE-AL, TCE-AL, MPAL + 1 linha do CNPJ raiz "Estado de Alagoas")
- `~/.claude/jobs/diretorios-uf/AL/apis.jsonl` - 33 APIs/portais, cada um testado com 1 GET real (campos `http`, `bytes`, `content_type`)
- Área de trabalho: `~/.claude/jobs/diretorios-uf/AL/_trabalho/` (HTML baixado, `al_dir.json`, `crawl.jsonl`, `manual.json` com o mapa órgão->CNPJ)

## 1. Fontes (diretórios oficiais)
- https://alagoas.al.gov.br/secretarias - "Estrutura Organizacional / Secretarias e Órgãos" do portal do governo. A lista é carregada por AJAX em `https://alagoas.al.gov.br/lista_secretarias.php?pag=1..9` (66 órgãos com titular, endereço, e-mail, telefone, horário, site, link de competências e LGPD). Organograma PDF e Lei Delegada 48/2022 na mesma página.
- https://alagoas.al.gov.br/fale-conosco e https://alagoas.al.gov.br/ouvidoria (Ouvidoria-Geral na CGE; e-OUV)
- https://transparencia.al.gov.br/ (Portal da Transparência Graciliano Ramos, CGE/ITEC): páginas /portal/api, /portal/download-de-dados, /portal/outros-poderes
- Poderes: TJAL (tjal.jus.br - SPA, lido via Jina: /ouvidoria, /enderecos), ALE-AL (al.al.leg.br - Plone; /contact-info devolve 403 até via Jina), TCE-AL (tceal.tc.br), MPAL (mpal.mp.br + transparencia.mpal.mp.br)
- Sites de cada órgão (home + páginas de contato/ouvidoria via `crawl_site.py`)

## 2. Cobertura - órgãos (71 linhas)
| Campo | Linhas com dado |
|---|---|
| Site | 67 |
| E-mail | 61 (112 e-mails, todos com URL de origem) |
| Telefone | 63 (217 números) |
| Endereço | 68 |
| Responsável/titular | 64 |
| Ouvidoria (URL) | 40 |
| Fale conosco (URL) | 45 |
| Redes sociais | 43 |
| Casados com CNPJ da lista-alvo | 59 - cobrem 62 dos 62 CNPJs de `alvos_AL.csv` |

Por tipo: {'autarquia': 22, 'empresa': 5, 'outro': 13, 'fundacao': 1, 'secretaria': 26, 'tribunal': 1, 'legislativo': 1, 'tce': 1, 'mp': 1}.

Casamento com a lista-alvo: feito por mapa manual (`_trabalho/manual.json`). Fundos sem site próprio foram associados ao órgão gestor: Fundo Estadual de Defesa Civil -> Coordenadoria de Defesa Civil; FESP -> SSP-AL; Fundo de Recursos Hídricos -> Semarh; FDRH -> Seplag. Pericia Oficial -> Polícia Científica (Polcal); Instituto de Inovação p/ Desenvolvimento Rural -> Emater; Procuradoria-Geral de Justiça -> MPAL; Diretoria de Teatros -> Diteal. O CNPJ raiz 12200176000176 (200 unidades compradoras: Porto de Maceió, polícias, DER etc.) está na linha "Estado de Alagoas (CNPJ raiz)".

Sem e-mail publicado (10): Desenvolve, Casal, GMAL, Procon Alagoas, Alagoas Sem Fome, Seagri, Sefaz, Governança, Semu, ALE-AL.
Sem site no diretório (4): GMAL, Governança, Semu, SEDH.

## 3. APIs e portais de dados (33 linhas)
Status dos testes: {'200 ok': 30, 'erro': 2, 'bloqueado': 1}.
- **Portal da Transparência AL - API JSON** (`/portal/api`): todas as consultas do portal em JSON, sem chave (o portal pede header `X-Requested-With: XMLHttpRequest`, mas respondeu 200 mesmo sem). Endpoints testados 200: `orcamento/json-dotacoes-avancada-ug/` (lista de UGs com id), `pessoal/json-servidores/?ano&mes&limit&offset` (folha), `licitacao/json-editais/`, `despesa/json-despesa-avancada-filtro/`, `receita/json-receita-avancada-filtro/`, `patrimonio/json-patrimonio-imobiliario/`, `repasse/json-repasse-municipios/`. Docs por endpoint em `/portal/api/<grupo>/<consulta>` (62 páginas) e dicionário em `/portal/api/dicionario-de-dados`. Licença CC BY-SA.
- **Download de dados**: `/portal/download-de-dados/<tabela>` descreve o layout (.txt pipe, zipado por ano); a lista de arquivos vem de `GET /arquivos-download/<tipo>` (JSON `[{ano,tipo,nome}]`, tipos folha_ativo, folha_inativo, licitacao...). O caminho `/media/arquivo/<nome>` indicado pelo JS devolveu 404 no teste - registrar como pendência.
- CGE: CEIS/AL (ceis.cge.al.gov.br), e-SIC (relatórios LAI), e-OUV. `dados.al.gov.br` (Alagoas em Dados) fora do ar.
- TCE-AL: consultas HTML (licitações SICAP, prestação de contas, processos, DOE) + painéis Power BI Report Server; sem API aberta documentada localizada.
- ALE-AL: Portal da Transparência (Plone, RSS) + SAPL com API REST (`sapl.al.al.leg.br/api/` 200).
- MPAL: transparencia.mpal.mp.br (HTML). TJAL: SPA; API de notícias exige token (401).

## 4. Faltas e limitações
- ALE-AL: página de contato (`/contact-info`) devolve 403 (nginx) para curl e Jina; só telefone do SIC presencial (82 3013-2263). Endereço não publicado em texto legível.
- TCE-AL e MPAL: endereço não extraído (páginas de unidades do MPAL têm telefones por unidade; endereço em tabela sem rótulo claro).
- Gabinete Militar, Semu, SEDH, Governança: sem site no diretório oficial.
- Órgãos sem e-mail no diretório e cujo site não publica e-mail em texto: ver lista acima (contato apenas por formulário/telefone).
- ZIPs de download da transparência: 404 no caminho indicado (verificar caminho real no navegador).
