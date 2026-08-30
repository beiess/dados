# Diretório oficial de órgãos e entidades do Governo da Paraíba + catálogo de APIs

Data: 2026-08-30. Coleta web (curl + Jina Reader), somente páginas públicas; todo e-mail/telefone tem URL de origem (`fonte_url`/`fontes`).

Arquivos:
- `~/.claude/jobs/diretorios-uf/PB/orgaos.jsonl` - 115 linhas
- `~/.claude/jobs/diretorios-uf/PB/apis.jsonl` - 14 APIs/portais (cada uma com 1 GET real)
- Área de trabalho: `~/.claude/jobs/diretorios-uf/PB/_trabalho/` (HTML baixado, scan_pb.jsonl, build_pb.py)

## 1. Fontes-mãe
1. **Barra de identidade do portal paraiba.pb.gov.br** (Plone govbr, presente em todos os sites *.pb.gov.br): menus "Secretarias" (28 diretas, links /diretas/...) e "Indiretas" (48 entidades com site próprio). É o diretório oficial. **Limitação**: paraiba.pb.gov.br passa a exigir CAPTCHA (Radware "Qual é o código exibido na imagem?") após poucas requisições - as páginas /diretas/* e /contatos ficaram inacessíveis (curl e r.jina.ai). Os contatos das secretarias vieram da fonte 2.
2. **Rede de Ouvidorias da OGE**: https://ouvidoria.pb.gov.br/rede-de-ouvidorias (55 ouvidorias: endereço, e-mail, telefone) + https://ouvidoria.pb.gov.br/rede-de-ouvidorias/rede-de-ouvidorias-da-saude (27 hospitais/GRS/Lacen/Hemocentro/ESP). Principal fonte de contatos.
3. Sites próprios das indiretas (home + /contato, /ouvidoria, /fale-conosco, /sic) e dos Poderes: ALPB, TJPB (403 → Jina), TCE-PB, MPPB, DPE-PB (defensoria.pb.def.br; o host www. não resolve).
4. SIC-PB (https://sic.pb.gov.br/) - portal único de LAI do Executivo; não lista SICs por órgão.

Filtro aplicado: contatos genéricos do rodapé Plone (ouvidoriageral@casacivil.pb.gov.br, transparencia@paraiba.pb.gov.br, (83) 3214-7221/3214-2508/3315-6800) foram removidos das linhas de cada órgão e mantidos apenas na linha do Governo/OGE.

## 2. Cobertura (115 linhas)
| Campo | Linhas |
|---|---|
| E-mail | 80 (70%) - 354 e-mails |
| Telefone | 91 (79%) - 477 números |
| Site | 76 |
| Endereço | 86 |
| Ouvidoria (URL) | 115 (própria ou rede OGE) |
| Casadas com CNPJ da lista-alvo | **114 de 114 CNPJs** de `alvos_PB.csv` |

Por tipo (linhas / e-mail / telefone / site / endereço): secretaria 24/14/14/24/14; autarquia 17/12/16/17/16; empresa 11/8/11/11/9; fundação 9/5/6/8/6; outro (hospitais, GRS, polícias, PGE, programas) 50/38/41/13/38; ALPB 1/1/1; TJPB só telefone (83) 3219-9400 + endereço; TCE-PB, MPPB, DPE-PB com e-mail.

Unidades compradoras (`alvos_PB_unidades.csv`, 709): 657 (93%) sob CNPJ com e-mail ou telefone; 622 (88%) com e-mail. As 276+ unidades do CNPJ raiz "Estado da Paraíba" (varas, ALPB, agências) foram associadas à linha GOVPB (OGE: ouvidoriageral@casacivil.pb.gov.br, 0800 021 2310).

Secretarias sem e-mail/telefone (site bloqueado por CAPTCHA e ausentes na rede de ouvidorias): SEAD, SEAFDS, SECOM, SEDAP, SEDAM, SEGOV, SEJEL, SEPLAG, SERI, Casa Civil (usa OGE). Entidades sem contato: IDEME, CENDAC, CODATA (só rodapé genérico), PROCASE, PAP, FUNECAP, LIFESA (só telefone), Rádio Tabajara (herda EPC).

## 3. APIs / portais (14)
- CKAN **dados.pb.gov.br** (200): 7 datasets reais (despesas/compras/convênios/orçamento da CGE, receitas SEFAZ, remuneração SEAD, saúde) e ~43 pacotes-lixo de teste de segurança ("audit-ssrf", "test-pwn") - anotar para o curador.
- Portal da Transparência (SPA React) - backend /api 403 para curl.
- **TCE-PB**: bucket https://download.tce.pb.gov.br/dados-abertos/ (XML listing S3, ~1.000 CSV/ZIP em dados-consolidados/{receitas,despesas} e dados-por-municipio/001..013) - 200; SAGRES Online (api 401); front dados-abertos.tce.pb.gov.br (SPA).
- **ALPB**: SAPL REST https://sapl.al.pb.leg.br/api/ (200, DRF, 168 parlamentares).
- TJPB transparência (403 curl/WAF), MPPB e DPE-PB transparência (200), SIC-PB, Rede de Ouvidorias, DOE (A União).

## 4. Não encontrado / pendências
- Página oficial "Contatos" do governo (https://paraiba.pb.gov.br/contatos) e páginas /diretas/* - bloqueio CAPTCHA server-side (não burlado). Rota alternativa: e-SIC (sic.pb.gov.br) ou repetir a leitura em outro horário/IP.
- Portal da Transparência: sem API pública documentada.
- E-mails de hospitais/GRS da SES são majoritariamente gmail/hotmail (marcados em `obs`).
