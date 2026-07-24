-- ============================================================================
-- CRM de Vendas Plenum — SCHEMA v2 (build real, espelha o conceito v14)
-- Rodar no SQL Editor: https://supabase.com/dashboard/project/ntkntgcegvqqlarjspjp/sql/new
--
-- Modelo:
--  · Cascata: crm_entidades › crm_setores (1º/2º nível) › crm_servidores (folha)
--  · CAPTURA é POR SERVIDOR; um servidor NÃO participa de campanhas concomitantes
--    (unique index parcial). Quem captura vira responsável; transferir = só gestor
--    (trigger). Escopo/%/valor unitário vêm da CAMPANHA (definidos pelo admin).
--  · Comissão: regras VERSIONADAS com vigência (regras_versoes) + APURAÇÕES
--    imutáveis com snapshot da regra à época (sem policy de update/delete).
--  · Login: Supabase Auth. CPF+senha = email alias cpf<digitos>@crm.plenumbrasil.com.br
--    (provisionado por tools/crm_logins.py). israel@licitapublica.com.br = irrestrito.
--  · Visibilidade: EQUIPE (org = matriz + filiais) vê tudo; escrita de cadastro só gestor.
--  · LGPD: cpf é chave interna — MASCARAR na exibição (app já mascara).
-- ============================================================================

-- ========================= EMPRESAS (matriz/filial) =========================
create table if not exists empresas (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  cnpj text unique,
  tipo text not null default 'matriz' check (tipo in ('matriz','filial')),
  matriz_id uuid references empresas(id),
  cidade text, uf text,
  ativo boolean default true,
  criado_em timestamptz default now()
);
insert into empresas (nome, cnpj, tipo) values
  ('Instituto de Desenvolvimento Público Plenum Brasil LTDA', '21650715000160', 'matriz')
  on conflict (cnpj) do nothing;
insert into empresas (nome, cnpj, tipo, matriz_id)
  select 'PlenumGestão LTDA', '41209777000148', 'filial', m.id
  from empresas m where m.cnpj = '21650715000160'
  on conflict (cnpj) do nothing;

-- ========================= FUNCIONÁRIOS (usuários) =========================
create table if not exists funcionarios (
  id uuid primary key default gen_random_uuid(),
  auth_user_id uuid unique references auth.users(id) on delete set null,
  nome text not null,
  email text,
  cpf text,                                       -- login interno (só dígitos) — MASCARAR na exibição
  empresa_id uuid not null references empresas(id),
  funcao text not null default 'vendedor' check (funcao in ('admin','gerente','vendedor')),
  setor text, cargo text, nivel text,
  area_atuacao text check (area_atuacao in ('Legislativo','Gestão Pública') or area_atuacao is null),
  comissao_base_pct numeric default 5,
  meta_individual numeric default 0,              -- meta configurável por vendedor (R$)
  acesso_irrestrito boolean default false,        -- israel@licitapublica.com.br
  salario numeric, dt_admissao date, sexo text, localizacao text,
  situacao text default 'ativo',
  ativo boolean default true,
  criado_em timestamptz default now()
);
create unique index if not exists ux_func_email on funcionarios(email) where email is not null;
create unique index if not exists ux_func_cpf   on funcionarios(cpf)   where cpf is not null;

-- usuário com acesso irrestrito (auth_user_id vinculado por tools/crm_logins.py --link)
insert into funcionarios (nome, email, empresa_id, funcao, acesso_irrestrito, comissao_base_pct)
  select 'Israel Santiago', 'israel@licitapublica.com.br', m.id, 'admin', true, 0
  from empresas m where m.cnpj = '21650715000160'
  on conflict do nothing;

-- senhas preenchidas manualmente pelo admin no app ficam AQUI até o provisionamento
-- (tools/crm_logins.py cria o usuário no Auth e APAGA a linha). Transiente; só gestor lê.
create table if not exists logins_pendentes (
  funcionario_id uuid primary key references funcionarios(id) on delete cascade,
  cpf text not null,
  senha text not null,
  criado_em timestamptz default now()
);

-- ---- Helpers de sessão ----
create or replace function app_org() returns uuid language sql stable security definer as $$
  select coalesce(e.matriz_id, e.id)
  from funcionarios f join empresas e on e.id = f.empresa_id
  where f.auth_user_id = auth.uid() and f.ativo limit 1;
$$;
create or replace function app_me_id() returns uuid language sql stable security definer as $$
  select id from funcionarios where auth_user_id = auth.uid() and ativo limit 1;
$$;
create or replace function app_is_gestor() returns boolean language sql stable security definer as $$
  select exists (select 1 from funcionarios
                 where auth_user_id = auth.uid() and ativo
                   and (funcao in ('admin','gerente') or acesso_irrestrito));
$$;

-- ========================= ENTIDADES (aba "Todos" em cascata) =========================
create table if not exists crm_entidades (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null default app_org(),
  cnpj text, cod_ibge text,
  nome text not null,
  esfera text check (esfera in ('Municipal','Estadual','Federal','Privado')),
  poder text,                                     -- Executivo / Legislativo / Judiciário / Controle Externo / —
  tipo_orgao text,                                -- Prefeitura / Câmara / Fundo de Saúde / Autarquia / Tribunal de Contas / Instituto / Assessoria / Fornecedor...
  area text check (area in ('Legislativo','Gestão Pública') or area is null),
  tema text,                                      -- Obras / Saúde / Educação / Administração / Legislativo / Controle Externo / Parceria
  tipo_cliente text default 'novo' check (tipo_cliente in ('novo','base')),
  cnae text,
  uf text, municipio text,
  email text, telefone text, site text,
  n_obras int, valor_obras numeric,               -- contexto do painel estratégico
  fonte text default 'painel_estrategico',
  criado_em timestamptz default now()
);
create unique index if not exists ux_ent_cnpj on crm_entidades(cnpj) where cnpj is not null;
create index if not exists ix_ent_ibge on crm_entidades(cod_ibge);

create table if not exists crm_setores (         -- 1º nível = secretaria; 2º nível = unidade
  id uuid primary key default gen_random_uuid(),
  entidade_id uuid not null references crm_entidades(id) on delete cascade,
  parent_id uuid references crm_setores(id) on delete cascade,
  nivel smallint not null default 1 check (nivel in (1,2)),
  nome text not null,
  tema text, email text,
  criado_em timestamptz default now()
);
create index if not exists ix_set_ent on crm_setores(entidade_id);

create table if not exists crm_servidores (      -- SEMPRE folha (último nível)
  id uuid primary key default gen_random_uuid(),
  entidade_id uuid not null references crm_entidades(id) on delete cascade,
  setor_id uuid references crm_setores(id) on delete set null,
  nome text not null,
  cargo text, email text, telefone text,
  cpf text,                                       -- interno; mascarar
  origem text default 'painel_estrategico',
  criado_em timestamptz default now()
);
create index if not exists ix_srv_ent on crm_servidores(entidade_id);
create index if not exists ix_srv_set on crm_servidores(setor_id);

create table if not exists crm_contatos (        -- tipos livres (ficha do servidor / entidade)
  id uuid primary key default gen_random_uuid(),
  entidade_id uuid references crm_entidades(id) on delete cascade,
  servidor_id uuid references crm_servidores(id) on delete cascade,
  tipo text not null,                             -- Email / Telefone / Setor / Responsabilidade / Rede social / Observação / Institucional / ...
  valor text not null,
  rede text,                                      -- qual rede social, quando tipo='Rede social'
  complemento text,
  criado_por uuid references funcionarios(id) default app_me_id(),
  criado_em timestamptz default now(),
  check (entidade_id is not null or servidor_id is not null)
);
create index if not exists ix_ct_srv on crm_contatos(servidor_id);

-- ========================= REGRAS DE COMISSÃO (versionadas, com vigência) =========================
create table if not exists regras_versoes (
  versao int generated always as identity primary key,
  org_id uuid not null default app_org(),
  vigente_de date not null default current_date,
  vigente_ate date,                               -- NULL = vigente
  descricao text not null,
  config jsonb not null default '{}',
  criado_por uuid references funcionarios(id) default app_me_id(),
  criado_em timestamptz default now()
);
insert into regras_versoes (org_id, vigente_de, descricao, config, criado_por)
  select coalesce(e.matriz_id, e.id), '2026-02-01',
         'Base IV/V 5% · cliente novo 5% · base/renovação 3% · rateio geral 70·30',
         '{"base":{"IV":5,"V":5},"cliente":{"novo":5,"base":3},"rateio_geral":[70,30]}'::jsonb,
         null
  from empresas e where e.cnpj='21650715000160'
  and not exists (select 1 from regras_versoes);

