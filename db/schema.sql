-- Base canônica TCE-MG — schema Supabase (Postgres)
-- 2 tabelas relacionadas por ibge / cnpj (Painel 1 ⊕ Painel 2)

-- Painel 1 — Dados Estratégicos (servidores; fontes complementares SICOM ⊕ PNTP ⊕ sites)
create table if not exists painel1_servidores (
  id                bigint generated always as identity primary key,
  ibge              text,
  entidade          text,
  orgao             text,
  esfera            text,
  setor             text,
  cargo_funcao      text,
  matricula         text,
  regime            text,
  nome              text,
  cpf               text,          -- chave interna; mascarar na exposição
  remuneracao       text,
  responsabilidade  text,
  cnpj_entidade     text,
  email_entidade    text,
  telefone_entidade text,
  site_entidade     text,
  endereco_entidade text,
  portal_transparencia_entidade text,
  redes_entidade    text,
  consta_site       text,
  origem            text,
  grau_confianca    text,
  motivo_ausencia   text
);
create index if not exists ix_p1_ibge on painel1_servidores (ibge);
create index if not exists ix_p1_nome on painel1_servidores (nome);
create index if not exists ix_p1_cpf  on painel1_servidores (cpf);
create index if not exists ix_p1_cnpj on painel1_servidores (cnpj_entidade);

-- Painel 2 — Cadastro Institucional (pessoas jurídicas / órgãos)
create table if not exists cadastro_institucional (
  entidade_id       text,
  ibge              text,
  uf                text,
  cod_orgao         text,
  cidade            text,
  entidade          text,
  orgao             text,
  esfera            text,
  cnpj              text,
  endereco          text,
  latitude          text,
  longitude         text,
  geo_precisao      text,
  contato           text,
  email             text,
  emails_setoriais  text,
  redes_sociais     text,
  site_oficial      text,
  portal_transparencia text,
  ouvidoria         text,
  links_relevantes  text,
  gestores          text,
  atores_relevantes text,
  atores_confirmados text,
  atores_validados  text,
  observacoes       text
);
create index if not exists ix_cad_ibge on cadastro_institucional (ibge);
create index if not exists ix_cad_cnpj on cadastro_institucional (cnpj);

-- RLS: leitura pública (anon) só-leitura; escrita via service_role
alter table painel1_servidores enable row level security;
alter table cadastro_institucional enable row level security;
drop policy if exists p1_read on painel1_servidores;
create policy p1_read on painel1_servidores for select using (true);
drop policy if exists cad_read on cadastro_institucional;
create policy cad_read on cadastro_institucional for select using (true);
