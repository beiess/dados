# Diretório oficial de órgãos e entidades do Governo de Minas Gerais + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl + Jina Reader). Somente páginas públicas; nenhum e-mail/telefone inventado - todo contato tem URL de origem (`fontes_emails`, `fontes_telefones`, `fonte_url`).

Arquivos gerados (JSON Lines, append):
- `~/.claude/jobs/diretorios-uf/MG/orgaos.jsonl` - 97 linhas (96 órgãos/entidades do diretório oficial + 1 linha do CNPJ raiz "Estado de Minas Gerais")
- `~/.claude/jobs/diretorios-uf/MG/apis.jsonl` - 63 APIs/portais catalogados e testados com 1 GET real
- `~/.claude/jobs/diretorios-uf/MG/relatorio.md` - este relatório

## 1. Fonte-mãe: diretório oficial

- **https://www.mg.gov.br/estrutura-governamental** - "Estrutura do Governo" do portal oficial. Cada órgão tem página `/instituicao_unidade/<slug>` com: Responsável Legal, Telefone, Site, Endereço, Horário de funcionamento, Organograma (PDF) e serviços. Não publica e-mail (exceto alguns conselhos).
- Seções do diretório (96 entradas): Secretarias de Estado 14 + Secretaria-Geral 1, Autarquias 17, Fundações 12, Empresas Estatais 15, Órgãos Autônomos 8 (AGE, CGE, CBMMG, ESP, GMG, OGE, PCMG, PMMG), Conselhos Estaduais 22, Judiciário 2 (TJMG, TJMMG), Legislativo 2 (ALMG, TCE), Ministério Público 1, Defensoria 1, Vice-Governadoria 1.
- PDF da estrutura orgânica do Executivo (16/07/2025): https://www.mg.gov.br/sites/default/files/media/document/2025/07/estrutura-organica-do-poder-executivo-de-mg-160725.pdf
- Complementos: https://www.mg.gov.br/pagina/telefones-e-sites-uteis (LigMinas 155, OGE 162, Cemig 116, Copasa 115, Detran/CET 155…), https://www.ouvidoriageral.mg.gov.br/canais-atendimento (162, WhatsApp 31 3915-2022, endereço da OGE), Portal de Dados Abertos https://dados.mg.gov.br (CKAN).

Para cada órgão visitou-se o site oficial (home) e até 8 páginas candidatas (links "ouvidoria", "fale conosco", "contato", "atendimento" + caminhos padrão /contato, /fale-conosco, /ouvidoria, /institucional/contato). Cascata de acesso: curl UA-navegador -> curl HTTP/1.1 -> curl Firefox -> Jina Reader. Passada extra em páginas "quem é quem"/institucional das secretarias.

## 2. Cobertura - órgãos (97 linhas)

| Campo | Linhas com dado |
|---|---|
| Endereço (do diretório) | 97 (100%) |
| Telefone | 92 (94%) - 408 números no total |
| Site | 90 (92%) (site respondeu HTTP 200: 76) |
| E-mail | 60 (61%) - 579 e-mails no total, todos com URL de origem |
| Ouvidoria (URL) | 61 (62%) |
| Fale conosco (URL) | 61 (62%) |
| Redes sociais | 51 (52%) |
| Casados com CNPJ da lista-alvo PNCP (`cnpj_pncp`) | 61 (62%) |

Por tipo (contrato): {'autarquia': 17, 'outro': 33, 'empresa': 15, 'fundacao': 12, 'tribunal': 2, 'legislativo': 2, 'mp': 1, 'secretaria': 15}. O campo extra `categoria_diretorio` guarda a seção original (Órgãos Autônomos, Conselhos etc.).

