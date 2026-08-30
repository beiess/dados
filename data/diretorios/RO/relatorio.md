# Diretório oficial de órgãos e entidades - Rondônia (RO) + catálogo de APIs

Data da coleta: 2026-08-30. Coleta por curl (UA navegador) + fallback Jina; só páginas públicas; todo e-mail/telefone tem URL de origem. Esfera: estadual.

Arquivos:
- `~/.claude/jobs/diretorios-uf/RO/orgaos.jsonl` - 63 linhas (53 unidades da Estrutura Organizacional da transparência + 5 órgãos do menu do portal + TJRO/ALE-RO/TCE-RO/MPRO/DPE-RO + CNPJ raiz)
- `~/.claude/jobs/diretorios-uf/RO/apis.jsonl` - 22 APIs/portais testados com GET (ou POST) real
- Área de trabalho: `~/.claude/jobs/diretorios-uf/RO/_trabalho/` (contatos_ugs.json, dir_final.json, manual.json, crawl.jsonl)

## 1. Fontes
- **https://transparencia.ro.gov.br/institucional/estrutura-organizacional** (CGE/SETIC): diretório oficial (LC 965/2017). Os cartões chamam `POST /Institucional/ContatosUnidadeGestora` com `UnidadeGestoraID` - devolve titular, endereço, e-mail corporativo, telefone e horário. Coletadas as 33 unidades da administração direta + 20 da indireta (53 POSTs).
- https://rondonia.ro.gov.br/ (menu "Órgãos" com 56 sites em /<sigla>/) - crawl de contato/ouvidoria em cada site
- https://transparencia.ro.gov.br/institucional/poderes, /home/contatos; https://rondonia.ro.gov.br/ouvidoria/
- Poderes: tjro.jus.br, al.ro.leg.br, tcero.tc.br, mpro.mp.br, defensoria.ro.def.br

## 2. Cobertura - órgãos (63 linhas)
| Campo | Linhas |
|---|---|
| Site | 60 |
| E-mail | 48 (255 e-mails) |
| Telefone | 49 (648 números) |
| Endereço | 53 |
| Responsável | 52 |
| Ouvidoria | 58 |
| Fale conosco | 56 |
| Redes sociais | 57 |
| Com CNPJ da lista-alvo | 49 - 59/59 CNPJs de `alvos_RO.csv` cobertos |

Tipos: {'outro': 23, 'secretaria': 15, 'autarquia': 13, 'empresa': 4, 'fundacao': 4, 'tribunal': 1, 'legislativo': 1, 'tce': 1, 'mp': 1}. Fundos mapeados ao gestor (F.E.Saúde/Hosp. Cosme e Damião->SESAU; FESP->SESDEC; FIDER->SEDEC; FUMORPGE->PGE; F.Reequip.Policial->PC; F.Modern.PM->PM; FRBL->MPRO; FUNDARON->ALE-RO; Superint. Juventude->SEJUCEL).
Sem e-mail publicado: Casa Civil, Casa Militar, Governadoria, SECOM, SI, Vice Governadoria, IDARON, IESPRO, PROCON-RO, COTES, DIOF, DRPC, ITERON, MP-RO, GOV-RO.

## 3. APIs (22 linhas) - status {'200 ok': 20, 'erro': 2}
- **API Públicas CGE-RO** (`transparencia.api.ro.gov.br`, Swagger/OpenAPI): 9 endpoints REST sem chave - despesas (6,1 mi reg.), receitas, remuneração-servidor, contratos, convênios, pagamento-fornecedor (exige DataInicial+DataFinal), fornecedores-impedidos (+histórico), dotação inicial. PageSize máx 100. Docs: wiki.cge.ro.gov.br.
- **CKAN dados.ro.gov.br**: 14 datasets/9 orgs; resources apontam para a API CGE.
- Transparência RO: POST ContatosUnidadeGestora (contatos oficiais por UG); obras.transparencia.ro.gov.br; e-SIC.
- TCE-RO: Portal do Cidadão, SIGAP, transparencia.tcero.tc.br (HTML). ALE-RO: SAPL API REST 200. TJRO: RH Transparente. MPRO: transparencia.mpro.mp.br.

## 4. Faltas
- Casa Civil, Casa Militar, Governadoria, SECOM, SI, Vice-Governadoria: transparência não publica e-mail/telefone (campos vazios); sites com formulário.
- MPRO: páginas de contato não expõem e-mail em texto (formulário); ALE-RO só protocologeral@ale.ro.gov.br.
- www2.sefin.ro.gov.br e ouvidoria.sistemas.ro.gov.br: http antigo sem resposta no teste.
