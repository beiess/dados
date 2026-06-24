-- Backend AUTENTICADO (Supabase Auth + RLS). Só usuário LOGADO lê os dados completos.
-- Roda no SQL Editor. Limpa o painel1 anterior (estava com ibge nulo) e recria enxuto.

drop table if exists painel1_servidores;

create table painel1_servidores (
  id bigint generated always as identity primary key,
  ibge text, orgao text, setor text, cargo_funcao text, nome text,
  cpf text, matricula text, remuneracao text, responsabilidade text,
  consta_site text, origem text
);
create index ix_p1_ibge on painel1_servidores (ibge);
create index ix_p1_nome on painel1_servidores (nome);
create index ix_p1_cpf  on painel1_servidores (cpf);

-- cadastro_institucional já existe (2.151). Garante RLS.
alter table painel1_servidores enable row level security;
alter table cadastro_institucional enable row level security;

-- remove leitura pública anterior
drop policy if exists p1_read on painel1_servidores;
drop policy if exists cad_read on cadastro_institucional;

-- leitura SOMENTE para usuários autenticados (login). anon (deslogado) NÃO lê.
create policy p1_auth_read  on painel1_servidores   for select to authenticated using (true);
create policy cad_auth_read on cadastro_institucional for select to authenticated using (true);
