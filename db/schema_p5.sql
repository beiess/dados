-- Painel 5 — Estrutura organizacional / Quadro de Detalhamento da Despesa 2026 (QDD/LOA).
-- Fonte: TCE-MG ReportViewer UC05-Arvore-RL. Grão = folha (nível Fonte de Recurso):
-- Órgão > Unidade > Função > Subfunção > Programa > Ação > Subação > Natureza > Fonte + valor.
-- A soma de `valor` por município reproduz o total da despesa orçada (LOA). Roda no SQL Editor.

drop table if exists estrutura_despesa_2026;

create table estrutura_despesa_2026 (
  id bigint generated always as identity primary key,
  cod_ibge text,
  orgao text,
  unidade_orcamentaria text,
  funcao text,
  subfuncao text,
  programa text,
  acao text,
  subacao text,
  natureza_despesa text,
  fonte_recurso text,
  valor text
);
create index ix_p5_ibge on estrutura_despesa_2026 (cod_ibge);

alter table estrutura_despesa_2026 enable row level security;
drop policy if exists p5_auth_read on estrutura_despesa_2026;
-- leitura SOMENTE para usuários autenticados (mesma regra dos demais painéis)
create policy p5_auth_read on estrutura_despesa_2026 for select to authenticated using (true);
