-- ============================================================================
-- CRM de Vendas — visão 360 (prospecção → fechamento → pós-venda) + comissionamento
-- Mesma instância Supabase dos painéis. Login = Supabase Auth. Leads vêm do painel
-- estratégico (obras_engenharia_orgaos). Visibilidade: a EQUIPE (organização = matriz +
-- filiais) vê os clientes trabalhados; comissão cada um vê a sua, gestor vê da equipe.
--
-- ARTEFATO DE DESENHO — revisar antes de rodar no SQL Editor. RLS inicial (refinável por papel).
-- ============================================================================

-- ========================= EMPRESAS (matriz/filial) =========================
create table if not exists empresas (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  cnpj text unique,
  tipo text not null default 'matriz' check (tipo in ('matriz','filial')),
  matriz_id uuid references empresas(id),        -- filial aponta p/ matriz; matriz = NULL
  cidade text, uf text,
  ativo boolean default true,
  criado_em timestamptz default now()
);

-- Seed das empresas reais do grupo (dado público de PJ). PII de colaborador NÃO vai no git —
-- funcionários são carregados por tools/load_crm_colaboradores.py a partir da planilha do RH.
insert into empresas (nome, cnpj, tipo) values
  ('Instituto de Desenvolvimento Público Plenum Brasil LTDA', '21650715000160', 'matriz')
  on conflict (cnpj) do nothing;
insert into empresas (nome, cnpj, tipo, matriz_id)
  select 'PlenumGestão LTDA', '41209777000148', 'filial', m.id
  from empresas m where m.cnpj = '21650715000160'
  on conflict (cnpj) do nothing;

-- ========================= FUNCIONÁRIOS (usuários) =========================
-- Estrutura alinhada à planilha real "COLABORADORES 2026" (RH/Interno).
create table if not exists funcionarios (
  id uuid primary key default gen_random_uuid(),
  auth_user_id uuid unique references auth.users(id) on delete set null,  -- login (Supabase Auth)
  nome text not null,
  email text,
  empresa_id uuid not null references empresas(id),
  funcao text not null default 'vendedor' check (funcao in ('admin','gerente','vendedor')),  -- papel no app
  setor text,                                    -- Comercial / Administrativo / Financeiro / Aux. de Limpeza
  cargo text,                                    -- ex.: "Vendedor V", "Gerente de Relacionamento", "Diretor Administrativo"
  nivel text,                                    -- escada do cargo (ex.: I..V) — usada em regra de comissão por nível
  area_atuacao text check (area_atuacao in ('Legislativo','Gestão Pública') or area_atuacao is null),
  -- ^ segmento de vendas. LIGA AO PAINEL: 'Gestão Pública' -> órgãos executivos (prefeituras/obras);
  --   'Legislativo' -> câmaras/legislativo. Usar para rotear leads por área.
  comissao_base_pct numeric default 0,           -- % base individual (pode vir do nível/cargo)
  -- campos de RH (opcionais, da planilha)
  salario numeric, dt_admissao date, sexo text, localizacao text,  -- OBS: BH/DF
  situacao text default 'ativo',
  ativo boolean default true,
  criado_em timestamptz default now()
);

-- ---- Helpers de sessão (usados nas policies de RLS) ----
-- org do usuário = a MATRIZ (matriz vê a si + filiais; filial pertence à mesma org).
create or replace function app_org() returns uuid language sql stable security definer as $$
  select coalesce(e.matriz_id, e.id)
  from funcionarios f join empresas e on e.id = f.empresa_id
  where f.auth_user_id = auth.uid() and f.ativo limit 1;
$$;
create or replace function app_is_gestor() returns boolean language sql stable security definer as $$
  select exists (select 1 from funcionarios
                 where auth_user_id = auth.uid() and ativo and funcao in ('admin','gerente'));
$$;
create or replace function app_me_id() returns uuid language sql stable security definer as $$
  select id from funcionarios where auth_user_id = auth.uid() and ativo limit 1;
$$;