-- ========================= CAMPANHAS (parâmetros definidos pelo ADMIN) =========================
create table if not exists campanhas (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null default app_org(),
  nome text not null,
  inicio date, fim date,
  meta_valor numeric,
  segmento text default 'Gestão Pública',
  escopo_rateio text default 'Individual' check (escopo_rateio in
    ('Individual','Com parceiro','Por equipe','Só matriz','Só filial','Geral')),
  pct_comissao numeric default 5,
  valor_unitario numeric default 0,
  regra_versao int references regras_versoes(versao),
  criterios jsonb default '{}',                   -- {temas:[],responsabilidade,funcao,setor,cargo,kw,cnae}
  anexos jsonb default '[]',                      -- [{nome,ext,url}]
  links  jsonb default '[]',                      -- [{nome,url}]
  status text default 'ativa' check (status in ('rascunho','ativa','encerrada')),
  criada_por uuid references funcionarios(id) default app_me_id(),
  criada_em timestamptz default now()
);

-- ========================= CAPTURAS (funil POR SERVIDOR) =========================
create table if not exists capturas (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null default app_org(),
  servidor_id uuid not null references crm_servidores(id) on delete cascade,
  entidade_id uuid not null references crm_entidades(id),
  campanha_id uuid not null references campanhas(id),
  responsavel_id uuid not null references funcionarios(id) default app_me_id(),
  estagio text not null default 'prospeccao' check (estagio in
    ('prospeccao','qualificacao','proposta','negociacao','fechamento','pos_venda','perdida')),
  valor_contrato numeric,
  obs text,
  ativo boolean default true,
  criado_por uuid references funcionarios(id) default app_me_id(),
  criado_em timestamptz default now(),
  atualizado_em timestamptz default now()
);
-- EXCLUSIVIDADE: um servidor não participa de campanhas concomitantes
create unique index if not exists ux_cap_servidor_ativo on capturas(servidor_id) where ativo;
create index if not exists ix_cap_ent on capturas(entidade_id);
create index if not exists ix_cap_camp on capturas(campanha_id);

-- transferência de responsável: SÓ gerente/admin/irrestrito
create or replace function trg_capturas_resp() returns trigger language plpgsql security definer as $$
begin
  if new.responsavel_id is distinct from old.responsavel_id and not app_is_gestor() then
    raise exception 'Transferência de responsável permitida apenas a gerente/admin';
  end if;
  new.atualizado_em := now();
  return new;
end $$;
drop trigger if exists t_capturas_resp on capturas;
create trigger t_capturas_resp before update on capturas
  for each row execute function trg_capturas_resp();

create table if not exists participacoes (
  id uuid primary key default gen_random_uuid(),
  captura_id uuid not null references capturas(id) on delete cascade,
  funcionario_id uuid not null references funcionarios(id),
  papel text default 'responsavel' check (papel in ('responsavel','parceiro','equipe')),
  rateio_pct numeric not null default 100,
  criada_em timestamptz default now(),
  unique (captura_id, funcionario_id)
);

create table if not exists atividades (
  id uuid primary key default gen_random_uuid(),
  captura_id uuid not null references capturas(id) on delete cascade,
  funcionario_id uuid references funcionarios(id) default app_me_id(),
  tipo text default 'nota' check (tipo in
    ('nota','ligacao','email','reuniao','mudanca_estagio','captura','proposta','documento')),
  descricao text,
  estagio_de text, estagio_para text,
  criada_em timestamptz default now()
);
create index if not exists ix_ativ_cap on atividades(captura_id);

-- ========================= APURAÇÕES (histórico IMUTÁVEL, regra à época) =========================
create table if not exists apuracoes (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null default app_org(),
  captura_id uuid references capturas(id),
  funcionario_id uuid not null references funcionarios(id),
  competencia text not null,                      -- 'AAAA-MM'
  regra_versao int not null references regras_versoes(versao),
  regra_snapshot jsonb,                           -- cópia da config à época (imune a edições futuras)
  base_valor numeric, pct_aplicado numeric, rateio_pct numeric,
  memoria text,                                   -- cálculo por extenso
  valor numeric not null,
  apurado_por uuid references funcionarios(id) default app_me_id(),
  apurado_em timestamptz default now()
);
create index if not exists ix_apur_func on apuracoes(funcionario_id);

-- ========================= VIEW 360 =========================
create or replace view v_capturas_360 with (security_invoker = on) as
select c.id, c.estagio, c.valor_contrato, c.obs, c.ativo, c.criado_em, c.atualizado_em,
       s.id as servidor_id, s.nome as servidor, s.cargo, s.email as servidor_email, s.telefone as servidor_tel,
       st.nome as setor, st2.nome as unidade,
       e.id as entidade_id, e.nome as entidade, e.esfera, e.poder, e.tipo_orgao, e.area, e.tema, e.uf, e.municipio,
       f.nome as responsavel, f.id as responsavel_id,
       cp.nome as campanha, cp.id as campanha_id, cp.escopo_rateio, cp.pct_comissao, cp.valor_unitario
from capturas c
join crm_servidores s on s.id = c.servidor_id
left join crm_setores st2 on st2.id = s.setor_id
left join crm_setores st on st.id = coalesce(st2.parent_id, s.setor_id)
join crm_entidades e on e.id = c.entidade_id
join funcionarios f on f.id = c.responsavel_id
join campanhas cp on cp.id = c.campanha_id;

-- ============================================================================
-- RLS
-- ============================================================================
alter table empresas          enable row level security;
alter table funcionarios      enable row level security;
alter table logins_pendentes  enable row level security;
alter table crm_entidades     enable row level security;
alter table crm_setores       enable row level security;
alter table crm_servidores    enable row level security;
alter table crm_contatos      enable row level security;
alter table regras_versoes    enable row level security;
alter table campanhas         enable row level security;
alter table capturas          enable row level security;
alter table participacoes     enable row level security;
alter table atividades        enable row level security;
alter table apuracoes         enable row level security;

-- Empresas / funcionários: equipe lê; escreve só gestor.
create policy emp_sel on empresas for select to authenticated
  using (id = app_org() or matriz_id = app_org());
create policy emp_wr  on empresas for all to authenticated
  using ((id = app_org() or matriz_id = app_org()) and app_is_gestor())
  with check (app_is_gestor());
create policy fun_sel on funcionarios for select to authenticated
  using (empresa_id in (select id from empresas where id = app_org() or matriz_id = app_org()));
create policy fun_wr  on funcionarios for all to authenticated
  using (app_is_gestor()) with check (app_is_gestor());
create policy lp_all  on logins_pendentes for all to authenticated
  using (app_is_gestor()) with check (app_is_gestor());

-- Cascata: equipe lê; qualquer autenticado da org adiciona (contatos/servidores/setores);
-- entidade nova também (ex.: fornecedor privado digitado à mão).
create policy ent_sel on crm_entidades  for select to authenticated using (org_id = app_org());
create policy ent_wr  on crm_entidades  for all    to authenticated using (org_id = app_org()) with check (org_id = app_org());
create policy set_all on crm_setores    for all to authenticated
  using (exists (select 1 from crm_entidades e where e.id = entidade_id and e.org_id = app_org()))
  with check (exists (select 1 from crm_entidades e where e.id = entidade_id and e.org_id = app_org()));
create policy srv_all on crm_servidores for all to authenticated
  using (exists (select 1 from crm_entidades e where e.id = entidade_id and e.org_id = app_org()))
  with check (exists (select 1 from crm_entidades e where e.id = entidade_id and e.org_id = app_org()));
create policy ct_all  on crm_contatos   for all to authenticated using (true) with check (true);

-- Regras/campanhas: equipe lê; escreve só gestor.
create policy rv_sel  on regras_versoes for select to authenticated using (org_id = app_org());
create policy rv_ins  on regras_versoes for insert to authenticated with check (org_id = app_org() and app_is_gestor());
create policy rv_upd  on regras_versoes for update to authenticated
  using (org_id = app_org() and app_is_gestor()) with check (app_is_gestor());  -- só p/ fechar vigência
create policy cmp_sel on campanhas for select to authenticated using (org_id = app_org());
create policy cmp_wr  on campanhas for all to authenticated
  using (org_id = app_org() and app_is_gestor()) with check (org_id = app_org() and app_is_gestor());

-- Capturas: equipe vê tudo (visão 360 compartilhada); cria quem captura (vira responsável
-- pelo default; trigger impede transferir sem ser gestor); atualiza equipe (estágio/obs).
create policy cap_sel on capturas for select to authenticated using (org_id = app_org());
create policy cap_ins on capturas for insert to authenticated
  with check (org_id = app_org() and (responsavel_id = app_me_id() or app_is_gestor()));
create policy cap_upd on capturas for update to authenticated
  using (org_id = app_org()) with check (org_id = app_org());
