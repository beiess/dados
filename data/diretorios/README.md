# Curadoria de diretórios oficiais — contatos e APIs por órgão (dados publicados)

Contatos oficiais (e-mail, telefone, site, ouvidoria) e catálogo de APIs/portais de dados abertos por órgão, coletados por
agentes de leitura web a partir dos **diretórios oficiais** de cada governo (estrutura organizacional, portais da transparência,
redes de ouvidoria/SIC, sites dos órgãos, portais de dados). **Somente leitura de páginas públicas; nada foi inferido** — cada
linha traz a URL de origem. Carregado no banco (`diretorio_orgaos`, `apis_orgaos`) e usado pelo Painel 16 e pela página 🟡.
Cobertura: **27 UFs + União**. Ver o formato em [`docs/CURADORIA_DIRETORIOS_UF.md`](../../docs/CURADORIA_DIRETORIOS_UF.md).

## Cobertura (30/08/2026)

| UF | Órgãos | com e-mail | com telefone | CNPJs PNCP casados | APIs (respondendo) | UGs estaduais/fed. com e-mail |
|---|--:|--:|--:|--:|--:|--:|
| BR | 891 | 810 (90%) | 849 (95%) | 1004 | 158 (107) | 8619/13833 |
| AC | 47 | 33 (70%) | 29 (61%) | 54 | 16 (10) | 356/428 |
| AL | 71 | 61 (85%) | 63 (88%) | 62 | 33 (30) | 295/302 |
| AM | 92 | 83 (90%) | 82 (89%) | 126 | 30 (28) | 333/570 |
| AP | 70 | 49 (70%) | 38 (54%) | 79 | 16 (15) | 3389/3894 |
| BA | 102 | 71 (69%) | 93 (91%) | 84 | 36 (34) | 2893/2964 |
| CE | 82 | 78 (95%) | 78 (95%) | 80 | 25 (21) | 264/2059 |
| DF | 117 | 103 (88%) | 104 (88%) | 120 | 39 (34) | 397/684 |
| ES | 78 | 72 (92%) | 77 (98%) | 123 | 32 (30) | 233/564 |
| GO | 62 | 61 (98%) | 61 (98%) | 44 | 13 (11) | 495/499 |
| MA | 172 | 84 (48%) | 75 (43%) | 135 | 44 (42) | 3123/3482 |
| MG | 97 | 60 (61%) | 92 (94%) | 61 | 63 (56) | 1743/2213 |
| MS | 50 | 44 (88%) | 38 (76%) | 96 | 10 (9) | 1090/1298 |
| MT | 46 | 24 (52%) | 29 (63%) | 67 | 12 (8) | 128/781 |
| PA | 106 | 82 (77%) | 81 (76%) | 95 | 11 (10) | 790/804 |
| PB | 114 | 79 (69%) | 91 (79%) | 114 | 14 (12) | 628/712 |
| PE | 93 | 78 (83%) | 76 (81%) | 134 | 44 (42) | 1537/1676 |
| PI | 45 | 26 (57%) | 32 (71%) | 47 | 17 (12) | 322/403 |
| PR | 86 | 82 (95%) | 84 (97%) | 79 | 23 (20) | 1044/1065 |
| RJ | 107 | 95 (88%) | 86 (80%) | 85 | 75 (70) | 151/721 |
| RN | 61 | 41 (67%) | 48 (78%) | 68 | 10 (7) | 103/407 |
| RO | 63 | 48 (76%) | 49 (77%) | 59 | 22 (20) | 260/452 |
| RR | 57 | 50 (87%) | 54 (94%) | 52 | 12 (11) | 128/136 |
| RS | 73 | 38 (52%) | 49 (67%) | 96 | 12 (12) | 667/761 |
| SC | 0 | 0 (0%) | 0 (0%) | 0 | 0 (0) | 0/670 |
| SE | 62 | 38 (61%) | 45 (72%) | 65 | 14 (12) | 77/259 |
| SP | 215 | 203 (94%) | 206 (95%) | 233 | 117 (115) | 2301/2562 |
| TO | 54 | 35 (64%) | 29 (53%) | 80 | 17 (15) | 4175/6821 |
| **Total** | **3113** | **2528** | **2638** | **3342** | **915 (793)** | **35541/51020** |

## Arquivos por UF (`data/diretorios/<UF>/`)
- `orgaos.jsonl` — 1 linha por órgão/entidade (nome, sigla, tipo, site, e-mails, telefones, endereço, ouvidoria, redes, CNPJ(s) do PNCP, fontes).
- `apis.jsonl` — 1 linha por API/portal (URL, docs, tipo, autenticação, formato, domínio, status testado).
- `relatorio.md` — fontes, cobertura por tipo, faltas.
