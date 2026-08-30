# Diretório oficial de órgãos e entidades do Governo do Estado do Amapá + catálogo de APIs

Data da coleta: 2026-08-30. Agente: coleta web (curl + Jina Reader). Somente páginas públicas; todo contato tem URL de origem.

Arquivos (JSON Lines, UTF-8):
- `~/.claude/jobs/diretorios-uf/AP/orgaos.jsonl` — 70 órgãos/entidades
- `~/.claude/jobs/diretorios-uf/AP/apis.jsonl` — 16 portais/APIs testados
- Trabalho em `~/.claude/jobs/diretorios-uf/AP/_trabalho/` (rede_ouv_contatos.json, crawl_in/out.json). Nada no Google Drive.

## 1. Fontes-mãe
- **https://cge.portal.ap.gov.br/pagina/rede-de-ouvidorias/rede-de-ouvidoria-estadual** (CGE-AP, "Rede Estadual de Ouvidoria 2025") — ouvidor(a), endereço+CEP, horário, telefone, e-mail e site por órgão (CGE, SEJUSP, AFAP, SEED, CAESA, IPEM, TCE, IAPEN, HEMOAP, CREAP, SESA, SEPM, CBM, DETRAN, AMPREV, SIAC, SEAS, SEAD, SECBEA, Polícia Científica, IEPA, SEPLAN, JUCAP…). Vários e-mails oficiais publicados são @gmail/@hotmail — mantidos com nota.
- **https://amapa.gov.br/orgaos** — diretório do portal (Laravel/Livewire; lista via JS). Sites oficiais dos órgãos seguem o padrão **<sigla>.portal.ap.gov.br** (23 confirmados) ou domínio antigo <sigla>.ap.gov.br (sead, detran, prodap, hemoap, amprev, sepi, afap, caesa, ipem, iepa, bombeiros).
- Poderes: ALAP, TCE-AP, TJAP, MPAP, DPE-AP.

## 2. Cobertura — 70 órgãos/entidades
Site 57 · E-mail 49 · Telefone 38 · Endereço 38 · Ouvidor(a) nominal 28 · Ouvidoria URL 46 · e-SIC 42 · Dados abertos/transparência 47 · Redes sociais 42.
CNPJs da lista-alvo: **79 de 81 casados**. Os 2 restantes NÃO são do AP (linhas fora de escopo na lista PNCP: "Assembleia Legislativa de Roraima" e "Corpo de Bombeiros do Piauí"). 13 registros mínimos criados só com CNPJ+nome (SETRAP, FUNDESA, SEMIN, SEPESCA, SDC, GASAP, Fundação Marabaixo, GSI, SECOM, SECOMPLA, SEMOB, SDR, PESCAP em liquidação) — sem contato publicado localizado. Fundos anexados ao gestor: FUNSEP→SEJUSP, Fundo PGE→PGE, FEDP→DPE, FERMA+Rec.Hídricos→SEMA, Reequipamento Policial→Polícia Civil. O CNPJ 00394577000125 "ESTADO DO AMAPA" (milhares de unidades — escolas, hospitais, delegacias em `alvos_AP_unidades.csv`) casa com o registro do portal do Governo; contatos dos órgãos-pai valem para as unidades.

## 3. Catálogo de APIs (16)
- **Portal da Transparência (www.transparencia.ap.gov.br): acesso intermitente** — falhou em várias tentativas (https sem resposta, Jina CONNECTION_RESET) mas respondeu 200 no teste final; monitorar.
- e-SIC próprio (esic.ap.gov.br, http), SIGA (compras JSF), AP Digital (carta de serviços), diretório amapa.gov.br.
- TCE-AP: site com backend REST /api/v1 (links assinados de atas/pautas), consulta de decisões, contas de governo.
- ALAP: transparência com consultas de remuneração/licitações/contratos + página "dados abertos". TJAP: portal transparência + app licitações. MPAP: transparencia.mpap.mp.br (o caminho no domínio principal dá 403). DPE-AP: transparência não localizada (404).
- Não há CKAN/portal de dados abertos estadual.

## 4. Faltas/limitações
- transparencia.ap.gov.br instável (várias falhas de conexão durante a coleta; respondeu só no fim) — recoletar contatos/downloads quando estável.
- Registros mínimos (13) sem contato: retomar via LAI/e-SIC ou quando o portal voltar.
- Lista Livewire de órgãos não renderiza sem JS; sites foram inferidos por padrão de subdomínio confirmado um a um.
