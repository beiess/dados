# Diretório oficial de órgãos e entidades do Governo de MS + catálogo de APIs

Data: 2026-08-30. Coleta web (curl + Jina Reader); contatos sempre com URL de origem (`fontes`).

Arquivos:
- `~/.claude/jobs/diretorios-uf/MS/orgaos.jsonl` - 50 linhas
- `~/.claude/jobs/diretorios-uf/MS/apis.jsonl` - 10 APIs/portais
- Área de trabalho: `~/.claude/jobs/diretorios-uf/MS/_trabalho/` (41 páginas /orgao/<slug> em orgaos_md/)

## 1. Fontes-mãe
1. **Diretório oficial**: https://www.ms.gov.br/orgaos (Portal Único, SPA React). Cada página /orgao/<slug> publica **gestor, horário, e-mail, telefone, site, redes e endereço completo**. O backend (rotas cms/orgaos_all/) não é acessível por fora; leitura renderizada via r.jina.ai (41 páginas; rate limit do Jina exigiu 3 rodadas; a página do DETRAN falhou e foi coberta pelo site próprio).
2. Sites próprios dos órgãos (home + contato/ouvidoria): 48 varridos; complementaram e-mails setoriais. Sanesul bloqueia curl (403).
3. Ouvidoria/e-SIC do Executivo: **Fala.BR (CGU)** - MS não tem página-diretório de ouvidorias com contatos.
4. Poderes: ALEMS (al.ms.gov.br), TJMS, TCE-MS, MPMS, DPE-MS (defensoria.ms.def.br, SPA sem contatos no HTML).

## 2. Cobertura (50 linhas)
E-mail 44 (88%); telefone 38 (76%); site 48; endereço 44; gestor/horário na maioria das linhas do diretório oficial. CNPJs: **96 de 96** casados (fundos mapeados à secretaria gestora; Empresa de Serviços Agropecuários extinta → AGRAER; FUNLES → MPMS). Unidades compradoras (1.298): 1.083 (83%) sob CNPJ com e-mail — as 555 unidades (comarcas) do fundo dos Juizados Especiais estão sob TJMS; as 192 do CNPJ raiz "Estado de MS" ficaram na linha GOVMS, que não tem contato próprio publicado (ouvidoria = Fala.BR), único caso relevante sem e-mail.
Sem e-mail/telefone: GOVMS (raiz), SEGOV (páginas "Não informado"), DPE-MS (SPA), IOMS (portal SPDO só login), FUNADEP e Procon-MS (sem site próprio localizado).

## 3. APIs / portais (10)
- MS **não tem CKAN estadual** (dados.ms.gov.br não resolve). Transparência = SPA sem API documentada.
- TCE-MS: /dados-abertos (SPA), transparencia.tce.ms.gov.br, SICAP (login).
- Diário Oficial SPDO; Fala.BR como canal LAI/ouvidoria; transparências de ALEMS/TJMS/MPMS.

## 4. Não encontrado / pendências
- API aberta de dados do Executivo (não existe ou não exposta); catálogo de dados abertos estadual ausente.
- Contatos da DPE-MS e da Imprensa Oficial (páginas SPA/login) - rota: e-SIC.
