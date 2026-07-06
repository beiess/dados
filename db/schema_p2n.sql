-- Painel 2N — Cadastro Institucional Nacional (Brasil / PNCP em cascata).
-- Fonte primária: PNCP consulta (quem publicou). Enriquecimento (fase 2): RFB, Compras.gov.br.
-- Chaves canônicas (CLAUDE.md): município = cod_ibge (7); órgão = cnpj (14). Contratação = id_pncp.
-- Dois grãos: cadastro_institucional_br (1 linha por ÓRGÃO/CNPJ) + _unidades (1 linha por SETOR).
-- Rodar no SQL Editor do Supabase. Carga: truncate + load (retro semanal faz upsert por cnpj).

-- ========================= ÓRGÃOS (grão = cnpj) =========================
drop table if exists cadastro_institucional_br_unidades;
drop table if exists cadastro_institucional_br;

create table cadastro_institucional_br (
  id bigint generated always as identity primary key,
  cnpj text not null unique,               -- chave canônica do órgão
  razao_social text,
  nome_fantasia text,
  poder text,                              -- Executivo/Legislativo/Judiciário/MP
  esfera text,                             -- Municipal/Estadual/Federal/Distrital
  cod_natureza_juridica text,
  natureza_juridica text,
  uf text,                                 -- siglaUF (2)
  uf_nome text,
  municipio text,
  cod_ibge text,                           -- 7 dígitos
  n_setores int default 0,
  status_ativo boolean,
  -- enriquecimento (fase 2; NULL enquanto não coletado)
  email text,
  telefone text,
  situacao_cadastral text,
  logradouro text,
  bairro text,
  cep text,
  site text,
  info_complementar text,
  -- fonte PNCP / proveniência (obrigatória por CLAUDE.md)
  publicou_pncp boolean default true,
  primeira_publicacao text,
  ultima_publicacao text,
  n_modalidades int,
  fonte_url text default 'https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao',
  fonte_tipo text default 'API oficial (PNCP)',
  data_coleta text,
  grau_confianca text default 'A'          -- A = identificador oficial completo (CNPJ/PNCP)
);
create index ix_p2n_uf     on cadastro_institucional_br (uf);
create index ix_p2n_ibge   on cadastro_institucional_br (cod_ibge);
create index ix_p2n_esfera on cadastro_institucional_br (esfera);
create index ix_p2n_poder  on cadastro_institucional_br (poder);
create index ix_p2n_razao  on cadastro_institucional_br (razao_social);

-- ========================= UNIDADES / SETORES (grão = unidade) =========================
create table cadastro_institucional_br_unidades (
  id bigint generated always as identity primary key,
  cnpj text not null references cadastro_institucional_br(cnpj) on delete cascade,
  codigo_unidade text,
  nome_unidade text,
  uf text,
  municipio text,
  cod_ibge text,
  unique (cnpj, codigo_unidade)
);
create index ix_p2nu_cnpj on cadastro_institucional_br_unidades (cnpj);
create index ix_p2nu_ibge on cadastro_institucional_br_unidades (cod_ibge);

-- ========================= RLS (leitura autenticada, padrão dos demais painéis) =========================
alter table cadastro_institucional_br enable row level security;
alter table cadastro_institucional_br_unidades enable row level security;
drop policy if exists p2n_read on cadastro_institucional_br;
drop policy if exists p2nu_read on cadastro_institucional_br_unidades;
create policy p2n_read  on cadastro_institucional_br            for select to authenticated using (true);
create policy p2nu_read on cadastro_institucional_br_unidades   for select to authenticated using (true);

-- ========================= RPCs de carga (mesmo molde do P8) =========================
create or replace function truncate_cadastro_institucional_br() returns void
  language sql security definer as $$
    truncate cadastro_institucional_br_unidades, cadastro_institucional_br restart identity;
  $$;

-- Retroalimentação semanal: em vez de truncate, faça UPSERT por cnpj via REST:
--   POST /rest/v1/cadastro_institucional_br  com header  Prefer: resolution=merge-duplicates
--   (on_conflict=cnpj). As unidades idem, on_conflict=(cnpj,codigo_unidade).
