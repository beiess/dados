# Diretório oficial de órgãos e entidades - Goiás (GO) + catálogo de APIs

Data da coleta: 2026-08-30. curl (UA navegador) + fallback Jina; só páginas públicas; contatos com URL de origem. Esfera: estadual.

Arquivos:
- `~/.claude/jobs/diretorios-uf/GO/orgaos.jsonl` - 62 linhas (55 do diretório oficial + IPASGO + TJGO/ALEGO/TCE-GO/TCM-GO/MPGO/DPE-GO)
- `~/.claude/jobs/diretorios-uf/GO/apis.jsonl` - 13 APIs/portais testados
- Área de trabalho: `~/.claude/jobs/diretorios-uf/GO/_trabalho/` (dir_go.json, dir_final.json, manual.json, crawl.jsonl)

## 1. Fontes
- **Diretório oficial** no portal goias.gov.br (Secretaria-Geral de Governo), 3 páginas com titular, endereço, e-mail, telefone e site por órgão:
  - https://goias.gov.br/administracao-direta/ (32 entradas, inclui Governador/Vice/Governadoria)
  - https://goias.gov.br/autarquias-e-fundacoes/ (10)
  - https://goias.gov.br/empresas-publicas/ (13)
- https://www.transparencia.go.gov.br/orgaos/ (lista de órgãos da CGE - usada para IPASGO)
- Crawl dos sites (home + contato/ouvidoria) de cada órgão + Poderes (tjgo.jus.br, portal.al.go.leg.br, portal.tce.go.gov.br, tcmgo.tc.br, mpgo.mp.br, defensoria.go.def.br)

## 2. Cobertura (62 linhas)
| Campo | Linhas |
|---|---|
| Site | 59 |
| E-mail | 61 (577 e-mails; ALEGO publica lista completa com 149 e-mails setoriais) |
| Telefone | 61 (822 números) |
| Endereço | 55 |
| Responsável/titular | 54 |
| Ouvidoria | 55 |
| Fale conosco | 55 |
| Com CNPJ-alvo | 40 - 44/47 CNPJs de `alvos_GO.csv` |

Tipos: {'outro': 13, 'secretaria': 20, 'autarquia': 11, 'empresa': 11, 'fundacao': 2, 'tribunal': 1, 'legislativo': 1, 'tce': 2, 'mp': 1}.
Não casados (3): Agência Goiana de Desenvolvimento Regional (extinta), Secretaria de Estado do Trabalho (extinta; funções absorvidas), Sindicato das Agências de Propaganda (entidade privada, fora do escopo).
Sem e-mail: IPASGO.

## 3. APIs (13) - status {'200 ok': 11, 'erro': 1, 'bloqueado': 1}
- **CKAN dadosabertos.go.gov.br**: 444 datasets / 25 organizações (1 por órgão); **DataStore ativo** (datastore_search e datastore_search_sql) - testado com resource real da SES (200). Docs em transparencia.go.gov.br/api-de-dados-abertos.
- **TCE-GO**: CKAN próprio dadosabertos.tce.go.gov.br (200). **TCM-GO**: api.tcm.go.gov.br (REST, 200).
- CGE: painéis LAI (lai.php por órgão) e API de relatório da Ouvidoria-Geral (JSON 200).
- ALEGO transparencia.al.go.leg.br 200; MPGO /transparencia 200; Diário Oficial diariooficial.abc.go.gov.br 200.
- TJGO: 403 para curl (WAF) - rota LAI/DataJud como alternativa.

## 4. Faltas
- goias.gov.br/orgaos-e-entidades/ dá 404 (o diretório real são as 3 páginas por categoria).
- compras.go.gov.br / comprasnet.go.gov.br sem DNS no teste.
- Governador/Primeira-dama/Governadoria compartilham o mesmo contato de agenda (páginas oficiais).