Rendimento por tipo (com e-mail / com telefone / com ouvidoria):
- Secretarias (15): 3 / 12 / 11 - a maioria das secretarias **não publica e-mail**: só formulário e encaminhamento à OGE. Exceções: SES (90 e-mails setoriais publicados no site), SEE (85 e-mails no "Quem é quem"), SEINFRA (84).
- Autarquias (17): 11 / 16 / 13 (IPEM 33 e-mails, IDENE 25, ARTEMIG 20, DER 20).
- Fundações (12): 9 / 12 / 6 (Hemominas, FAOP, Funed, FJP, FHA, FCS, Fucam, IEPHA, FAPEMIG).
- Empresas (15): 10 / 15 / 11 (Cohab 15, MGI 15, BDMG, Codemge, Gasmig, Prodemge, Epamig, EMC, Invest Minas, MGS).
- Órgãos autônomos/conselhos/outros (33): 23 / 32 / 15 (AGE 50 e-mails, OGE 15, 19 dos 22 conselhos têm e-mail publicado no próprio diretório).
- Poderes/MP (5): TJMMG 48 e-mails, TCE, ALMG, MPMG com e-mail; TJMG só telefone.

Casamento com as listas-alvo: 60 dos 67 CNPJs de `alvos_MG.csv` foram casados a uma linha (campo `cnpj_pncp` + `n_unidades_pncp`). Não casados e motivo: SENAC-MG (03447242000116) - entidade do Sistema S, não é órgão estadual; PRODERJ (30121578000167) - autarquia do RJ, listada por engano em MG; IGAM CNPJ 17387481000302 - filial BAIXADA na RFB (matriz 17387481000132 casada); PMMG CNPJ 16695025011121 - filial (matriz 16695025000197 casada); ESTADO DE MINAS GERAIS 18715615000240 - filial (SCGOV/ENCARGOS/SEF). A linha "EMG" (CNPJ 18715615000160, 1.053 unidades) cobre o CNPJ raiz; observou-se que ~600 dessas unidades PNCP são **prefeituras/câmaras** e ~50 são **consórcios intermunicipais/fundos municipais** que compram sob o CNPJ do Estado (via Portal de Compras MG) - não são órgãos estaduais e não foram curados aqui. Unidades regionais (SREs, GRS/URS, URFBio, SUPRAM, URG do DER, AFs da SEF, delegacias, batalhões) herdam o contato do órgão-pai; as páginas de unidades regionais visitadas (SEE/SREs, PCMG/unidades, SEF/atendimento) não publicam e-mail por unidade.

## 3. APIs e portais de dados (63 linhas em apis.jsonl)

Status dos testes (1 GET cada): {'200 ok': 56, 'bloqueado': 4, 'nao_testado': 2, 'erro': 1}.

Principais achados:
- **dados.mg.gov.br (CKAN)** - API completa sem chave: package_search/package_show/organization_list (200). 95 conjuntos em 18 organizações; DataStore desativado (datastore_search 404) - baixar CSV/JSON por `resources[].url` (testado 200). Catalogado 1 linha por organização com `fq=organization:<slug>` (CGE 17, SEPLAG 17, FHEMIG 27, SES 8, IPSEMG 8, FAPEMIG 3, IEPHA 3, SEF 2, SEJUSP 2, GMG 2, SG 2, DER 1, PCMG 1, SEDESE 1, SEGOV 1; ARTEMIG/SCC/SEINFRA sem conjuntos). Destaques: remuneração de servidores (166 recursos), relação nominal de servidores, SIAFI/SISOR, notas fiscais (113), licitações, contratos, obras (DER), crimes (SEJUSP), hospitalares (FHEMIG).
- **Portal da Transparência MG** - SPA Angular; backend `https://apigw.mgapi.prodemge.gov.br/portaltransparencia/1.0.0` exige token OAuth2 (401) obtido em `/oauth2/token` com credencial embutida no bundle -> registrado como *bloqueado*; Jina recebe 403. Endpoints mapeados no bundle (contratos.json, lista-orgaos.json, visao-geral.json etc.) ficam anotados na linha.
- **ALMG Dados Abertos API v2** - REST/JSON aberto, Swagger em https://dadosabertos.almg.gov.br/api/ajuda/swagger/view/lastest (deputados, comissões, legislação, contratos/atas/convênios) - 200.
- **TCE-MG** - portal dadosabertos.tce.mg.gov.br é SPA cujo backend (`arabiasaudita.tce.mg.gov.br:8443/TCEMG-proxy-web/publico/wso2amgw/dados-abertos/`) responde 401 (gateway WSO2 + reCAPTCHA, mesmo padrão do Fiscalizando) -> *bloqueado*; Fiscalizando (Tableau), Portal SICOM, CAPMG e SISOP respondem 200 (HTML). Banco de Preços e Lupa de Minas deram timeout.
- **SEJUSP** - CSVs mensais de criminalidade (crimes violentos 2012-2026, homicídios, furtos, roubos, veículos) em seguranca.mg.gov.br - 200 (56 MB no teste).
- **IDE-Sisema (SEMAD)** - GeoNetwork com CSW OGC (200) e busca JSON; geoserver não exposto no host testado; geoportal deu timeout.
- **Portal de Compras MG** - consulta pública Lei 14.133 (SPA), CAGEF/CAFIMP (JSF) - 200; sem API REST pública identificada.
- **Diário Oficial** - novo portal jornalminasgerais.mg.gov.br e acervo DSpace jornal.iof.mg.gov.br: curl local falha (TLS/rede), Jina lê (marcados *bloqueado* para curl).
- Sites WordPress com REST `wp-json` aberto: PMMG, SES, compras.mg.gov.br, SEE (vazio).
- Planilhas de transparência (xlsx) testadas 200: SEE (cronologia, fornecedores, convênios), SES (cronologia, gestores/fiscais), FAPEMIG (projetos, bolsas, instituições).
- Empresas: Copasa, Gasmig, Epamig, Prodemge, MGS, BDMG têm só páginas HTML de transparência; Copasa "dados abertos" está vazia; Cemig não tem portal de dados abertos (só RI).

