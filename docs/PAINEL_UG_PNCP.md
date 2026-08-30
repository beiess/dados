# Painel 16 — Unidades Gestoras (PNCP) · registro completo de órgãos do PNCP

**Objetivo:** todas as unidades gestoras/compradoras cadastradas no PNCP (não só quem publicou), com
localização, órgão, natureza jurídica, UASG e **contatos**; e o Painel 2 enriquecido com o registro do PNCP.
**Regra:** acesso ao PNCP **somente leitura** (apenas `GET`; o `POST /v1/usuarios/login` é só autenticação).

## Fonte primária — registro de órgãos do PNCP (API `api/pncp`, OpenAPI em `pncp.gov.br/pncp-api/v3/api-docs`)
- `GET /v1/orgaos/id/{id}` — **IDs sequenciais e densos**: 1 … 98.490 (máximo em 29/08/2026). IDs 1–~95.250 são a
  carga-semente de 28/07/2021; os demais são auto-cadastros. Retorna cnpj, razão social, natureza jurídica (código),
  poder (E/L/J/M/N), esfera (M/E/F/D/N), validado, statusAtivo, datas. **Não traz UF/município.**
- `GET /v1/orgaos/{cnpj}/unidades` — unidades com `municipio{codigoIbge, uf}`; **404 = órgão sem unidades** (~70%).
- Latência ~5–7 s/req; sem bloqueio até 40 em paralelo (~2–4 req/s) → varredura completa ≈ 14 h.
- O login (usuário-sistema da Memory/Plenum) **não destrava dados extras** de órgãos/unidades; só devolve os
  575 `entesAutorizados` do próprio login (→ coluna `cliente_pncp`). `/v1/usuarios?cpfCnpj=` só mostra o próprio
  usuário; `/permissoes` é exclusivo de administradores.

## Fontes complementares
- **UASG / órgãos SIASG** (Compras.gov.br dados abertos, público, 500/página): `modulo-uasg/1_consultarUasg?statusUasg=`
  (45.334 UASGs; 21.970 ativas) e `2_consultarOrgao?statusOrgao=` (11.872 órgãos) → tabelas `uasg`, `orgaos_siasg`.
  Casam com a unidade do PNCP por `codigo_unidade = codigo_uasg` e mesmo CNPJ.
- Contatos: `cadastro_institucional` (MG curado: email, contato, site, portal, ouvidoria, **emails_setoriais**),
  `cadastro_institucional_br`, `obras_engenharia_orgaos` (RFB), `contatos_orgaos_fontes`, `painel14_gestores_rh`,
  `email_vinculos` (Painel 15).

## Pipeline (`~/.claude/jobs/pncp-orgaos/`, credencial do banco em `P1_DB_URL`)
1. `coleta_orgaos.py --ate 98700 --conc 40 --unidades` — ledger `orgaos.jsonl` / `unidades.jsonl` (resumível; 404 fica
   no ledger, queda de rede não). Incremental: novos órgãos entram no fim da sequência → rodar com `--de <último+1>`.
2. `coleta_uasg.py` — UASGs e órgãos SIASG.
3. `carga_pncp.py` — UPSERT em `pncp_orgaos` (PK orgao_id, cnpj único; sede = moda do município das unidades;
   `publicou_pncp` = está em cadastro BR/obras; `cliente_pncp` = ente autorizado do login), `pncp_unidades`, `uasg`, `orgaos_siasg`.
4. `rfb_orgaos.py` — órgãos sem sede/contato → minhareceita (uf, município IBGE, telefone, e-mail, endereço) em `pncp_orgaos_rfb`.
5. `contatos_ug.py` — sede de órgãos sem unidades (uasg > cadastros > RFB); `pncp_ug_contatos` (1 linha/unidade):
   contato do órgão por CNPJ (prioridade cadastro MG > BR > obras/RFB) + **e-mail setorial** (emails_setoriais do
   cadastro MG casado por palavras-chave da unidade × rótulo/parte local do e-mail) + **pessoas** (contatos/gestores/
   vínculos: mesmo CNPJ; fallback por município só p/ órgãos municipais; unidade específica exige afinidade de
   palavra-chave, unidade genérica pega o "melhor contato") → view **`v_pncp_ug`** (lida pelo Painel 16).
6. `enriquece_painel2.py` — colunas `pncp_orgao_id/pncp_validado/pncp_natureza/pncp_n_unidades/pncp_cliente/
   pncp_data_inclusao/pncp_unidades` em `cadastro_institucional` e `cadastro_institucional_br` (Painel 2).

## App
- Painel 16 lê `v_pncp_ug` com o filtro do topo (Municípios → cod_ibge; Estado → uf; Esfera → esfera, estadual inclui
  distrital) + formulário (texto, só com contato, só clientes, só UASG). Colunas extras ocultas por padrão.
- Vínculo `pncp` (CNPJ → registro do PNCP) disponível em ☰ colunas dos Painéis 2, 3, 7, 13 e 15.

## Resultado da carga completa (30/08/2026)
- Varredura de `orgaos/id/1…98.700` em **1h48** (o servidor acelerou para ~15 req/s de madrugada): **98.456 órgãos**
  (34 IDs apagados entre 95.2k–96.6k), **162.627 unidades em 24.647 órgãos** (25% — os 404 de `/unidades` são genuínos:
  200 re-sondados, nenhum mudou). Esfera: Municipal 61.434 · Estadual 19.537 · Federal 13.397 · não inf. 3.736 · Distrital 352.
- UASG: 24.426 unidades casadas (`codigo_unidade = codigo_uasg` e mesmo CNPJ).
- RFB: situação dos CNPJs da semente 2021 = ATIVA ~77% · BAIXADA ~19% · INAPTA ~3% → coluna `situacao_rfb`
  (filtro "só CNPJ ativo" no Painel 16).
- Contatos (v_pncp_ug): e-mail do órgão em 44.143 unidades, e-mail setorial em 1.513, pessoa de contato em 6.031,
  contato de órgão (e-mail ou telefone) em ~117 mil (72%); 210 domínios institucionais (fed/est) derivados do Painel 1.
  Estadual/federal têm pouco e-mail (as fontes de contato são municipais) — coluna `dominio_institucional` ajuda.
- Painel 2: 2.102/2.151 (MG) e 6.002/6.002 (BR) casados com o registro do PNCP; 514 + 143 marcados como clientes.
- Nota: `pgrep -f nome.py` dentro de scripts/monitores casa com o próprio comando → usar `pgrep -f "[n]ome.py"`.
