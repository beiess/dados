# Diretório de órgãos e entidades - Acre (AC) + catálogo de APIs

Data da coleta: 2026-08-30. curl (UA navegador) + fallback Jina; só páginas públicas; contatos sempre com URL de origem. Esfera: estadual.

**Limitação central**: o diretório oficial "Órgãos e Entidades" (https://estado.ac.gov.br/orgao-entidades/) e o próprio portal estado.ac.gov.br estavam FORA DO AR durante toda a coleta (timeout também via Jina; Wayback Machine 503). A lista foi reconstituída a partir da lista-alvo do PNCP + descoberta DNS de sites *.ac.gov.br (46 sites verificados) + crawl de contato/ouvidoria em cada site. Recoletar o diretório oficial quando o portal voltar.

Arquivos:
- `~/.claude/jobs/diretorios-uf/AC/orgaos.jsonl` - 47 linhas
- `~/.claude/jobs/diretorios-uf/AC/apis.jsonl` - 16 APIs/portais testados
- Área de trabalho: `~/.claude/jobs/diretorios-uf/AC/_trabalho/`

## 1. Fontes
- Sites oficiais *.ac.gov.br de cada órgão (home + contato/ouvidoria) - crawl com 2 passadas
- https://transparencia.ac.gov.br/ (CGE): rotas JSON (servidores/orgaos etc.), rodapé com endereço da CGE
- https://www.ac.gov.br/ouvidoria (Ouvidoria-Geral/CGE) e https://www.ac.gov.br/catalogo-de-api
- Poderes: tjac.jus.br, tceac.tc.br, mpac.mp.br, defensoria (ac.def.br); al.ac.leg.br fora do ar

## 2. Cobertura (47 linhas)
| Campo | Linhas |
|---|---|
| Site | 46 |
| E-mail | 33 (166 e-mails) |
| Telefone | 29 (106 números) |
| Endereço | 1 (sites do AC quase não publicam endereço em texto) |
| Ouvidoria | 31 |
| Fale conosco | 23 |
| Redes sociais | 26 |
| Com CNPJ-alvo | 45 - 54/54 CNPJs cobertos |

Tipos: {'secretaria': 18, 'autarquia': 13, 'outro': 9, 'fundacao': 3, 'mp': 1, 'tribunal': 1, 'legislativo': 1, 'tce': 1}. Extintos/incorporados mapeados: DEPASA e SEDUR->SEINFRA; FUNDAC e F. Elias Mansour->SECOM; IMA->SEMA; SEEL->SEE; FEDC->PROCON; Gab. Militar->raiz.
Sem e-mail publicado/da fonte: SEPLAG-AC, SEPA, PMAC, Acreprevidência, CBMAC, SEINFRA-AC, FUNDHACRE, PROCON-AC, SEET, ALEAC, PCAC, SECT, Agência de Negócios do Acre (Anac), IPEM-AC.
Sites fora do ar no teste: ALEAC, CBMAC, PMAC, SECT, SEET, SEINFRA, SEPA, SEPLAG (000), PROCON (502).

## 3. APIs (16) - status {'200 ok': 10, 'erro': 6}
- **Catálogo de APIs do Estado** (www.ac.gov.br/catalogo-de-api): ~40 APIs (SEAD documentoSei: unidades/órgãos/processos; licitações: editais, avisos, esclarecimentos; patrimônio: bens, movimentações; almoxarifado; servidores: dados funcionais, férias, licenças, afastamentos; serviços digitais). Docs renderizadas via JS; endpoint testado devolveu 404 sem parâmetros - anotar como a documentar.
- **Transparência AC (Laravel/Inertia)**: rotas JSON GET /servidores/orgaos e /despesas/orgaos (200); consultas /conteudo/*/listar são POST (405 no GET). 169 rotas Ziggy embutidas na página.
- **CKAN dados.ac.gov.br**: 20 datasets (socioeconômicos).
- e-SIC, Diário Oficial, LEGIS 200. TJAC transparência 200; MPAC transparencia.mpac.mp.br 200; TCE-AC no site; LICON TCE fora do ar no teste.