-- ========================= REGRAS DE COMISSÃO =========================
-- Esquemas configuráveis (não hard-coded). config em JSON, ex.:
--   individual : {"pct_base":5, "pct_novo":8}
--   progressivo: {"faixas":[{"ate":100000,"pct":3},{"ate":500000,"pct":5},{"acima":true,"pct":7}]}
--   pos_meta   : {"pct":4, "meta":500000, "bonus_pct":2}   -- bônus após bater a meta
create table if not exists regras_comissao (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null default app_org(),
  nome text not null,
  tipo text not null check (tipo in ('individual','progressivo','pos_meta')),
  aplica_cliente text default 'ambos' check (aplica_cliente in ('base','novo','ambos')),
  config jsonb not null default '{}',
  ativo boolean default true,
  criada_em timestamptz default now()
);

-- ========================= CAMPANHAS =========================
create table if not exists campanhas (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null default app_org(),
  nome text not null,
  descricao text,
  inicio date, fim date,
  meta_valor numeric,
  regra_comissao_id uuid references regras_comissao(id),
  status text default 'ativa' check (status in ('rascunho','ativa','encerrada')),
  criada_por uuid references funcionarios(id) default app_me_id(),
  criada_em timestamptz default now()
);

-- ========================= CLIENTES (leads do painel estratégico) =========================
create table if not exists clientes (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null default app_org(),
  campanha_id uuid references campanhas(id),
  origem text default 'painel_estrategico',
  ref_cnpj text,                    -- vínculo ao painel: obras_engenharia_orgaos.cnpj
  ref_cod_ibge text,
  razao_social text not null,
  tipo text default 'novo' check (tipo in ('base','novo')),   -- cliente de base × novo
  area_atuacao text check (area_atuacao in ('Legislativo','Gestão Pública') or area_atuacao is null),
  -- ^ segmento do lead (deriva do poder do órgão no painel: executivo->Gestão Pública; legislativo->Legislativo).
  --   Casa com funcionarios.area_atuacao para rotear o lead ao vendedor da área certa.
  uf text, municipio text,
  email text, telefone text, emails_setoriais text, site text,
  criado_por uuid references funcionarios(id) default app_me_id(),
  criado_em timestamptz default now()
);

-- ========================= OPORTUNIDADES (o funil) =========================
create table if not exists oportunidades (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null default app_org(),
  cliente_id uuid not null references clientes(id) on delete cascade,
  campanha_id uuid references campanhas(id),
  titulo text,
  valor_estimado numeric,
  valor_fechado numeric,
  estagio text not null default 'prospeccao' check (estagio in
    ('prospeccao','qualificacao','proposta','negociacao','fechada_ganha','fechada_perdida','pos_venda')),
  probabilidade int,
  dono_id uuid references funcionarios(id) default app_me_id(),
  aberta_em timestamptz default now(),
  fechada_em timestamptz,
  motivo_perda text
);

-- ========================= PARTICIPAÇÕES (quem atuou + rateio) =========================
-- Registra CADA pessoa que atuou na venda e sua fatia. Soma de rateio_pct por oportunidade = 100.
create table if not exists participacoes (
  id uuid primary key default gen_random_uuid(),
  oportunidade_id uuid not null references oportunidades(id) on delete cascade,
  funcionario_id uuid not null references funcionarios(id),
  papel text default 'responsavel' check (papel in ('responsavel','parceiro','equipe')),
  escopo text default 'individual' check (escopo in
    ('individual','parceiro','equipe','matriz','filial','geral')),
  rateio_pct numeric not null default 100,
  criada_em timestamptz default now(),
  unique (oportunidade_id, funcionario_id)
);

-- ========================= ATIVIDADES (timeline 360) =========================
create table if not exists atividades (
  id uuid primary key default gen_random_uuid(),
  oportunidade_id uuid not null references oportunidades(id) on delete cascade,
  funcionario_id uuid references funcionarios(id) default app_me_id(),
  tipo text default 'nota' check (tipo in
    ('nota','ligacao','email','reuniao','mudanca_estagio','proposta','documento')),
  descricao text,
  estagio_de text, estagio_para text,           -- preenchidos quando tipo='mudanca_estagio'
  criada_em timestamptz default now()
);

-- ========================= COMISSÕES (calculado ao ganhar) =========================
create table if not exists comissoes (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null default app_org(),
  oportunidade_id uuid references oportunidades(id) on delete cascade,
  funcionario_id uuid references funcionarios(id),
  base_valor numeric,
  pct_aplicado numeric,
  valor_comissao numeric,
  memoria jsonb,                                 -- detalhamento auditável (regra, faixa, rateio…)
  status text default 'prevista' check (status in ('prevista','apurada','paga')),
  criada_em timestamptz default now()
);

