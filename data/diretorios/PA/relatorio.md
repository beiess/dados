# Diretório oficial de órgãos e entidades do Governo do Pará + catálogo de APIs

Data: 2026-08-30. Coleta web (curl; Jina só pontual). Contatos sempre com URL de origem (`fontes`).

Arquivos:
- `~/.claude/jobs/diretorios-uf/PA/orgaos.jsonl` - 106 linhas
- `~/.claude/jobs/diretorios-uf/PA/apis.jsonl` - 11 APIs/portais
- Área de trabalho: `~/.claude/jobs/diretorios-uf/PA/_trabalho/` (98 páginas em orgaos_html/)

## 1. Fontes-mãe
1. **Diretório oficial**: https://www.pa.gov.br/orgao ("Estrutura de Governo") - 98 órgãos, cada um em /orgao?id_orgao=N com **titular (gestor), endereço, telefone, e-mail e site**. Server-side, sem bloqueio - melhor diretório entre as UFs deste lote.
2. Sites dos Poderes/órgãos de controle (ALEPA, TJPA, TJME, TCE-PA, TCM-PA, MPPA, MPC-PA, MPCM-PA, DPE-PA) + CGE/OGE - varridos com scanner (home+contato/ouvidoria).
3. e-SIC (sistemas.pa.gov.br/esic) e Ouvidoria Geral (ouvidoria.pa.gov.br) como canais transversais.

## 2. Cobertura (106 linhas)
E-mail 82 (77%); telefone 81 (76%); site 84; endereço 84; **gestor 98**. CNPJs: **95 de 96** (excluído o CRECI 12ª Região, conselho profissional federal, fora do escopo estadual). Unidades compradoras (804): 795 (99%) sob CNPJ com e-mail/telefone; 787 (98%) com e-mail — as 502 unidades do CNPJ raiz "Estado do Pará" mapeadas ao Gabinete da Governadora (gabinetedogovernador@palacio.pa.gov.br).
Sem contato no diretório: IESP, PCT Guamá, UNACON e 8 hospitais regionais geridos por OS (páginas sem e-mail/tel) e NAC.
Observação: vários e-mails oficiais de secretarias são Gmail (ex.: gabinetecasacivil.pa@gmail.com, semupara@gmail.com) - marcados em `obs` como não institucionais, mas publicados no diretório oficial.

## 3. APIs / portais (11)
- **Portal da Transparência PA**: SPA que consome **13 microserviços REST abertos** `api-*.sistemas.pa.gov.br` (despesas, receitas, servidores, notas de empenho, obras, bens móveis/imóveis, diárias, suprimento de fundos, transferências, planejamento, áreas temáticas, compras) - Spring Boot com **OpenAPI em /v3/api-docs (200 ok, sem chave)**. Achado principal da UF.
- e-SIC (JSF), Ouvidoria Geral, TCE-PA/TCM-PA/ALEPA/TJPA portais de transparência.
- Portal de dados abertos (dados.pa.gov.br) linkado mas **403/DNS** - indisponível externamente.

## 4. Não encontrado / pendências
- dados.pa.gov.br inacessível (bloqueio/DNS) - rota: e-SIC ou usar as APIs da transparência.
- TCE-PA não expõe portal de dados abertos dedicado (só transparência HTML).
- Justiça Militar (TJME) sem contatos no HTML lido (site institucional JS).
