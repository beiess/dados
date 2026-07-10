-- Servidores públicos — esferas federal, Justiça e AL (coleta 2026-07-09)
-- Fontes: Portal da Transparência/CGU (SIAPE 2026-05), DadosJusBr (membros,
-- 2025-09..2026-05), Portal da Transparência de AL (2026-06).
-- Complementa painel1_servidores (municípios/MG) e servidores_estado_2026 (estado/MG).
-- Proveniência conforme CLAUDE.md: fonte_url, fonte_tipo, data_coleta, grau_confianca.
-- CPF já vem MASCARADO na origem (CGU: ***.999.999-**; AL: ###.999.9##-##).

create extension if not exists pg_trgm;

create table if not exists servidores_brasil_2026 (
  id bigint generated always as identity primary key,
  -- proveniência
  fonte text not null,              -- SIAPE | DADOSJUSBR | TRANSPARENCIA_AL
  fonte_url text not null,
  fonte_tipo text not null default 'download_massa',
  data_coleta date not null,
  grau_confianca text not null default 'A',
  competencia text not null,        -- AAAA-MM da folha
  -- estrutura organizacional
  esfera text not null,             -- federal | estadual | justica
  poder text,                       -- executivo | judiciario | ministerio_publico
  uf text,
  entidade text,                    -- órgão superior / entidade
  cod_orgao text,
  orgao text,
  setor text,                       -- UORG de exercício / local de trabalho
  -- pessoa e vínculo
  nome text not null,
  cpf text,                         -- mascarado na origem
  matricula text,
  cargo text,
  classe_cargo text,
  funcao text,
  atividade text,
  tipo_vinculo text,
  situacao text,
  regime text,
  jornada text,
  data_ingresso_orgao text,
  remuneracao numeric,               -- básica bruta (federal) / total (AL, Justiça)
  -- enriquecimento (09-10/07/2026)
  esfera_adm text,                   -- federal | estadual (esfera administrativa)
  id_servidor_portal text,           -- id individual no Portal da Transparência (federal)
  remuneracao_liquida numeric,       -- após deduções obrigatórias (federal)
  instituidor_pensao text            -- de quem deriva a pensão (pensionistas federais)
);

create index if not exists idx_sb26_nome_trgm on servidores_brasil_2026 using gin (nome gin_trgm_ops);
create index if not exists idx_sb26_orgao on servidores_brasil_2026 (orgao);
create index if not exists idx_sb26_entidade on servidores_brasil_2026 (entidade);
create index if not exists idx_sb26_uf on servidores_brasil_2026 (uf);
create index if not exists idx_sb26_esfera_poder on servidores_brasil_2026 (esfera, poder);

alter table servidores_brasil_2026 enable row level security;
drop policy if exists sb26_leitura_autenticada on servidores_brasil_2026;
create policy sb26_leitura_autenticada on servidores_brasil_2026
  for select to authenticated using (true);
