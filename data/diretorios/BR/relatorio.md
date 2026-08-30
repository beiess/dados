# Diretório oficial da União (esfera federal) — contatos e catálogo de APIs

Gerado em 2026-08-30. Arquivos: `BR/orgaos.jsonl` (895 linhas), `BR/apis.jsonl` (158 linhas). Só leitura de páginas públicas; nenhum e-mail/telefone foi inferido — todos vêm de página oficial com `fonte_url` registrada.

## Cobertura de órgãos (BR/orgaos.jsonl)

- Total de órgãos/entidades: **895** — por poder: Executivo (conselho profissional): 525, Executivo: 266, Judiciário: 94, Funções Essenciais à Justiça: 7, Legislativo: 3
- Com e-mail: **811** (90%) | com telefone: **853** (95%) | com site: 755 | com endereço: 515 | com URL de ouvidoria: 397 | com fale-conosco: 359 | com redes sociais: 440
- Com e-mail OU telefone: **871**; sem nenhum contato: 24

### Casamento com a lista-alvo (alvos_BR.csv, 1.126 CNPJs do PNCP)

- Alvos casados com algum registro do diretório: **1005/1126** (89%); entre os 300 primeiros (mais unidades): **281/300**; entre os que publicaram no PNCP: **594/623**
- Alvos casados com registro que tem e-mail: **920**; com telefone: **976**
- Alvos não casados: 121 — por categoria: conselho: 58, militar: 23, fundacao: 13, empresa: 12, autarquia_outra: 10, hospital: 3, adm_direta: 1, judiciario: 1
  - Motivos: CNPJs de entidades extintas/sucedidas (CEFETs e Escolas Agrotécnicas foram mapeados ao IF sucessor quando o município era inequívoco; ministérios extintos mapeados ao sucessor quando óbvio), unidades militares avulsas (batalhões, bases) que pertencem aos Comandos, fundos contábeis sem estrutura própria (FCDF, FESR, FUNDEB…), registros espúrios do PNCP ('Cliente de Demonstração', câmaras/fundos municipais cadastrados como federais) e conselhos regionais cujo diretório federal não foi alcançado (ver 'O que faltou').

## Fontes usadas (diretórios oficiais)

1. **SIORG — Estrutura Organizacional do Poder Executivo Federal** (API pública, sem chave): `https://estruturaorganizacional.dados.gov.br/doc/orgao-entidade/completa?codigoPoder={1..4}&codigoEsfera=1` → 330 órgãos/entidades (265 Executivo, 59 Judiciário, 3 Legislativo, 3 Funções Essenciais à Justiça) com telefone, e-mail, site e endereço oficiais (278 com contato). É a espinha dorsal do diretório.
2. **gov.br — Órgãos do Governo**: `https://www.gov.br/pt-br/orgaos-do-governo` (só ministérios) e a listagem completa `https://www.gov.br/pt-br/servicos/listar_orgaos?b_start:int=0..330` → 338 páginas `/pt-br/orgaos/<slug>` (site oficial, ouvidoria e telefone quando publicados; a maioria não tem bloco de contato).
3. **Sites dos órgãos** (home + Canais de atendimento/Fale conosco/Ouvidoria): 265 do Executivo (SIORG), 109 do Judiciário/MPU/Legislativo/militares (+ retentativas via Jina Reader para sites com WAF: TREs, TSE, Marinha, FAB), 30 conselhos federais.
4. **Diretórios dos conselhos federais de fiscalização profissional** (fonte oficial dos regionais): CFO (`website.cfo.org.br/conselhos-regionais/`), CONFEA (`confea.org.br/sistema-profissional/creas`), CFM (`portal.cfm.org.br/epweb/contatos_{norte,nordeste,sul,sudeste,centrooeste}.html`), CFF (`site.cff.org.br/regionais`), CFA (`cfa.org.br/institucional/conselho-regional/`), CFC (`cfc.org.br/conselhos/` + 27 subpáginas), CFMV (`cfmv.gov.br/conselhos-regionais/` + 27 subpáginas), COFEN (`cofen.gov.br/contato/conselhos-regionais/` → 27 sites dos Corens), CFP (`site.cfp.org.br/cfp/sistema-conselhos/conselhos-pelo-brasil/`), CFESS (`cfess.org.br/pagina/view/24`), CFN (`cfn.org.br/index.php/conselhos-regionais/` via Jina), CONFEF (`confef.org.br/crefs/` via Jina), COFFITO (`coffito.gov.br/nsite/?page_id=3009`), CONTER (`conter.gov.br/regionais/`), CFFa (`fonoaudiologia.org.br/conselhos-regionais/`), CFBio (`cfbio.gov.br/crbios/`), COFEM, CONFERE (`confere.org.br/enderecos.php`), COFECI (lista oficial publicada pelo CRECI-RS `creci-rs.gov.br/siteNovo/conselhos.php`), CAU/UF (27 sites `cau{uf}.gov.br`), CFQ (sites `crq{n}.org.br`), COFECON (sites `corecon-{uf}.org.br`), CFT (sites CRT), CFBM (sites CRBM), OAB (`oab.org.br/seccional/{uf}`).
5. **dados.gov.br**: a API pública (`/dados/api/publico/…`) exige chave (HTTP 401 sem ela) — catalogada como 'bloqueado (exige chave)'; o CKAN legado (`/api/3/action/…`) foi descontinuado. Por isso o catálogo por órgão foi montado a partir dos portais setoriais próprios (abaixo) e testado com 1 GET real cada.