create policy part_all on participacoes for all to authenticated
  using (exists (select 1 from capturas c where c.id = captura_id and c.org_id = app_org()))
  with check (exists (select 1 from capturas c where c.id = captura_id and c.org_id = app_org()));
create policy ativ_all on atividades for all to authenticated
  using (exists (select 1 from capturas c where c.id = captura_id and c.org_id = app_org()))
  with check (exists (select 1 from capturas c where c.id = captura_id and c.org_id = app_org()));

-- Apurações: vendedor vê a SUA, gestor vê tudo; INSERE só gestor; SEM update/delete (imutável).
create policy apr_sel on apuracoes for select to authenticated
  using (org_id = app_org() and (app_is_gestor() or funcionario_id = app_me_id()));
create policy apr_ins on apuracoes for insert to authenticated
  with check (org_id = app_org() and app_is_gestor());

-- ============================================================================
-- Depois de rodar:
--   1) python3 tools/load_crm_colaboradores.py          (funcionários da planilha RH)
--   2) python3 tools/load_crm_entidades.py              (cascata: entidades/setores/servidores do painel)
--   3) python3 tools/crm_logins.py --link israel@licitapublica.com.br   (+ provisionar CPFs)
--   4) publicar crm/index.html (GitHub Pages)
-- ============================================================================

-- ============================================================================
-- MIGRAÇÃO v2.1 — lotes do produto + desconto por organização + modalidade
-- (idempotente: pode rodar de novo com segurança)
-- ============================================================================
alter table campanhas add column if not exists lotes jsonb default '[]';
  -- [{nome:'Lote 1', data:'2026-08-31', pres:1200, online:790}, ...]
alter table campanhas add column if not exists desconto_org_pct numeric default 0;
  -- % de desconto POR servidor adicional já capturado da MESMA organização
alter table capturas add column if not exists modalidade text
  check (modalidade in ('presencial','online') or modalidade is null);

-- ============================================================================
-- MIGRAÇÃO v2.2 — busca por nome no Painel 1 em milissegundos (typeahead)
-- pg_trgm permite ilike '%texto%' indexado. Custo: ~100–150MB de disco (GIN).
-- Se o plano free reclamar de espaço, remova com: drop index ix_p1_nome_trgm;
-- ============================================================================
create extension if not exists pg_trgm;
create index if not exists ix_p1_nome_trgm
  on painel1_servidores using gin (nome gin_trgm_ops);

-- ============================================================================
-- MIGRAÇÃO v2.3 — MOTOR DE APURAÇÃO DE COMISSÕES (Fase 2)  [APLICADA 17/07/2026]
-- Venda ganha (captura → fechamento/pos_venda) gera apurações automáticas:
-- 1 por participante (participacoes; sem participações = responsável 100%),
-- com a regra vigente à época (versão + snapshot imutável) e memória de cálculo.
-- Idempotente: 1 apuração por (captura, funcionário) — reapurar não duplica.
-- ============================================================================
create unique index if not exists ux_apur_cap_func on apuracoes(captura_id, funcionario_id);

create or replace function crm_apurar_captura(p_cap uuid) returns int
language plpgsql security definer set search_path = public as $$
declare
  c capturas%rowtype; cp campanhas%rowtype; rv regras_versoes%rowtype;
  base numeric; comp text; fmt_base text; pcttxt text;
  p record; v numeric; mem text; n int := 0; rc int;
begin
  select * into c from capturas where id = p_cap;
  if not found or not c.ativo then return 0; end if;
  select * into cp from campanhas where id = c.campanha_id;
  select * into rv from regras_versoes
    where org_id = c.org_id and vigente_ate is null
    order by versao desc limit 1;
  if rv.versao is null then
    select * into rv from regras_versoes where org_id = c.org_id order by versao desc limit 1;
  end if;
  if rv.versao is null then return 0; end if;   -- sem regra cadastrada: não bloqueia a venda
  base := coalesce(c.valor_contrato, cp.valor_unitario, 0);
  comp := to_char(now() at time zone 'America/Sao_Paulo', 'YYYY-MM');
  fmt_base := replace(to_char(round(base), 'FM999G999G999G999'), ',', '.');
  pcttxt  := replace(rtrim(rtrim(to_char(coalesce(cp.pct_comissao,0),'FM990D99'),'0'),'.'),'.',',');
  for p in
    select * from (
      select funcionario_id, coalesce(rateio_pct,100) as rateio_pct, papel
        from participacoes where captura_id = c.id
      union all
      select c.responsavel_id, 100::numeric, 'responsavel'
       where not exists (select 1 from participacoes where captura_id = c.id)
    ) x
  loop
    v := round(base * coalesce(cp.pct_comissao,0)/100.0 * p.rateio_pct/100.0, 2);
    mem := 'R$ '||fmt_base||' × '||pcttxt||'%'||
           case when p.rateio_pct <> 100
                then ' → '||replace(rtrim(rtrim(to_char(p.rateio_pct,'FM990D99'),'0'),'.'),'.',',')||'% ('||p.papel||')'
                else '' end;
    insert into apuracoes (org_id, captura_id, funcionario_id, competencia, regra_versao, regra_snapshot,
                           base_valor, pct_aplicado, rateio_pct, memoria, valor, apurado_por)
    values (c.org_id, c.id, p.funcionario_id, comp, rv.versao, rv.config,
            base, coalesce(cp.pct_comissao,0), p.rateio_pct, mem, v, app_me_id())
    on conflict (captura_id, funcionario_id) do nothing;
    get diagnostics rc = row_count; n := n + rc;
  end loop;
  return n;
end $$;

-- só o trigger chama (security definer); PostgREST não expõe a apuração manual
revoke execute on function crm_apurar_captura(uuid) from public, anon, authenticated;

create or replace function trg_capturas_apura() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if new.estagio in ('fechamento','pos_venda')
     and coalesce(old.estagio,'') not in ('fechamento','pos_venda') then
    perform crm_apurar_captura(new.id);
  end if;
  return new;
end $$;
drop trigger if exists t_capturas_apura on capturas;
create trigger t_capturas_apura after update on capturas
  for each row execute function trg_capturas_apura();

-- ============================================================================
-- MIGRAÇÃO v4 — PAINEL DE COMISSÕES  [APLICADA 18/07/2026]
-- crm_apurar_pendentes(): varredura de vendas fechadas ainda sem apuração —
-- botão "⚖ Apurar pendentes" do painel. Só gestor/admin (conexão de serviço,
-- auth.uid() null, passa); revogada de anon/public no nível de role, porque
-- anon também tem auth.uid() null e furaria a guarda.
-- ============================================================================
create or replace function crm_apurar_pendentes() returns int
language plpgsql security definer set search_path = public as $$
declare r record; n int := 0;
begin
  if auth.uid() is not null and not app_is_gestor() then
    raise exception 'apenas gestor ou administrador pode apurar comissões';
  end if;
  for r in
    select cp.id from capturas cp
     where cp.ativo
       and cp.estagio in ('fechamento','pos_venda')
       and not exists (select 1 from apuracoes a where a.captura_id = cp.id)
  loop
    n := n + crm_apurar_captura(r.id);
  end loop;
  return n;
end $$;
revoke execute on function crm_apurar_pendentes() from public, anon;
grant execute on function crm_apurar_pendentes() to authenticated;

-- ============================================================================
-- MIGRAÇÃO v5 — ESTORNO + ENDURECIMENTO + EXCLUSÃO ADMIN + GUARDA DE RATEIO
-- [APLICADA 19/07/2026 — migração crm_v5_estorno_guardas_exclusao]
-- (1) venda desfeita (sai de fechamento/pós-venda, vira perdida ou é
--     desativada) gera ESTORNO automático (lançamento negativo, histórico
--     preservado); refechar reapura. 1 estorno por apuração (ux_apur_estorno);
--     reapuração só de quem não tem apuração ATIVA (positiva não estornada).
-- (2) alterar captura (valor, obs, ativo…): só responsável ou gerente/admin.
-- (3) DELETE em capturas: só admin e só SEM apuração (política cap_del + FK).
-- (4) participacoes (rateio): só responsável da captura ou gerente/admin.
-- ============================================================================
alter table apuracoes add column if not exists estorno_de uuid references apuracoes(id);
drop index if exists ux_apur_cap_func;
create unique index if not exists ux_apur_estorno on apuracoes(estorno_de) where estorno_de is not null;

create or replace function crm_apurar_captura(p_cap uuid) returns int
language plpgsql security definer set search_path = public as $$
declare
  c capturas%rowtype; cp campanhas%rowtype; rv regras_versoes%rowtype;
  base numeric; comp text; fmt_base text; pcttxt text;
  p record; v numeric; mem text; n int := 0;
