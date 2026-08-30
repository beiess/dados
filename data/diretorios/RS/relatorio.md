# Diretório oficial de órgãos e entidades do Governo do RS + catálogo de APIs

Data: 2026-08-30. Coleta web (curl + Jina Reader), somente páginas públicas; contatos sempre com URL de origem (`fontes`).

Arquivos:
- `~/.claude/jobs/diretorios-uf/RS/orgaos.jsonl` - 73 linhas
- `~/.claude/jobs/diretorios-uf/RS/apis.jsonl` - 12 APIs/portais testados
- Área de trabalho: `~/.claude/jobs/diretorios-uf/RS/_trabalho/`

## 1. Fontes-mãe
1. **estado.rs.gov.br** (matriz PROCERGS): /institucional e /secretarias. A página /secretarias carrega a lista via JS (não veio no HTML e o Jina deu timeout); a estrutura oficial é a da **Lei 15.934/2023**. Diretório reconstruído pelos subdomínios-padrão *.rs.gov.br (todas as secretarias/órgãos usam a matriz PROCERGS com /inicial).
2. Sites de cada órgão (home + /contato, /fale-conosco, /ouvidoria): 71 sites varridos; 8 exigiram Jina (SPGG, SEDES, CBM, Susepe, Cientec, Piratini, IGTF, Emater) e mesmo assim alguns não publicam contato na home.
3. **Ouvidoria-Geral** (ouvidoriageral.rs.gov.br): canal único de manifestações do Executivo (0800 541 6136, ouvidoriageral@casacivil.rs.gov.br); não há página-diretório de ouvidorias setoriais com contatos (diferente de PE/PB).
4. Poderes: ALRS (ww4.al.rs.gov.br), TJRS (tjrs.jus.br/novo), TCE-RS (tcers.tc.br - raiz tce.rs.gov.br dá 403), MPRS, DPE-RS.

Filtro: contatos genéricos do rodapé matriz (ouvidoriageral@casacivil, 0800 541 6136, (51) 3210-4100) mantidos só nas linhas GOVRS/OGE.

## 2. Cobertura (73 linhas)
E-mail 38 (52%); telefone 49 (67%); site 72; endereço 13. CNPJs da lista-alvo casados: **96 de 96** (a "Secretaria da Administração e dos RH" extinta foi mapeada à SPGG). Unidades compradoras (761): 699 (92%) sob CNPJ com e-mail/telefone; 667 (88%) com e-mail — inclui as 468 unidades do CNPJ raiz associadas à linha GOVRS/OGE.
Sem contato publicado (home institucional matriz sem e-mail/tel): CM, SPGG, SEDES, SME, SEDEC, SAAM, SECOM, CAGE, CBMRS, CIENTEC, PIRATINI, IGTF, SUSEPE, UERGS, FPERS (aviso eleitoral), OSPA (404), Banrisul/Emater (institucional sem contato direto).
Destaques: SES publica a rede completa de ouvidorias do SUS (19 e-mails/45 tel das CRS); SEMA/FEPAM listam dezenas de setoriais; FASE 56 telefones; TCE-RS 20 e-mails.

## 3. APIs / portais (12 testados)
- **dados.rs.gov.br** (CKAN): 404 datasets, 11 orgs (SPGG/DEE 325). 200 ok.
- **dados.tce.rs.gov.br** (CKAN): **73.438 datasets** - balancetes/licitações por município/ano. 200 ok.
- Transparência RS (Umbraco): /dados-abertos (CSVs), ApiDefesaCivil, ViewApi (docs de API). 200 ok.
- dados.mprs.mp.br: home 200, mas /api/3 e /dataset 404 (não é CKAN padrão).
- ALRS transparencia.al.rs.gov.br, sistema de proposições; TJRS portal novo; Central de Informação RS.

## 4. Não encontrado / pendências
- Lista oficial renderizada de secretarias (JS) - contornado via Lei 15.934/2023 + subdomínios.
- Endereços físicos da maioria (matriz não publica na home; ficam em /fale-conosco de alguns).
- APIs REST do Portal da Transparência: documentadas em ViewApi mas endpoints exatos exigem navegação JS.
