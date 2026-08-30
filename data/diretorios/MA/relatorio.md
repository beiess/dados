# Diretório oficial de órgãos e entidades do Governo do Maranhão + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl + Jina Reader). Somente páginas públicas; nenhum e-mail/telefone inventado - todo contato tem URL de origem (`fonte_url`/`fontes`).

Arquivos gerados (JSON Lines):
- `~/.claude/jobs/diretorios-uf/MA/orgaos.jsonl` - 173 linhas (órgãos/entidades, fundos/UGs, poderes autônomos e unidades PM/CBM com CNPJ próprio no PNCP)
- `~/.claude/jobs/diretorios-uf/MA/apis.jsonl` - 44 APIs/portais testados com 1 GET real
- `~/.claude/jobs/diretorios-uf/MA/relatorio.md` - este relatório
- Área de trabalho (páginas baixadas, scripts, crawl bruto): `~/.claude/jobs/diretorios-uf/MA/_trabalho/`

## 1. Fontes-mãe (diretórios oficiais)

1. **Portal do Governo do Maranhão - "Órgãos do Governo"**: https://www.ma.gov.br/todas-as-secretarias?tab=all (SPA Next.js). A lista e o detalhe vêm de uma API aberta do próprio portal: `https://www.ma.gov.br/api/admin/organs?page_size=100` (73 órgãos) e `https://www.ma.gov.br/api/admin/organs/<id>` (campos `organ_contact` = telefone/e-mail/WhatsApp/redes, `organ_address`, `organ_manager_data` = gestor, `portal_url`). 35 dos 73 têm contato e 38 têm endereço cadastrados na API.
2. **Portal da Transparência do MA - Informações Institucionais**: https://www.transparencia.ma.gov.br/app/v2/informacoes_institucionais - 64 cards (Governadoria, Vice, Gabinete, secretarias, autarquias, fundações, empresas, universidades) com **gestor, cargo, endereço, horário, site, e-mail e telefone do órgão** e competências. Foi a fonte mais rica de contatos.
3. **Portal da Transparência - Unidades Gestoras** (JSON embutido em https://www.transparencia.ma.gov.br/app/v2/fique_por_dentro/treeMapUG): 105 UGs SIAFEM (código + nome) - usada para incluir fundos e unidades (FES, FUNAT, FEMA, FEUC, FUNCON, CCL, ARSEP, EMARHP, Fundação Nice Lobão/CINTRA, Colégios Militares, CFAP, APM Gonçalves Dias, BPA, CPTUR...).
4. Sites oficiais de cada órgão (home + páginas de contato/ouvidoria), sites dos Poderes (ALEMA, TJMA, TCE-MA, MPMA, DPE-MA) e páginas de unidades: PMMA (https://pm.ssp.ma.gov.br/contatos/ - 28 e-mails setoriais), CBMMA (https://cbm.ssp.ma.gov.br/unidades-bm/ - 43 páginas de unidades com e-mail @cbm.ma.gov.br), PCMA (https://www.policiacivil.ma.gov.br/delegacias-do-interior/ - 217 e-mails de delegacias regionais/municipais).
5. Ouvidoria e e-SIC únicos do Executivo: e-OUV https://www.ouvidorias.ma.gov.br/ (ouvidoria@stc.ma.gov.br / sic@stc.ma.gov.br) e e-SIC https://www.e-sic.ma.gov.br/ - preenchidos como `ouvidoria_url`/`esic_url` quando o órgão não tem ouvidoria própria.

Observação importante: **22 sites de órgãos estavam "Suspensão Temporária | Período Eleitoral 2026"** na data da coleta (AGEM, AGEMSUL, Casa Civil, CONSEA, FUNAC, ITERMA, MOB, SEAM, SEAP, SECAP, SEDEL, SEDEPE, SEDES, SEEJUV, SEG, SEGOV, SEINC, SEMAG, SEMU, SEPA, SETRES e outros); para esses, os contatos vieram do diretório oficial (API) e da Transparência (marcado em `obs`). SES está "em manutenção" (wp-json responde). Não respondem: pm.ma.gov.br, ccl.ma.gov.br, arsep/arsema, cge, nasp, emarhp, cmt.ma.gov.br, IMESC (HTTP 503), app.tcema.tc.br (503).

## 2. Cobertura - órgãos (173 linhas)

| Campo | Linhas com dado |
|---|---|
| Ouvidoria (URL) | 173 (100%) - própria ou e-OUV central |
| Site | 129 (75%) |
| E-mail | 84 (49%) - 457 e-mails, todos com URL de origem |
| Endereço | 81 (47%) |
| Telefone | 75 (43%) - 313 números |
| Responsável/gestor | 66 |
| Redes sociais | 48 |
| Fale conosco (URL) | 22 |
| Casadas com CNPJ da lista-alvo (`cnpjs_pncp`) | 121 linhas -> **135 dos 136 CNPJs** de `alvos_MA.csv` |

Rendimento por tipo (linhas / com e-mail / com telefone / com site / com endereço):
- secretaria 38 / 35 / 33 / 35 / 36 - quase todas com e-mail de gabinete (muitos @gmail.com institucionais, publicados no diretório oficial e na Transparência)
- autarquia 18 / 17 / 16 / 17 / 17
- empresa 7 / 4 / 6 / 6 / 5 (CAEMA e EMAP sem e-mail publicado; GASMAR, EMSERH, MAPA, Investe MA com)
- fundação 5 / 4 / 4 / 4 / 4
- fundo 20 / 0 / 0 / 1 / 0 - fundos não têm contato próprio; herdam do órgão gestor (`orgao_pai`)
- outro 81 / 20 / 12 / 62 / 15 - inclui 29 batalhões/companhias da PMMA e 13 unidades do CBMMA com CNPJ próprio no PNCP; batalhões da PM não têm contato individual publicado (linha traz `obs` com o caminho: contatos setoriais em pm.ssp.ma.gov.br/contatos)
- poderes: ALEMA (ouvidoria@al.ma.leg.br), TJMA (telejudiciario@tjma.jus.br, 0800 707 1581), TCE-MA (contato@tcema.tc.br), MPMA (ouvidoria@mpma.mp.br), DPE-MA (só telefones)

Cobertura das **3.482 unidades compradoras** da lista-alvo: 3.185 (91%) estão sob um CNPJ cuja linha tem e-mail ou telefone; 3.065 (88%) com e-mail. As 435 unidades da SSP, 371 do CNPJ raiz "Estado do Maranhão", 184 da PMMA, 161 da ALEMA, 132 da SEDUC e 113 da SEFAZ ficam cobertas pelo contato do órgão-mãe (as páginas de unidades não publicam e-mail por unidade, exceto CBM e delegacias da PC).

Não casado: 23829292000175 "1ª Companhia Independente de Bombeiros Militar" (a página da 1ª CIEBM não tem e-mail próprio além do geral; ficou sem CNPJ na linha).

## 3. APIs e portais (44 linhas em apis.jsonl)

Status dos testes: 42 "200 ok", 2 "erro" (IMESC 503; API Swagger do TCE-MA em app.tcema.tc.br 503).

Destaques:
- **API do diretório oficial** (`/api/admin/organs`, `/api/admin/organs/<id>`, `/api/admin/featured-services`) - JSON aberto, sem chave.
- **dados.ma.gov.br (DKAN)** - catálogo DCAT em `?q=data.json` (37 conjuntos): Despesa, Folha de Pagamento (nominal, com CPF) e Receita 2019-2026 em CSV mensal (`;`), Balanços, LOA/LDO/PPA, RREO/RGF, inventário patrimonial, Juros Zero (SEINC). Não há API CKAN (`/api/3` = 404).
- **Portal da Transparência (Laravel)** - módulos HTML em `/app/v2/*` e endpoints AJAX JSON (ex.: `/app/v2/despesas/carregar-dropdowns-ajax` 200; `fornecedoresContratantes` é POST). `treeMapUG` traz JSON das 105 UGs. Informações Institucionais = diretório com contatos.
- e-SIC e e-OUV (ASP.NET), Portal de Compras (SIGA, sem API), Portal do Servidor (login), DOEMA (sem API), LEGISLA/STC.
- WordPress REST `wp-json` aberto em SES, SEDUC, SSP, PCMA, IPREV, AGED, FAPEMA, PROCON, UEMASUL.
- Poderes: ALEMA transparência (JSF, sem dados abertos), TJMA índice Res. CNJ 215 (sem API própria; DataJud/CNJ), TCE-MA transparência Joomla + API Swagger fora do ar, MPMA transparência, DPE transparência.
- Unidades: CBMMA/unidades-bm e PMMA/contatos (páginas HTML com e-mails).

## 4. O que não foi encontrado / limitações
- Sem e-mail publicado: CAEMA (só telefones e formulário), EMAP/Porto do Itaqui, CBMMA usa e-mails @cbm.ma.gov.br por unidade (ok), DETRAN (gabinete@detran.ma.gov.br via diretório), DPE-MA (só telefones), SSP (gabsspma@gmail.com na Transparência).
- Batalhões/companhias da PMMA (29 CNPJs no PNCP) e Colégios Militares: nenhuma página com contato individual; fundos (20) idem.
- Endereços dos Poderes foram preenchidos a partir do site institucional (não extraídos automaticamente) - conferir antes de uso postal.
- Vários e-mails de gabinete são @gmail/@hotmail publicados oficialmente (diretório e Transparência) - mantidos como estão, com origem.