begin
  select * into c from capturas where id = p_cap;
  if not found or not c.ativo then return 0; end if;
  select * into cp from campanhas where id = c.campanha_id;
  select * into rv from regras_versoes
    where org_id = c.org_id and vigente_ate is null
    order by versao desc limit 1;
  if rv.versao is null then
    select * into rv from regras_versoes where org_id = c.org_id order by versao desc limit 1;
  end if;
  if rv.versao is null then return 0; end if;
  base := coalesce(c.valor_contrato, cp.valor_unitario, 0);
  comp := to_char(now() at time zone 'America/Sao_Paulo', 'YYYY-MM');
  fmt_base := replace(to_char(round(base), 'FM999G999G999G999'), ',', '.');
  pcttxt  := replace(rtrim(rtrim(to_char(coalesce(cp.pct_comissao,0),'FM990D99'),'0'),'.'),'.',',');
  for p in
    select * from (
      select funcionario_id, coalesce(rateio_pct,100) as rateio_pct, papel
        from participacoes where captura_id = c.id
      union all
      select c.responsavel_id, 100::numeric, 'responsavel'
       where not exists (select 1 from participacoes where captura_id = c.id)
    ) x
  loop
    if exists (select 1 from apuracoes a
                where a.captura_id = c.id and a.funcionario_id = p.funcionario_id
                  and a.estorno_de is null
                  and not exists (select 1 from apuracoes e where e.estorno_de = a.id)) then
      continue;
    end if;
    v := round(base * coalesce(cp.pct_comissao,0)/100.0 * p.rateio_pct/100.0, 2);
    mem := 'R$ '||fmt_base||' × '||pcttxt||'%'||
           case when p.rateio_pct <> 100
                then ' → '||replace(rtrim(rtrim(to_char(p.rateio_pct,'FM990D99'),'0'),'.'),'.',',')||'% ('||p.papel||')'
                else '' end;
    insert into apuracoes (org_id, captura_id, funcionario_id, competencia, regra_versao, regra_snapshot,
                           base_valor, pct_aplicado, rateio_pct, memoria, valor, apurado_por)
    values (c.org_id, c.id, p.funcionario_id, comp, rv.versao, rv.config,
            base, coalesce(cp.pct_comissao,0), p.rateio_pct, mem, v, app_me_id());
    n := n + 1;
  end loop;
  return n;
end $$;
revoke execute on function crm_apurar_captura(uuid) from public, anon, authenticated;

create or replace function crm_estornar_captura(p_cap uuid) returns int
language plpgsql security definer set search_path = public as $$
declare a record; n int := 0; comp text;
begin
  comp := to_char(now() at time zone 'America/Sao_Paulo', 'YYYY-MM');
  for a in
    select * from apuracoes x
     where x.captura_id = p_cap and x.estorno_de is null
       and not exists (select 1 from apuracoes e where e.estorno_de = x.id)
  loop
    insert into apuracoes (org_id, captura_id, funcionario_id, competencia, regra_versao, regra_snapshot,
                           base_valor, pct_aplicado, rateio_pct, memoria, valor, apurado_por, estorno_de)
    values (a.org_id, a.captura_id, a.funcionario_id, comp, a.regra_versao, a.regra_snapshot,
            a.base_valor, a.pct_aplicado, a.rateio_pct,
            'ESTORNO — '||coalesce(a.memoria,''), -a.valor, app_me_id(), a.id);
    n := n + 1;
  end loop;
  return n;
end $$;
revoke execute on function crm_estornar_captura(uuid) from public, anon, authenticated;

create or replace function trg_capturas_apura() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if new.ativo and new.estagio in ('fechamento','pos_venda')
     and (not coalesce(old.ativo,true) or coalesce(old.estagio,'') not in ('fechamento','pos_venda')) then
    perform crm_apurar_captura(new.id);
  elsif coalesce(old.ativo,true) and coalesce(old.estagio,'') in ('fechamento','pos_venda')
     and (not new.ativo or new.estagio not in ('fechamento','pos_venda')) then
    perform crm_estornar_captura(new.id);
  end if;
  return new;
end $$;

create or replace function trg_capturas_resp() returns trigger
language plpgsql security definer as $$
declare ordem text[] := array['prospeccao','qualificacao','proposta','negociacao','fechamento','pos_venda'];
begin
  if auth.uid() is not null then
    if not (coalesce(old.responsavel_id = app_me_id(), false) or app_is_gestor()) then
      raise exception 'Somente o vendedor responsável ou gerente/admin pode alterar esta captura';
    end if;
    if new.responsavel_id is distinct from old.responsavel_id and not app_is_gestor() then
      raise exception 'Transferência de responsável permitida apenas a gerente/admin';
    end if;
    if new.estagio is distinct from old.estagio then
      if not (coalesce(old.responsavel_id = app_me_id(), false) or app_is_admin()) then
        raise exception 'Somente o vendedor responsável ou um administrador pode avançar o estágio';
      end if;
      if not app_is_admin() and new.estagio <> 'perdida'
         and array_position(ordem, new.estagio) is distinct from array_position(ordem, old.estagio) + 1 then
        raise exception 'Avanço sequencial: da fase % só é possível ir para %',
          old.estagio, coalesce(ordem[array_position(ordem, old.estagio)+1], '(fim do funil)');
      end if;
    end if;
  end if;
  new.atualizado_em := now();
  return new;
end $$;

drop policy if exists cap_del on capturas;
create policy cap_del on capturas for delete to authenticated
  using (org_id = app_org() and app_is_admin()
         and not exists (select 1 from apuracoes a where a.captura_id = capturas.id));

create or replace function trg_participacoes_guard() returns trigger
language plpgsql security definer as $$
declare cid uuid;
begin
  if auth.uid() is not null then
    cid := coalesce(new.captura_id, old.captura_id);
    if not (app_is_gestor() or exists
        (select 1 from capturas c where c.id = cid and c.responsavel_id = app_me_id())) then
      raise exception 'Somente o responsável pela captura ou gerente/admin pode alterar o rateio';
    end if;
  end if;
  if tg_op = 'DELETE' then return old; end if;
  return new;
end $$;
drop trigger if exists t_part_guard on participacoes;
create trigger t_part_guard before insert or update or delete on participacoes
  for each row execute function trg_participacoes_guard();

-- ============================================================================
-- MIGRAÇÃO v6 — RECICLAR LEAD PARA PROSPECÇÃO  [APLICADA 20/07/2026]
-- O vendedor responsável pode DEVOLVER seu próprio lead para 'prospeccao' a
-- qualquer momento (além de avançar +1 fase ou marcar 'perdida'). Admin livre.
-- Se o lead reciclado estava em fechamento/pós-venda (comissão apurada), o
-- estorno automático (v5) zera a comissão ao sair dessas fases. Avanço PARA
-- FRENTE segue sequencial (uma fase por vez).
-- ============================================================================
create or replace function trg_capturas_resp() returns trigger
language plpgsql security definer as $$
declare ordem text[] := array['prospeccao','qualificacao','proposta','negociacao','fechamento','pos_venda'];
begin
  if auth.uid() is not null then
    if not (coalesce(old.responsavel_id = app_me_id(), false) or app_is_gestor()) then
      raise exception 'Somente o vendedor responsável ou gerente/admin pode alterar esta captura';
    end if;
    if new.responsavel_id is distinct from old.responsavel_id and not app_is_gestor() then
      raise exception 'Transferência de responsável permitida apenas a gerente/admin';
    end if;
    if new.estagio is distinct from old.estagio then
      if not (coalesce(old.responsavel_id = app_me_id(), false) or app_is_admin()) then
        raise exception 'Somente o vendedor responsável ou um administrador pode avançar o estágio';
      end if;
      -- não-admin: pode ir +1 fase, marcar 'perdida', OU reciclar para 'prospeccao'
      if not app_is_admin()
         and new.estagio <> 'perdida' and new.estagio <> 'prospeccao'
         and array_position(ordem, new.estagio) is distinct from array_position(ordem, old.estagio) + 1 then
        raise exception 'Avanço sequencial: da fase % só é possível ir para % (ou reciclar para Prospecção / marcar Perdida)',
          old.estagio, coalesce(ordem[array_position(ordem, old.estagio)+1], '(fim do funil)');
      end if;
    end if;
  end if;
  new.atualizado_em := now();
  return new;
end $$;

