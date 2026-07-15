-- Painel 13 — Contatos consolidados de "Outras Fontes"
-- Tabela alimentada por tools de normalização (scratchpad: normaliza_contatos.py + carga_contatos.py + xref_contatos.py).
-- Fonte: exports de contatos (PM/CM/previdências/consórcios de MG) + base de e-mails, casados por município/órgão
-- e cruzados contra painel6_responsaveis, pessoas_obras, servidor_contatos/painel1 e cadastro_institucional.
create table if not exists contatos_orgaos_fontes (
  id bigint generated always as identity primary key,
  fonte_arquivo text not null,
  tipo_orgao text not null,          -- PM | CM | PREV | CONSORCIO | OUTRO
  municipio text, ibge text,
  entidade_id text, cnpj text, entidade text,
  nome_pessoa text, cargo text, setor text,
  email text, telefone1 text, telefone2 text,
  obs text, score int,
  melhor_contato boolean default false,   -- 1 por grupo (ibge, tipo_orgao): maior score
  uf text default 'MG',
  fonte text default 'outras_fontes_andre_azevedo',
  data_coleta date default current_date
);
create index if not exists ix_cof_ibge on contatos_orgaos_fontes (ibge);
create index if not exists ix_cof_entidade on contatos_orgaos_fontes (entidade_id);
create index if not exists ix_cof_email on contatos_orgaos_fontes (email);
create index if not exists ix_cof_melhor on contatos_orgaos_fontes (melhor_contato) where melhor_contato;
alter table contatos_orgaos_fontes enable row level security;
create policy cof_auth_read on contatos_orgaos_fontes for select to authenticated using (true);
