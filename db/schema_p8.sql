-- Painel 8 — Servidores do Poder Executivo do Estado de MG (2026), consolidado por pessoa (masp).
-- Fonte: dados.mg.gov.br (SEPLAG) "Relação Nominal dos Servidores", meses 202601–202605.
-- Grão: 1 linha por pessoa (masp). Campos *_atual = último mês presente; *_periodo = distintos jan–mai.
-- SEM CPF e SEM remuneração na fonte (só dado público institucional). Rodar no SQL Editor do Supabase.

drop table if exists servidores_estado_2026;

create table servidores_estado_2026 (
  id bigint generated always as identity primary key,
  masp text,
  nome text,
  situacao_atual text,
  cargo_efetivo_atual text,
  comissao_atual text,
  funcao_gratif_atual text,
  carga_horaria text,
  sigla_lotacao_atual text,
  desc_lotacao_atual text,
  sigla_dotacao_atual text,
  desc_dotacao_atual text,
  data_inicio text,
  data_aposentadoria text,
  data_desligamento text,
  n_vinculos text,
  vinculos_adm text,
  cargos_efetivos_periodo text,
  comissoes_periodo text,
  funcoes_gratif_periodo text,
  orgaos_lotacao_periodo text,
  situacoes_periodo text,
  mudou_situacao text,
  n_meses text,
  primeiro_mes text,
  ultimo_mes text,
  presente_em text
);
create index ix_p8_masp on servidores_estado_2026 (masp);
create index ix_p8_nome on servidores_estado_2026 (nome);
create index ix_p8_lot  on servidores_estado_2026 (sigla_lotacao_atual);
create index ix_p8_sit  on servidores_estado_2026 (situacao_atual);

alter table servidores_estado_2026 enable row level security;
drop policy if exists p8_auth_read on servidores_estado_2026;
create policy p8_auth_read on servidores_estado_2026 for select to authenticated using (true);