-- ============================================================================
-- MIGRAÇÃO v7 — LIBERAR SERVIDOR DE VOLTA AO POOL (aba "Todos")  [APLICADA 20/07/2026]
-- "Liberar" um lead = capturas.ativo=false: o servidor sai do funil, some o
-- badge na cascata e volta a aparecer DISPONÍVEL na aba Todos, pronto para nova
-- prospecção. Feito pelo responsável ou admin (trg_capturas_resp já exige
-- responsável/gestor para qualquer alteração; se o lead estava ganho, o estorno
-- automático da v5 zera a comissão ao ficar inativo).
-- A trava de exclusividade por campanha passa a valer só enquanto ATIVO (antes
-- era permanente e barraria recaptura no mesmo servidor+campanha). Continua
-- garantido no máximo 1 captura ATIVA por (campanha, servidor).
-- ============================================================================
drop index if exists ux_cap_camp_srv;
create unique index if not exists ux_cap_camp_srv on capturas(campanha_id, servidor_id) where ativo;

-- ============================================================================
-- MIGRAÇÃO v8 — REALTIME (painel ao vivo entre usuários)  [APLICADA 20/07/2026]
-- Adiciona capturas/participacoes/apuracoes ao publication supabase_realtime.
-- O app assina postgres_changes nessas tabelas (sbc.channel('crm-live'), com
-- sbc.realtime.setAuth(token) — sem o setAuth as mudanças com RLS não chegam)
-- e chama refreshCaps() ao vivo. RLS continua valendo: cada usuário só recebe
-- mudanças das linhas que pode SELECT (mesma org). REPLICA IDENTITY FULL para
-- propagar DELETE/estorno. Idempotente.
-- ============================================================================
do $$
declare t text;
begin
  foreach t in array array['capturas','participacoes','apuracoes'] loop
    if not exists (
      select 1 from pg_publication_rel pr
      join pg_publication p on p.oid = pr.prpubid
      join pg_class c on c.oid = pr.prrelid
      where p.pubname = 'supabase_realtime' and c.relname = t
    ) then
      execute format('alter publication supabase_realtime add table public.%I', t);
    end if;
  end loop;
end $$;
alter table capturas       replica identity full;
alter table participacoes  replica identity full;

-- ============================================================================
-- MIGRAÇÃO v9 — REALTIME p/ CAMPANHAS e REGRAS (completa o painel ao vivo)  [APLICADA 20/07/2026]
-- Adiciona campanhas e regras_versoes ao publication: nova campanha criada pelo
-- admin ou nova versão de regra publicada aparecem ao vivo para todos (o app
-- chama refreshCampsRules() → re-renderiza header/rulecards/rulelog/comissões).
-- Também: os selos da cascata "Todos" são re-sincronizados no refreshCaps()
-- (refreshCascadeBadges). RLS mantém o escopo por org. Idempotente.
-- ============================================================================
do $$
declare t text;
begin
  foreach t in array array['campanhas','regras_versoes'] loop
    if not exists (
      select 1 from pg_publication_rel pr
      join pg_publication p on p.oid = pr.prpubid
      join pg_class c on c.oid = pr.prrelid
      where p.pubname = 'supabase_realtime' and c.relname = t
    ) then
      execute format('alter publication supabase_realtime add table public.%I', t);
    end if;
  end loop;
end $$;
alter table campanhas      replica identity full;
alter table regras_versoes replica identity full;

-- ============================================================================
-- CRM v10 (1ª ONDA — novo modelo de campanha) [APLICADA 22/07/2026]
-- Campanha passa a conter PRODUTOS/SERVIÇOS (campanha_itens), cada um com
-- PLANOS (item_planos) e sua própria métrica de comissão (% ou fixo, com
-- override por plano). Comissão em dois modos: 'total' (1× no fechamento) e
-- 'recorrente_mensal' (mês a mês enquanto o contrato estiver ativo — pg_cron).
-- Produto vende-se ao ÓRGÃO (servidor_id nulo + captura_contatos); serviço/
-- curso, ao SERVIDOR. Meta por item. Só admin cadastra. RETROCOMPATÍVEL:
-- captura sem item_id usa o % único da campanha (comportamento antigo).
-- Migrações aplicadas: v10a estrutura · v10b motor · v10c cron · v10d hardening.
-- ============================================================================

-- ---- v10a: estrutura ----
create table if not exists campanha_itens (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null default app_org(),
  campanha_id uuid not null references campanhas(id) on delete cascade,
  nome text not null,
  categoria text not null default 'produto' check (categoria in ('produto','servico','curso')),
  nivel_venda text not null default 'orgao' check (nivel_venda in ('orgao','servidor')),
  cobranca text not null default 'unica' check (cobranca in ('unica','mensal')),
  comissao_modo text not null default 'total' check (comissao_modo in ('total','recorrente_mensal')),
  comissao_tipo text not null default 'percentual' check (comissao_tipo in ('percentual','fixo')),
  comissao_valor numeric not null default 0,
  meta_valor numeric,
  ordem int default 0,
  ativo boolean default true,
  criado_por uuid references funcionarios(id) default app_me_id(),
  criado_em timestamptz default now()
);
create index if not exists ix_citem_camp on campanha_itens(campanha_id);

create table if not exists item_planos (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null default app_org(),
  item_id uuid not null references campanha_itens(id) on delete cascade,
  nome text not null,
  preco numeric not null default 0,
  unidade text not null default 'unica' check (unidade in ('unica','mensal')),
  meses_padrao int,
  modalidade text check (modalidade in ('presencial','online') or modalidade is null),
  vigencia_ate date,
  comissao_ovr_tipo text check (comissao_ovr_tipo in ('percentual','fixo') or comissao_ovr_tipo is null),
  comissao_ovr_valor numeric,
  ordem int default 0,
  ativo boolean default true
);
create index if not exists ix_iplano_item on item_planos(item_id);

create table if not exists captura_contatos (
  id uuid primary key default gen_random_uuid(),
  captura_id uuid not null references capturas(id) on delete cascade,
  servidor_id uuid not null references crm_servidores(id) on delete cascade,
  papel text default 'contato',
  criado_por uuid references funcionarios(id) default app_me_id(),
  criado_em timestamptz default now(),
  unique (captura_id, servidor_id)
);
create index if not exists ix_capct_cap on captura_contatos(captura_id);

alter table capturas add column if not exists item_id uuid references campanha_itens(id);
alter table capturas add column if not exists plano_id uuid references item_planos(id);
alter table capturas add column if not exists meses_contrato int;
alter table capturas add column if not exists contrato_ativo boolean;
alter table capturas add column if not exists contrato_desde date;
alter table capturas add column if not exists contrato_ate date;
alter table capturas alter column servidor_id drop not null;

drop index if exists ux_cap_servidor_ativo;
drop index if exists ux_cap_camp_srv;
create unique index if not exists ux_cap_legacy_srv on capturas(servidor_id)
  where ativo and item_id is null and servidor_id is not null;
create unique index if not exists ux_cap_item_srv on capturas(campanha_id, item_id, servidor_id)
  where ativo and item_id is not null and servidor_id is not null;
create unique index if not exists ux_cap_item_org on capturas(campanha_id, item_id, entidade_id)
  where ativo and item_id is not null and servidor_id is null;

alter table apuracoes add column if not exists tipo text not null default 'fechamento'
  check (tipo in ('fechamento','recorrente','estorno'));

alter table campanha_itens   enable row level security;
alter table item_planos      enable row level security;
alter table captura_contatos enable row level security;
drop policy if exists citem_sel on campanha_itens;
drop policy if exists citem_wr  on campanha_itens;
create policy citem_sel on campanha_itens for select to authenticated using (org_id = app_org());
create policy citem_wr  on campanha_itens for all to authenticated
  using (org_id = app_org() and app_is_admin()) with check (org_id = app_org() and app_is_admin());
drop policy if exists iplano_sel on item_planos;
drop policy if exists iplano_wr  on item_planos;
create policy iplano_sel on item_planos for select to authenticated using (org_id = app_org());
create policy iplano_wr  on item_planos for all to authenticated
  using (org_id = app_org() and app_is_admin()) with check (org_id = app_org() and app_is_admin());
drop policy if exists capct_sel on captura_contatos;
drop policy if exists capct_wr  on captura_contatos;
create policy capct_sel on captura_contatos for select to authenticated
  using (exists (select 1 from capturas c where c.id = captura_id and c.org_id = app_org()));
create policy capct_wr on captura_contatos for all to authenticated
  using (exists (select 1 from capturas c where c.id = captura_id and c.org_id = app_org()
                 and (coalesce(c.responsavel_id = app_me_id(),false) or app_is_gestor())))
  with check (exists (select 1 from capturas c where c.id = captura_id and c.org_id = app_org()
                 and (coalesce(c.responsavel_id = app_me_id(),false) or app_is_gestor())));
-- realtime: alter publication supabase_realtime add table campanha_itens, item_planos, captura_contatos;
-- (+ replica identity full nas três) — ver migração aplicada.

