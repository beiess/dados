-- Painel 6 — Responsáveis por licitação/dispensa/comissão/parecer (SICOM), cruzados c/ Painel 1.
-- Fonte: SICOM licitacao.{respLicitacao,respDispensa,comissaoLicitacao,parecLicitacao}.
-- CPF: completo (11 díg) quando casou no Painel 1; senão mascarado da origem ("072***406**").
-- Exibição mascarada por padrão no app (mesma regra dos demais painéis). Roda no SQL Editor.

drop table if exists painel6_responsaveis;

create table painel6_responsaveis (
  id bigint generated always as identity primary key,
  cod_ibge text,
  orgao text,
  nome text,
  tipo_responsabilidade text,
  cpf text,
  origem text,
  no_painel1 text
);
create index ix_p6_ibge on painel6_responsaveis (cod_ibge);

alter table painel6_responsaveis enable row level security;
drop policy if exists p6_auth_read on painel6_responsaveis;
create policy p6_auth_read on painel6_responsaveis for select to authenticated using (true);
