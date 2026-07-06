-- Painel 11 — Pessoas ligadas a Obras + "email por secretaria" no Painel 7.
-- Rodar no SQL Editor do Supabase (uma vez). Depois: tools/build_pessoas_obras.py e
-- tools/enrich_obras_email.py fazem a carga.

-- ========================= Painel 11: pessoas_obras (grão = pessoa/papel) =========================
-- Une duas fontes, só órgãos EXECUTIVOS de municípios que contratam obra:
--   A) Responsáveis (SICOM/painel6) COM email — origem='Responsável'. setor = função no processo.
--   B) Engenheiros (servidores/painel1) — origem='Engenheiro'. setor = lotação real (email pode faltar).
-- Multiplos emails de uma mesma pessoa vêm separados por vírgula.
drop table if exists pessoas_obras;
create table pessoas_obras (
  id bigint generated always as identity primary key,
  nome text,
  cpf text,                 -- chave interna; MASCARADO na exposição (LGPD/LAI, CLAUDE.md)
  setor text,               -- função (responsável) OU setor de lotação (engenheiro)
  email text,               -- 1+ emails separados por vírgula
  orgao text,
  municipio text,
  cod_ibge text,
  origem text,              -- 'Responsável' | 'Engenheiro'
  fonte_tipo text default 'SICOM (painel6_responsaveis / painel1_servidores) ∩ órgãos com obra',
  data_coleta text,
  grau_confianca text default 'B'
);
create index ix_p11_ibge   on pessoas_obras (cod_ibge);
create index ix_p11_origem on pessoas_obras (origem);
create index ix_p11_nome   on pessoas_obras (nome);

alter table pessoas_obras enable row level security;
drop policy if exists p11_read on pessoas_obras;
create policy p11_read on pessoas_obras for select to authenticated using (true);

create or replace function truncate_pessoas_obras() returns void
  language sql security definer as $$ truncate pessoas_obras restart identity; $$;

-- ========================= Painel 7: coluna "email por secretaria" =========================
-- emails_setoriais = "SECRETARIA: email, OUTRA: email" (do cadastro_institucional, por CNPJ).
alter table obras_engenharia_orgaos add column if not exists emails_setoriais text;