-- ---- v10b: motor ----
create unique index if not exists ux_apur_recorrente
  on apuracoes(captura_id, funcionario_id, competencia) where tipo = 'recorrente' and estorno_de is null;

create or replace function crm_grava_apur(p_cap uuid, base numeric, ctipo text, cval numeric, comp text, p_tipo text)
returns int language plpgsql security definer set search_path=public as $$
declare c capturas%rowtype; rv regras_versoes%rowtype; p record; v numeric; mem text; n int:=0;
  fmt_base text; fmt_cval text; pcttxt text; metric_lbl text;
begin
  select * into c from capturas where id=p_cap;
  select * into rv from regras_versoes where org_id=c.org_id and vigente_ate is null order by versao desc limit 1;
  if rv.versao is null then select * into rv from regras_versoes where org_id=c.org_id order by versao desc limit 1; end if;
  if rv.versao is null then return 0; end if;
  fmt_base := replace(to_char(round(base),'FM999G999G999G999'),',','.');
  fmt_cval := replace(to_char(round(cval),'FM999G999G999G999'),',','.');
  pcttxt   := replace(rtrim(rtrim(to_char(coalesce(cval,0),'FM990D99'),'0'),'.'),'.',',');
  for p in select * from (
      select funcionario_id, coalesce(rateio_pct,100) as rateio_pct, papel from participacoes where captura_id=c.id
      union all select c.responsavel_id, 100::numeric, 'responsavel' where not exists(select 1 from participacoes where captura_id=c.id)
    ) x
  loop
    if exists(select 1 from apuracoes a where a.captura_id=c.id and a.funcionario_id=p.funcionario_id
              and a.competencia=comp and a.tipo=p_tipo and a.estorno_de is null
              and not exists(select 1 from apuracoes e where e.estorno_de=a.id)) then continue; end if;
    if ctipo='fixo' then
      v := round(coalesce(cval,0) * p.rateio_pct/100.0, 2); metric_lbl := 'R$ '||fmt_cval||' (fixo)';
    else
      v := round(base * coalesce(cval,0)/100.0 * p.rateio_pct/100.0, 2); metric_lbl := 'R$ '||fmt_base||' × '||pcttxt||'%';
    end if;
    mem := metric_lbl || case when p_tipo='recorrente' then ' · mensal '||comp else '' end
         || case when p.rateio_pct<>100 then ' → '||replace(rtrim(rtrim(to_char(p.rateio_pct,'FM990D99'),'0'),'.'),'.',',')||'% ('||p.papel||')' else '' end;
    insert into apuracoes(org_id,captura_id,funcionario_id,competencia,regra_versao,regra_snapshot,
                          base_valor,pct_aplicado,rateio_pct,memoria,valor,apurado_por,tipo)
    values(c.org_id,c.id,p.funcionario_id,comp,rv.versao,rv.config,
           base, case when ctipo='fixo' then null else cval end, p.rateio_pct, mem, v, app_me_id(), p_tipo);
    n := n+1;
  end loop;
  return n;
end $$;
revoke execute on function crm_grava_apur(uuid,numeric,text,numeric,text,text) from public, anon, authenticated;

create or replace function crm_apurar_captura(p_cap uuid) returns int
language plpgsql security definer set search_path=public as $$
declare c capturas%rowtype; cp campanhas%rowtype; it campanha_itens%rowtype; pl item_planos%rowtype;
  base numeric; ctipo text; cval numeric; comp text; meses int;
begin
  select * into c from capturas where id=p_cap;
  if not found or not c.ativo then return 0; end if;
  comp := to_char(now() at time zone 'America/Sao_Paulo','YYYY-MM');
  if c.item_id is not null then
    select * into it from campanha_itens where id=c.item_id;
    if c.plano_id is not null then select * into pl from item_planos where id=c.plano_id; end if;
    if it.comissao_modo='recorrente_mensal' then return 0; end if;
    meses := coalesce(c.meses_contrato, pl.meses_padrao, 1);
    if coalesce(pl.unidade,'unica')='mensal' then base := coalesce(pl.preco,0)*meses;
    else base := coalesce(pl.preco, c.valor_contrato, 0); end if;
    ctipo := coalesce(pl.comissao_ovr_tipo, it.comissao_tipo, 'percentual');
    cval  := coalesce(pl.comissao_ovr_valor, it.comissao_valor, 0);
  else
    select * into cp from campanhas where id=c.campanha_id;
    base := coalesce(c.valor_contrato, cp.valor_unitario, 0);
    ctipo := 'percentual'; cval := coalesce(cp.pct_comissao,0);
  end if;
  return crm_grava_apur(p_cap, base, ctipo, cval, comp, 'fechamento');
end $$;
revoke execute on function crm_apurar_captura(uuid) from public, anon, authenticated;

create or replace function crm_apurar_recorrente(p_cap uuid, p_comp text) returns int
language plpgsql security definer set search_path=public as $$
declare c capturas%rowtype; it campanha_itens%rowtype; pl item_planos%rowtype; ctipo text; cval numeric;
begin
  select * into c from capturas where id=p_cap;
  if not found or not c.ativo or not coalesce(c.contrato_ativo,false) then return 0; end if;
  if c.item_id is null then return 0; end if;
  select * into it from campanha_itens where id=c.item_id;
  if it.comissao_modo <> 'recorrente_mensal' then return 0; end if;
  if c.contrato_desde is not null and p_comp < to_char(c.contrato_desde,'YYYY-MM') then return 0; end if;
  if c.contrato_ate   is not null and p_comp > to_char(c.contrato_ate,'YYYY-MM')   then return 0; end if;
  select * into pl from item_planos where id=c.plano_id;
  ctipo := coalesce(pl.comissao_ovr_tipo, it.comissao_tipo, 'percentual');
  cval  := coalesce(pl.comissao_ovr_valor, it.comissao_valor, 0);
  return crm_grava_apur(p_cap, coalesce(pl.preco,0), ctipo, cval, p_comp, 'recorrente');
end $$;
revoke execute on function crm_apurar_recorrente(uuid,text) from public, anon, authenticated;

create or replace function crm_apurar_recorrentes(p_comp text default null) returns int
language plpgsql security definer set search_path=public as $$
declare comp text; r record; n int:=0;
begin
  if auth.uid() is not null and not app_is_gestor() then
    raise exception 'apenas gestor/admin pode apurar comissões recorrentes';
  end if;
  comp := coalesce(p_comp, to_char(now() at time zone 'America/Sao_Paulo','YYYY-MM'));
  for r in
    select c.id from capturas c
     where c.ativo and coalesce(c.contrato_ativo,false) and c.estagio in ('fechamento','pos_venda')
       and exists(select 1 from campanha_itens it where it.id=c.item_id and it.comissao_modo='recorrente_mensal')
       and (c.contrato_desde is null or comp >= to_char(c.contrato_desde,'YYYY-MM'))
       and (c.contrato_ate   is null or comp <= to_char(c.contrato_ate,'YYYY-MM'))
  loop n := n + crm_apurar_recorrente(r.id, comp); end loop;
  return n;
end $$;
revoke execute on function crm_apurar_recorrentes(text) from public, anon, authenticated;

create or replace function crm_estornar_captura(p_cap uuid) returns int
language plpgsql security definer set search_path=public as $$
declare a record; n int := 0; comp text;
begin
  comp := to_char(now() at time zone 'America/Sao_Paulo','YYYY-MM');
  for a in select * from apuracoes x
     where x.captura_id=p_cap and x.tipo='fechamento' and x.estorno_de is null
       and not exists(select 1 from apuracoes e where e.estorno_de=x.id)
  loop
    insert into apuracoes(org_id,captura_id,funcionario_id,competencia,regra_versao,regra_snapshot,
                          base_valor,pct_aplicado,rateio_pct,memoria,valor,apurado_por,estorno_de,tipo)
    values(a.org_id,a.captura_id,a.funcionario_id,comp,a.regra_versao,a.regra_snapshot,
           a.base_valor,a.pct_aplicado,a.rateio_pct,'ESTORNO — '||coalesce(a.memoria,''),-a.valor,app_me_id(),a.id,'estorno');
    n := n+1;
  end loop;
  return n;
end $$;
revoke execute on function crm_estornar_captura(uuid) from public, anon, authenticated;