## 4. O que não foi encontrado / limitações

- **Sites do SISEMA** (SEMAD www.meioambiente.mg.gov.br, IEF, IGAM, FEAM, COPAM, CERH) devolvem 403 para curl (qualquer UA) e certificado com CN inválido para Jina; só IEF foi lido uma vez via Jina. Contatos desses órgãos vêm apenas do diretório mg.gov.br (telefone/endereço) e dos e-mails dos conselhos (assoc@meioambiente.mg.gov.br).
- **IPSEMG e JUCEMG**: handshake TLS aborta no curl (servidor encerra após ClientHello); Jina devolveu snapshot com shadow DOM (IPSEMG) e home (JUCEMG, sem e-mail). CEE/MG: 403 em curl e Jina.
- **Hosts fora do ar/timeout** no dia: utramig.mg.gov.br, metropolitana.mg.gov.br (ARMBH migrou para agenciarmbh.mg.gov.br - coletado), fjp.mg.gov.br com www (sem www funciona - coletado), casacivil/comunicacao/secretariageral/governo.mg.gov.br (timeouts intermitentes; lidos via Jina, sem e-mail publicado).
- Sem site no diretório: CEDCA, CEM, CONEP, CES, CETER, Metrominas, Vice-Governadoria (mantidos com telefone/endereço/e-mail do diretório quando havia).
- Secretarias sem e-mail publicado (SEF, SEPLAG, SEJUSP, SEDESE, SECULT, SEDE, SEAPA, SEGOV, SCC, SECOM, SG, SEMAD), além de CGE, GMG, PMMG, PCMG, CBMMG, ESP, TJMG, Copasa, Cemig, Emater, Fhemig, LEMG: o canal oficial é formulário + OGE (162 / manifestacao.ouvidoriageral.mg.gov.br) e e-SIC (acessoainformacao.mg.gov.br). Rota para obter e-mails institucionais: pedido LAI à OGE/CGE (lista de e-mails de gabinete) ou cruzamento por CNPJ no cadastro institucional.
- Sem API pública: Portal da Transparência MG e Dados Abertos TCE-MG exigem token de gateway (não burlado); Detran, PCMG, PMMG, SEF (NF-e/ICMS) não expõem API aberta.
- Não foram curados os ~2.100 itens de `alvos_MG_unidades.csv` que são unidades internas, prefeituras, câmaras e consórcios; os órgãos-pai de todas as unidades estaduais estão cobertos.

## 5. Rendimento numérico (resumo)

- Órgãos/entidades: 97 | com telefone 92 | com e-mail 60 | com site 90 | com ouvidoria 61 | com endereço 97 | casados PNCP 61/67 CNPJs.
- E-mails coletados: 579 | telefones: 408.
- APIs/portais: 63 | 200 ok 56 | bloqueado 4 | erro 1 | não testado 2.
- Páginas lidas: ~438 (diretório 97 + sites/contatos ~330 + APIs/portais ~120).