## Catálogo de APIs (BR/apis.jsonl)

- Total: **158** APIs/portais; status: 200 ok: 107, erro: 36, bloqueado: 10, bloqueado (exige chave): 4, 302: 1
- Por domínio: outro: 58, educacao: 43, transparencia: 12, normas: 12, geo: 10, saude: 10, compras: 4, orcamento: 4, servidores: 3, obras: 2
- APIs programáveis (REST/OpenAPI/CKAN) respondendo 200: **50** — destaques: MGI — SIORG — Estrutura Organizacional; MGI — Compras.gov.br — API de Dados Abertos; MGI — PNCP — API de consultas; MGI — PNCP — API PNCP; MGI — Transferegov — API de Dados Abertos; STN — Tesouro Transparente — API SICONFI; STN — Tesouro Transparente — CKAN; STN — SIAFI — dados abertos; IBGE — API de localidades; IBGE — SIDRA — API de tabelas; IBGE — API de malhas geográficas; MS — API de Dados Abertos do Ministério da Saúde; CAPES — Dados abertos CAPES; CNJ — DataJud — API pública; TCU — Dados abertos TCU; Câmara — Dados Abertos da Câmara dos Deputados; Senado — Dados Abertos do Senado; BCB — Dados Abertos BCB; BCB — OLINDA — APIs BCB; RFB — minhareceita.org; ANEEL — Dados abertos ANEEL; ANA — Portal de dados abertos ANA; BNDES — Dados abertos BNDES; IBAMA — Dados abertos IBAMA; MAPA — API Agrofit/Sistemas MAPA
- Exigem chave/token (gratuita): dados.gov.br (chave via login gov.br), Portal da Transparência (chave CGU, já disponível no projeto em PORTAL_TRANSPARENCIA_KEY), DataJud/CNJ (APIKey pública divulgada na wiki — testado 200 com ela), SERPRO (comercial).
- Bloqueios/erros registrados: TSE (CKAN e CDN respondem 403 a clientes não-navegador), ANATEL `anatel.gov.br/dadosabertos` (403), e-MEC (403), OpenDataSUS (500 no momento do teste), hosts que não resolveram DNS no teste (dados.tcu.gov.br, dados.antt.gov.br, ipeadata OData, dadosabertos.cnj.jus.br, dados.ufsc.br, dadosabertos.dataprev.gov.br) — marcados 'erro' com observação.

## O que faltou / limitações

- **TREs**: sites atrás de WAF (403 para curl); via Jina Reader obtivemos ouvidoria/telefones de parte deles, mas o Jina limita taxa (403 após ~8 requisições seguidas) — os TREs restantes ficaram sem e-mail (o SIORG traz contato de TRE-RR, TRE-MA, TRE-RO, TRE-SP).
- **Comando da Marinha e FAB** (`marinha.mil.br`, `fab.mil.br`): 403 para curl; contatos vieram só do que o Jina conseguiu ler; Exército (`eb.mil.br`) não expõe e-mail/telefone na home nem em /contato.
- **Seções Judiciárias (JF)**: só as da 5ª Região (jfce, jfpe, jfrn, jfpb, jfal, jfse) e parte da 1ª (portal.trf1.jus.br/sjXX) e 2ª/4ª têm site próprio acessível; várias retornam vazio para curl.
- **Conselhos regionais sem diretório federal legível**: CRB (Biblioteconomia — só links), CRQ/CORECON/CRT/CRBM/CAU/COREN foram cobertos por crawl direto dos sites regionais (rendimento parcial); OAB seccionais têm páginas dinâmicas (JS) sem contato no HTML; CFC bloqueou 7 subpáginas por taxa (retentadas lentamente).
- **CFM**: a única lista consolidada de CRMs com e-mail está em página antiga do portal (epweb, 2011) — registrada com observação 'conferir no site do CRM'.
- **dados.gov.br por órgão**: não catalogado (exige chave). Rota: gerar chave em https://dados.gov.br (login gov.br) e chamar `GET /dados/api/publico/conjuntos-dados?idOrganizacao=…` com cabeçalho `chave-api-dados-abertos`.
- Telefones/e-mails do SIORG são os cadastrados pelo próprio órgão (gabinete/presidência); e-mails de crawl podem incluir setoriais (corregedoria, protocolo). Nenhum foi filtrado por LGPD (todos públicos/institucionais); e-mails não-institucionais (gmail/uol etc.) de conselhos foram mantidos por serem os publicados oficialmente.
- Não foi feita carga no banco (tarefa era só curadoria em arquivos); o enriquecimento no cadastro_institucional_br deve ser só-nulos, casando por `cnpjs_pncp`.

## Formato

Campos extras além do contrato: `poder`, `natureza_siorg`, `siorg_codigo`, `govbr_url`, `fonte_url_contato`, `fontes[]`, `cnpjs_pncp[]` (CNPJs da lista-alvo casados), `n_unidades_pncp`, `publicou_pncp`, `uf_sede` (conselhos regionais), `obs`.