create or replace function trg_capturas_contrato() returns trigger
language plpgsql security definer set search_path=public as $$
begin
  if new.item_id is not null and new.ativo and new.estagio in ('fechamento','pos_venda')
     and exists(select 1 from campanha_itens it where it.id=new.item_id and it.comissao_modo='recorrente_mensal') then
    if new.contrato_ativo is null then
      new.contrato_ativo := true;
      new.contrato_desde := coalesce(new.contrato_desde,(now() at time zone 'America/Sao_Paulo')::date);
    end if;
  end if;
  if tg_op='UPDATE' then
    if coalesce(old.contrato_ativo,false) and not coalesce(new.contrato_ativo,false) and new.contrato_ate is null then
      new.contrato_ate := (now() at time zone 'America/Sao_Paulo')::date;
    elsif not coalesce(old.contrato_ativo,false) and coalesce(new.contrato_ativo,false) then
      new.contrato_ate := null;
      new.contrato_desde := coalesce(new.contrato_desde,(now() at time zone 'America/Sao_Paulo')::date);
    end if;
  end if;
  return new;
end $$;
revoke execute on function trg_capturas_contrato() from public, anon, authenticated;
drop trigger if exists t_capturas_contrato on capturas;
create trigger t_capturas_contrato before insert or update on capturas
  for each row execute function trg_capturas_contrato();

create or replace function trg_capturas_apura() returns trigger
language plpgsql security definer set search_path=public as $$
declare recor boolean;
begin
  recor := new.item_id is not null and exists(select 1 from campanha_itens it where it.id=new.item_id and it.comissao_modo='recorrente_mensal');
  if new.ativo and new.estagio in ('fechamento','pos_venda')
     and (not coalesce(old.ativo,true) or coalesce(old.estagio,'') not in ('fechamento','pos_venda')) then
    if recor then perform crm_apurar_recorrente(new.id, to_char(now() at time zone 'America/Sao_Paulo','YYYY-MM'));
    else perform crm_apurar_captura(new.id); end if;
  elsif coalesce(old.ativo,true) and coalesce(old.estagio,'') in ('fechamento','pos_venda')
     and (not new.ativo or new.estagio not in ('fechamento','pos_venda')) then
    perform crm_estornar_captura(new.id);
  end if;
  return new;
end $$;
revoke execute on function trg_capturas_apura() from public, anon, authenticated;

-- ---- v10c: rotina mensal automática (pg_cron) ----
create extension if not exists pg_cron;
select cron.schedule('crm-recorrentes-mensal','0 6 1 * *',$$select crm_apurar_recorrentes()$$);

-- ============================================================================
-- CRM v11 — cor do bloco da campanha + configuração da regra de comissão  [APLICADA 22/07/2026]
-- regra_tipo/regra_config guardam os parâmetros das regras (progressiva níveis+%,
-- pós-meta %, individual meta+% por vendedor). NÃO entram na apuração ainda — a
-- forma de combinar com a comissão por item precisa ser definida.
-- ============================================================================
alter table campanhas add column if not exists cor text;
alter table campanhas add column if not exists regra_tipo text
  check (regra_tipo in ('progressiva','pos_meta','individual') or regra_tipo is null);
alter table campanhas add column if not exists regra_config jsonb default '{}'::jsonb;

-- ============================================================================
-- CRM v12 — REGRA DE COMISSÃO "SOMA POR CIMA" + majoração cliente novo  [APLICADA 22/07/2026]
-- comissão por vendedor = comissão do item + base×(% da regra) + base×(% cliente novo)
--   progressiva → % do NÍVEL do vendedor; pós-meta → % se vendido da campanha ≥ meta;
--   individual → % se vendido do vendedor ≥ meta dele; cliente novo → % se entidade não-'base'.
-- Recorrente: base = mensalidade. Ver crm_regra_bonus_pct + crm_grava_apur (migração aplicada).
-- ============================================================================
alter table campanhas add column if not exists cliente_novo_pct numeric;
-- crm_regra_bonus_pct(capturas,uuid) e crm_grava_apur reescritos para somar o bônus por participante.

-- ============================================================================
-- CRM v14 — arquivamento de campanha (soft delete)  [APLICADA 22/07/2026]
-- Excluir campanha = arquivar: sai das listagens (arquivada_em is null filtra),
-- mas dados/capturas/comissões são preservados. App confirma com a senha do admin
-- (re-login) antes de arquivar; RLS cmp_wr (gestor) é a trava real.
-- ============================================================================
alter table campanhas add column if not exists arquivada_em timestamptz;
create index if not exists ix_camp_arquivada on campanhas(arquivada_em) where arquivada_em is null;

-- ============================================================================
-- CRM v15 (2ª ONDA) — ENGINE DE BÔNUS SURPRESA  [APLICADA 22/07/2026]
-- campanha_bonus (config oculta) + bonus_conquistas (revelação imutável).
-- Regras: % sobre o VENDIDO do vendedor; top N por vendido (desempate: qtd de
-- contratos; 3º critério 'habilitantes por cidade' PENDENTE de definição);
-- revela quando a meta cai com vendas em status VENDIDO (fechamento/pós-venda);
-- meta_equipe revela p/ todos (nomeando os ganhadores); prêmio físico = só
-- conquista (sem R$), com marcação de entregue. RLS: só gestor/admin lê a config
-- (protege a surpresa); vendedor vê a SUA conquista + selo via crm_tem_bonus.
-- Ver funções crm_avaliar_bonus/crm_conceder_bonus/crm_vendido_vendedor/crm_tem_bonus
-- e o gatilho trg_capturas_apura (reavalia no fechamento). Migração aplicada.
-- ============================================================================
create table if not exists campanha_bonus (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null default app_org(),
  campanha_id uuid not null references campanhas(id) on delete cascade,
  descricao text,
  gatilho text not null default 'meta_equipe' check (gatilho in ('meta_equipe','meta_vendedor','top_vendedores')),
  meta_valor numeric, top_n int default 2,
  tipo text not null default 'fixo' check (tipo in ('percentual','fixo','premio')),
  valor numeric, premio_desc text,
  escopo text not null default 'todos' check (escopo in ('todos','individual')),
  funcionario_id uuid references funcionarios(id),
  ativo boolean default true,
  criado_por uuid references funcionarios(id) default app_me_id(), criado_em timestamptz default now()
);
create table if not exists bonus_conquistas (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null default app_org(),
  bonus_id uuid not null references campanha_bonus(id) on delete cascade,
  campanha_id uuid not null references campanhas(id) on delete cascade,
  funcionario_id uuid not null references funcionarios(id),
  competencia text, tipo text, valor numeric default 0, base_valor numeric, premio_desc text,
  revelado_em timestamptz default now(), entregue boolean default false, entregue_em timestamptz,
  unique (bonus_id, funcionario_id)
);
-- funções crm_vendido_vendedor / crm_conceder_bonus / crm_avaliar_bonus / crm_tem_bonus
-- + trg_capturas_apura estendido + RLS (cbonus_sel gestor, cbonus_wr admin, bconq_sel own/gestor,
--   bconq_upd gestor) + realtime nas 2 tabelas — ver migração aplicada (crm_v15_engine_bonus).

-- ============================================================================
-- CRM v17 — anexar arquivo funcional (Supabase Storage)  [APLICADA 22/07/2026]
-- Bucket público 'crm-anexos' (leitura pública via URL; escrita só admin).
-- O botão "＋ Anexar" faz upload real e o chip do anexo vira link clicável.
-- ============================================================================
insert into storage.buckets (id, name, public) values ('crm-anexos','crm-anexos', true)
  on conflict (id) do update set public=excluded.public;
create policy "crm_anexos_read"   on storage.objects for select using (bucket_id='crm-anexos');
create policy "crm_anexos_insert" on storage.objects for insert to authenticated with check (bucket_id='crm-anexos' and app_is_admin());
create policy "crm_anexos_update" on storage.objects for update to authenticated using (bucket_id='crm-anexos' and app_is_admin());
create policy "crm_anexos_delete" on storage.objects for delete to authenticated using (bucket_id='crm-anexos' and app_is_admin());

-- ============================================================================
-- CRM v20 — LOG DE ACESSO (auditoria de sigilo)  [APLICADA 22/07/2026]
-- Registra quem abriu o quê e quando (login, abrir lead/360, abrir comissões).
-- Insert liberado ao autenticado, mas um trigger FORÇA funcionario_id/org_id
-- (impede forjar identidade); leitura só gestor/admin. Obs.: INSERT ... RETURNING
-- dispara a policy de SELECT — por isso o app faz insert simples (sem select).
-- ============================================================================
create table if not exists crm_acessos (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null default app_org(),
  funcionario_id uuid default app_me_id(),
  evento text, alvo text, em timestamptz default now()
);
create index if not exists ix_acessos_em on crm_acessos(em desc);
alter table crm_acessos enable row level security;
create or replace function trg_acessos_stamp() returns trigger
language plpgsql security definer set search_path=public as $$
begin
  new.funcionario_id := app_me_id();
  new.org_id := coalesce(app_org(), new.org_id);
  new.em := coalesce(new.em, now());
  return new;
