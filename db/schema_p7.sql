-- Painel 7 — Obras e Serviços de Engenharia (órgãos/setores que CONTRATAM obras).
-- Grão comercial (lead B2G): quem demanda obra/engenharia + como contatar (email/tel/site).
-- Fonte primária: PNCP consulta `/v1/contratacoes/publicacao` (mesma espinha do P2N).
-- Classificação de obra/engenharia: HEURÍSTICA por léxico sobre `objetoCompra` (o PNCP não
--   expõe categoria de obra na consulta pública; item vem "Não se aplica"). Por isso o
--   grau_confianca do RECORTE é 'B' (heurística textual), distinto do 'A' do cadastro (CNPJ oficial).
-- Enriquecimento (email/telefone/endereço): RFB via minhareceita.org — parcial p/ órgãos públicos.
-- Chaves canônicas (CLAUDE.md): município = cod_ibge (7); órgão = cnpj (14); setor = codigo_unidade.
-- Dois grãos: obras_engenharia_orgaos (1 linha por ÓRGÃO/CNPJ) + _unidades (1 linha por SETOR).
-- Rodar no SQL Editor do Supabase. Carga: truncate + load (retro semanal faz upsert por cnpj).

-- ========================= ÓRGÃOS (grão = cnpj) =========================
drop table if exists obras_engenharia_unidades;
drop table if exists obras_engenharia_orgaos;

create table obras_engenharia_orgaos (
  id bigint generated always as identity primary key,
  cnpj text not null unique,               -- chave canônica do órgão
  razao_social text,
  nome_fantasia text,
  poder text,                              -- Executivo/Legislativo/Judiciário/MP
  esfera text,                             -- Municipal/Estadual/Federal/Distrital
  natureza_juridica text,
  uf text,                                 -- siglaUF (2)
  uf_nome text,
  municipio text,
  cod_ibge text,                           -- 7 dígitos
  -- recorte de OBRAS (agregado das contratações classificadas como obra/engenharia)
  n_obras int default 0,                   -- nº de contratações de obra/engenharia publicadas
  n_setores_obras int default 0,           -- nº de setores distintos que publicaram obra
  valor_estimado_obras numeric,            -- soma de valorTotalEstimado das obras (quando informado)
  modalidades_obras text,                  -- modalidades usadas (ex.: "Concorrência; Dispensa")
  primeira_obra text,                      -- data da 1ª obra publicada (YYYY-MM-DD)
  ultima_obra text,                        -- data da última obra publicada
  exemplos_objeto text,                    -- 2–3 objetos de obra (evidência da classificação)
  setores_obras text,                      -- lista das secretarias/unidades que publicaram obra (denormalizado p/ exibição)
  -- contato / enriquecimento (fase 2; NULL enquanto não coletado)
  email text,
  telefone text,
  situacao_cadastral text,
  logradouro text,
  bairro text,
  cep text,
  site text,
  -- proveniência (obrigatória por CLAUDE.md)
  fonte_url text default 'https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao',
  fonte_tipo text default 'API oficial (PNCP) + classificação heurística por objeto',
  data_coleta text,
  grau_confianca text default 'B'          -- B = recorte por heurística textual sobre objetoCompra
);
create index ix_p7_uf     on obras_engenharia_orgaos (uf);
create index ix_p7_ibge   on obras_engenharia_orgaos (cod_ibge);
create index ix_p7_esfera on obras_engenharia_orgaos (esfera);
create index ix_p7_poder  on obras_engenharia_orgaos (poder);
create index ix_p7_razao  on obras_engenharia_orgaos (razao_social);
create index ix_p7_nobras on obras_engenharia_orgaos (n_obras);

-- ========================= SETORES / SECRETARIAS (grão = unidade) =========================
-- Só os setores que publicaram obra (é onde mora a "Secretaria de Obras/Infraestrutura").
create table obras_engenharia_unidades (
  id bigint generated always as identity primary key,
  cnpj text not null references obras_engenharia_orgaos(cnpj) on delete cascade,
  codigo_unidade text,
  nome_unidade text,                       -- ex.: "SECRETARIA MUNICIPAL DE OBRAS E URBANISMO"
  uf text,
  municipio text,
  cod_ibge text,
  n_obras int default 0,                   -- nº de obras publicadas por este setor
  valor_estimado_obras numeric,
  ultima_obra text,
  unique (cnpj, codigo_unidade)
);
create index ix_p7u_cnpj on obras_engenharia_unidades (cnpj);
create index ix_p7u_ibge on obras_engenharia_unidades (cod_ibge);

-- ========================= RLS (leitura autenticada, padrão dos demais painéis) =========================
alter table obras_engenharia_orgaos   enable row level security;
alter table obras_engenharia_unidades enable row level security;
drop policy if exists p7_read  on obras_engenharia_orgaos;
drop policy if exists p7u_read on obras_engenharia_unidades;
create policy p7_read  on obras_engenharia_orgaos    for select to authenticated using (true);
create policy p7u_read on obras_engenharia_unidades  for select to authenticated using (true);

-- ========================= RPC de carga (mesmo molde do P2N) =========================
create or replace function truncate_obras_engenharia() returns void
  language sql security definer as $$
    truncate obras_engenharia_unidades, obras_engenharia_orgaos restart identity;
  $$;

-- Retroalimentação semanal: em vez de truncate, faça UPSERT por cnpj via REST:
--   POST /rest/v1/obras_engenharia_orgaos  com header  Prefer: resolution=merge-duplicates
--   (on_conflict=cnpj). Setores idem, on_conflict=(cnpj,codigo_unidade).
