# Curadoria de diretórios oficiais — contatos e APIs por órgão (dados publicados)

Dados coletados por agentes de leitura web a partir dos **diretórios oficiais** de cada governo (estrutura organizacional,
portais da transparência, redes de ouvidoria/SIC, sites dos órgãos) e dos portais de dados abertos. **Somente leitura de páginas
públicas; nenhum e-mail/telefone foi inferido** — cada linha traz a URL de origem (`fonte_url`, `fontes_emails`, `fontes_telefones`).
Formato de saída: ver [`docs/CURADORIA_DIRETORIOS_UF.md`](../../docs/CURADORIA_DIRETORIOS_UF.md). Carregado no banco pelas
tabelas `diretorio_orgaos`, `apis_orgaos` (+ `_cnpj`) e usado pelo Painel 16 (Unidades Gestoras) e pela página 🟡 (APIs).

## Cobertura publicada (30/08/2026)

| UF | Órgãos no diretório | com e-mail | com telefone | com site | CNPJs do PNCP casados | APIs catalogadas (respondendo) | Unidades compradoras do PNCP com e-mail | com telefone |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| União (federal) (BR) | 891 | 810 (90%) | 849 (95%) | 754 | 1004 | 158 (107) | 8581 / 13833 (62%) | 11985 |
| Minas Gerais (MG) | 97 | 60 (61%) | 92 (94%) | 90 | 61 | 63 (56) | 1743 / 2213 (78%) | 2213 |
| São Paulo (SP) | 215 | 203 (94%) | 206 (95%) | 212 | 233 | 117 (115) | 2302 / 2562 (89%) | 2557 |
| Maranhão (MA) | 172 | 84 (48%) | 75 (43%) | 129 | 135 | 44 (42) | 3123 / 3482 (89%) | 3266 |
| Pernambuco (PE) | 93 | 78 (83%) | 76 (81%) | 85 | 134 | 44 (42) | 1537 / 1676 (91%) | 1655 |
| Distrito Federal (DF) | 117 | 103 (88%) | 104 (88%) | 107 | 120 | 39 (34) | 388 / 684 (56%) | 520 |
| Espírito Santo (ES) | 78 | 72 (92%) | 77 (98%) | 75 | 123 | 32 (30) | 233 / 564 (41%) | 564 |
| Amazonas (AM) | 92 | 83 (90%) | 82 (89%) | 85 | 126 | 30 (28) | 333 / 570 (58%) | 570 |

**Totais:** 1755 órgãos/entidades · 1936 CNPJs do PNCP casados · 527 APIs (454 respondendo a um GET real).

## Arquivos por UF (`data/diretorios/<UF>/`)
- `orgaos.jsonl` — 1 linha por órgão/entidade: nome, sigla, tipo, site, e-mails, telefones, endereço, ouvidoria, fale-conosco, redes, CNPJ(s) do PNCP, fontes.
- `apis.jsonl` — 1 linha por API/portal de dados: URL, docs, tipo (CKAN/REST/OpenAPI/CSV/portal), autenticação, formato, domínio, status testado.
- `relatorio.md` — fontes usadas, cobertura por tipo de órgão, faltas e limitações.

Estados em curso (lote 3): PB, RS, MS, PA, SC, RJ, BA, TO, AP, PR, CE, PI, RN, MT, SE, AL, RO, AC, RR, GO.