end $$;
revoke execute on function trg_acessos_stamp() from public, anon, authenticated;
drop trigger if exists t_acessos_stamp on crm_acessos;
create trigger t_acessos_stamp before insert on crm_acessos for each row execute function trg_acessos_stamp();
drop policy if exists acessos_ins on crm_acessos;
drop policy if exists acessos_sel on crm_acessos;
create policy acessos_ins on crm_acessos for insert to authenticated with check (true);
create policy acessos_sel on crm_acessos for select to authenticated using (org_id = app_org() and app_is_gestor());

-- ============================================================================
-- CRM v22 — busca de servidores rápida  [APLICADA 23/07/2026]
-- crm_buscar_servidores fazia 'order by p.nome' sobre ilike '%termo%'; para
-- termo comum (ex.: 'maria' = 720k matches num painel1 de 5,8M) isso ordenava
-- tudo antes do LIMIT (~49s) → timeout no PostgREST → busca voltava vazia no app.
-- Trocado por 'order by p.id' (o planner para cedo no LIMIT: typeahead ~0,2s).
-- App: applyAll usa p_limit:200 (era 1000) e degrada com timeout de forma graciosa.
-- ============================================================================
-- (ver definição completa de crm_buscar_servidores na migração crm_v22_busca_rapida:
--  idêntica à anterior, apenas 'order by p.id' no lugar de 'order by p.nome')

-- ============================================================================
-- CRM v23 — busca por nome encontra TODO servidor do Painel 1  [APLICADA 24/07/2026]
-- Bug: crm_buscar_servidores fazia INNER JOIN em crm_entidades pelo entidade_id.
-- Mas 87% dos 8,4M servidores do Painel 1 estão SEM entidade_id (ex.: NELSON DE
-- ALMEIDA ASSAD, cuja Prefeitura nem está no CRM — só a Câmara está) → sumiam.
-- FIX: LEFT JOIN resolvendo a entidade por IBGE + poder (câmara×resto, do campo
-- p.orgao); quando o órgão não está no CRM, devolve o dado do próprio Painel 1
-- (orgao, uf, esfera, município via ibge_populacao). loadP1 (p_entidade) também
-- passa a casar por ibge+poder (mostra todos os servidores do órgão, não só os
-- linkados). Busca por nome SEM order (planner para cedo no LIMIT — 'ana paula'
-- caía de 7s p/ 0,3s); ordena por id só no loadP1 (paginação estável).
-- Ver definição completa em crm_v23_busca_left_join_ibge + crm_v23b_busca_order_condicional.

-- ─────────────────────────────────────────────────────────────────────────────
-- crm_v24_materializar_painel1 / crm_v24b_materializar_fix (2026-07-24)
-- "Capturar servidores de órgãos que ainda não estão no CRM".
-- Contexto: 87% dos 8,4M servidores do Painel 1 têm entidade_id nulo e muitos
-- órgãos (ex.: Prefeitura de São José da Barra / NELSON DE ALMEIDA ASSAD) não
-- existem em crm_entidades — só a Câmara existia. A busca (v23) já resolvia a
-- entidade por ibge+poder para EXIBIR, mas não havia como CAPTURAR o servidor.
--
-- RPC crm_materializar_painel1(p_painel1 bigint) SECURITY DEFINER:
--   1. lê a linha do painel1_servidores;
--   2. deriva o poder pelo nome do órgão (ilike '%c_mara%' → Legislativo);
--   3. acha a entidade do org atual por cod_ibge + poder; se não houver, CRIA
--      (nome=orgao, município do ibge_populacao, esfera initcap, tipo_orgao
--      Prefeitura/Câmara, area Gestão Pública/Legislativo, fonte='painel1');
--   4. materializa o servidor em crm_servidores (dedup por painel1_id | cpf |
--      nome dentro da entidade), origem='painel1', copiando cargo/email/telefone;
--   5. retorna (servidor_id, entidade_id, entidade_nome). Idempotente.
--   grant apenas a authenticated (revoke public/anon) → respeita RLS por org
--   via app_org(). App: botão ⊕ em cada resultado da busca (sugPaint/suggest
--   carregam painel1_id) chama a RPC, injeta um SVREG sintético e abre a captura.
-- Correção v24b: a coluna de saída entidade_id sombreava crm_servidores.entidade_id
--   ("column reference entidade_id is ambiguous") → qualificado com alias (s.).

-- ─────────────────────────────────────────────────────────────────────────────
-- crm_v25_split_majoracao_oculta (2026-07-24)
-- Painel de comissões POR VENDEDOR (sigilo) + majoração cliente-novo oculta.
-- Motivação: a "majoração para cliente novo" deve ser oculta do vendedor
-- ("por enquanto não mostrar"), mas crm_regra_bonus_pct a somava junto ao bônus
-- de regra (progressiva/pós-meta/individual) num único pct — que ia parar na
-- memoria ("+X% regra") e em pct_aplicado, vazando para a tela do vendedor.
--   • apuracoes.majoracao_oculta numeric not null default 0 (nova coluna).
--   • crm_regra_bonus_pct(c,fid): agora só o bônus VISÍVEL (removido o bloco de
--     cliente novo).
--   • crm_majoracao_oculta(c): nova — só a % de cliente novo (entidade tipo_cliente
--     <> 'base' e campanhas.cliente_novo_pct <> 0).
--   • crm_grava_apur: valor/memoria/pct_aplicado ficam só com o visível; a parte
--     oculta (base×cliente_novo% × rateio) vai para majoracao_oculta. Total real a
--     pagar = valor + majoracao_oculta (o gestor soma; o vendedor vê só valor).
-- App (crm/index.html):
--   • rebuildComm só monta a linha do próprio vendedor quando !GESTOR
--     (TEAM.filter …&&(GESTOR||t.id===MEID)); antes montava a prevista de TODOS os
--     colegas a partir de CAPS (capturas são visíveis a todo o org) → vazamento.
--   • KPIs "vendido/ganhas/meta" escopados ao próprio vendedor (meta individual);
--     título vira "Minhas comissões · sigilo".
--   • gestor vê "+ R$ x cliente novo (oculto)" na memória e o total no valor;
--     vendedor não. window.MEID = funcionário logado.
-- Nota de robustez: a coluna majoracao_oculta trafega no select do vendedor (RLS é
--   por linha, não por coluna); o ocultamento hoje é na UI. Hardening futuro: RPC
--   SECURITY DEFINER devolvendo projeção redigida p/ perfil vendedor.

-- ─────────────────────────────────────────────────────────────────────────────
-- crm_v26_drenar_logins + crm_v26c_cron (2026-07-24)
-- Fecha o buraco do provisionamento de login da equipe. Sintoma: vendedora
-- Kathellyn (e 12 dos 15 funcionários) não logava. Causa: o app, ao salvar
-- colaborador com CPF+senha, só ENFILEIRA em logins_pendentes; a criação da conta
-- no Auth é um passo server-side (tools/crm_logins.py) que raramente rodava — a
-- fila ficava parada. Só Israel e Kelly tinham conta.
-- Solução escolhida (SQL + cron; deploy de Edge Function estava bloqueado):
--   • public.crm_drenar_logins() SECURITY DEFINER: para cada linha de
--     logins_pendentes, deriva o e-mail alias cpf<digitos>@crm.plenumbrasil.com.br,
--     e — se o funcionário já tem conta (ou existe conta com o e-mail) — troca a
--     senha (bcrypt $2a$10$ via extensions.crypt/gen_salt) e confirma o e-mail;
--     senão CRIA a conta escrevendo direto em auth.users + auth.identities
--     (espelha o formato do GoTrue: aud/role='authenticated', instance_id zero,
--     raw_app_meta_data provider email, identity_data sub/email, provider_id=uid).
--     Vincula funcionarios.auth_user_id e apaga a linha da fila. Idempotente.
--   • cron.schedule('crm-drenar-logins','* * * * *', …) drena a cada minuto.
--   • execute revogado de public/anon/authenticated (só o cron/postgres chama).
--   • App: mensagem do dbSaveFunc trocada de "rode tools/crm_logins.py" para
--     "login provisionado automaticamente (até 1 min)".
-- Cuidados do schema do GoTrue nesta versão: auth.users.confirmed_at e
--   auth.identities.email são GERADAS (não inserir); os 4 tokens sem default
--   (confirmation_token/recovery_token/email_change_token_new/email_change) recebem
--   '' p/ evitar erro de NULL→string no login. Validado ponta a ponta: conta criada
--   por SQL faz login real (grant_type=password) ✓, senha errada 400 ✓, troca de
--   senha ✓. RISCO conhecido: escreve em tabelas internas do Auth — se o Supabase
--   mudar o schema do GoTrue, revisar esta função (alternativa robusta = Edge
--   Function provisionar-logins via API oficial, quando o deploy for liberado).