-- ========================= ÍNDICES =========================
create index if not exists ix_func_auth   on funcionarios(auth_user_id);
create index if not exists ix_op_org       on oportunidades(org_id);
create index if not exists ix_op_estagio   on oportunidades(estagio);
create index if not exists ix_op_cliente   on oportunidades(cliente_id);
create index if not exists ix_cli_org      on clientes(org_id);
create index if not exists ix_ativ_op      on atividades(oportunidade_id);
create index if not exists ix_part_op      on participacoes(oportunidade_id);
create index if not exists ix_com_func     on comissoes(funcionario_id);

-- ============================================================================
-- RLS — visibilidade da EQUIPE (mesma org) + escrita por autenticados; comissão own/gestor
-- ============================================================================
alter table empresas         enable row level security;
alter table funcionarios     enable row level security;
alter table regras_comissao  enable row level security;
alter table campanhas        enable row level security;
alter table clientes         enable row level security;
alter table oportunidades    enable row level security;
alter table participacoes    enable row level security;
alter table atividades       enable row level security;
alter table comissoes        enable row level security;

-- Empresas: vê as da sua org (matriz + filiais); escreve só gestor.
create policy emp_sel on empresas for select to authenticated
  using (id = app_org() or matriz_id = app_org());
create policy emp_wr  on empresas for all to authenticated
  using ((id = app_org() or matriz_id = app_org()) and app_is_gestor())
  with check ((id = app_org() or matriz_id = app_org()) and app_is_gestor());

-- Funcionários: vê os da org; escreve só gestor.
create policy fun_sel on funcionarios for select to authenticated
  using (empresa_id in (select id from empresas where id = app_org() or matriz_id = app_org()));
create policy fun_wr  on funcionarios for all to authenticated
  using (app_is_gestor() and empresa_id in (select id from empresas where id = app_org() or matriz_id = app_org()))
  with check (app_is_gestor());

-- Tabelas org-scoped (org_id): EQUIPE vê tudo; qualquer autenticado da org cria/edita.
-- (campanhas e regras: leitura equipe, escrita gestor.)
create policy rc_sel  on regras_comissao for select to authenticated using (org_id = app_org());
create policy rc_wr   on regras_comissao for all    to authenticated using (org_id = app_org() and app_is_gestor()) with check (org_id = app_org() and app_is_gestor());
create policy cmp_sel on campanhas       for select to authenticated using (org_id = app_org());
create policy cmp_wr  on campanhas       for all    to authenticated using (org_id = app_org() and app_is_gestor()) with check (org_id = app_org() and app_is_gestor());

create policy cli_sel on clientes        for select to authenticated using (org_id = app_org());
create policy cli_wr  on clientes        for all    to authenticated using (org_id = app_org()) with check (org_id = app_org());
create policy opp_sel on oportunidades   for select to authenticated using (org_id = app_org());
create policy opp_wr  on oportunidades   for all    to authenticated using (org_id = app_org()) with check (org_id = app_org());

-- Participações e atividades: visíveis/edit por quem é da org da oportunidade.
create policy part_all on participacoes for all to authenticated
  using (exists (select 1 from oportunidades o where o.id = oportunidade_id and o.org_id = app_org()))
  with check (exists (select 1 from oportunidades o where o.id = oportunidade_id and o.org_id = app_org()));
create policy ativ_all on atividades for all to authenticated
  using (exists (select 1 from oportunidades o where o.id = oportunidade_id and o.org_id = app_org()))
  with check (exists (select 1 from oportunidades o where o.id = oportunidade_id and o.org_id = app_org()));

-- Comissões: cada um vê a SUA; gestor vê da org. Escrita pelo motor (service_role) ou gestor.
create policy com_sel on comissoes for select to authenticated
  using (org_id = app_org() and (app_is_gestor() or funcionario_id = app_me_id()));
create policy com_wr  on comissoes for all to authenticated
  using (org_id = app_org() and app_is_gestor()) with check (org_id = app_org() and app_is_gestor());

-- ============================================================================
-- PENDENTE (Fase 2): função calcular_comissao(oportunidade) que, ao estágio virar
-- 'fechada_ganha', percorre participacoes × regra_comissao da campanha (tipo cliente,
-- faixa progressiva, pós-meta) e grava linhas em comissoes com a memoria jsonb.
-- ============================================================================
