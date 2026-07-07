-- ============================================================================
-- MIGRAÇÃO v3 — REGISTRO-OURO DO SERVIDOR
-- Painel 1 vira a espinha dorsal (1,36M), com vínculo à entidade canônica,
-- dedup, razão de contatos incremental (validado por tipo) e RPCs de busca
-- unificada (cascata, typeahead e critérios de campanha usam a MESMA função).
--
-- Rodar no SQL Editor. As etapas 2–3 percorrem 1,36M de linhas: ~1 a 5 min.
-- ============================================================================
set statement_timeout = '30min';

create extension if not exists unaccent;
create extension if not exists pg_trgm;

-- ========================= 1. ESPINHA: vínculo + dedup =========================
alter table painel1_servidores add column if not exists entidade_id uuid references crm_entidades(id);
alter table painel1_servidores add column if not exists dup_of bigint;
create index if not exists ix_p1_entidade on painel1_servidores(entidade_id);
create index if not exists ix_p1_cpf on painel1_servidores(cpf) where cpf is not null;
create index if not exists ix_p1_nome_trgm on painel1_servidores using gin (nome gin_trgm_ops);
alter table crm_servidores add column if not exists painel1_id bigint;

-- ========================= 2. CROSSWALK ibge+órgão -> entidade =========================
-- câmaras
update painel1_servidores p set entidade_id = e.id
from crm_entidades e
where p.entidade_id is null and e.cod_ibge = p.ibge
  and unaccent(coalesce(p.orgao,'')) ilike '%CAMARA%'
  and e.tipo_orgao ilike '%mara%';
-- prefeituras / município
update painel1_servidores p set entidade_id = e.id
from crm_entidades e
where p.entidade_id is null and e.cod_ibge = p.ibge
  and unaccent(coalesce(p.orgao,'')) not ilike '%CAMARA%'
  and (unaccent(coalesce(p.orgao,'')) ilike '%PREFEITURA%'
       or unaccent(coalesce(p.orgao,'')) ilike '%MUNICIPIO%')
  and e.tipo_orgao = 'Prefeitura';
-- fundos de saúde e institutos de previdência (quando a entidade existe no CRM)
update painel1_servidores p set entidade_id = e.id
from crm_entidades e
where p.entidade_id is null and e.cod_ibge = p.ibge
  and ((unaccent(coalesce(p.orgao,'')) ilike '%SAUDE%' and e.tipo_orgao = 'Fundo de Saúde')
    or (unaccent(coalesce(p.orgao,'')) ilike '%PREVID%' and e.tipo_orgao = 'Instituto de Previdência'));

-- ========================= 3. DEDUP exato (linhas idênticas) =========================
update painel1_servidores p set dup_of = k.keep
from (
  select min(id) as keep, ibge, orgao, nome,
         coalesce(cpf,'') c0, coalesce(matricula,'') m0,
         coalesce(setor,'') s0, coalesce(cargo_funcao,'') g0
  from painel1_servidores
  group by ibge, orgao, nome, coalesce(cpf,''), coalesce(matricula,''),
           coalesce(setor,''), coalesce(cargo_funcao,'')
  having count(*) > 1
) k
where p.ibge = k.ibge and p.orgao = k.orgao and p.nome = k.nome
  and coalesce(p.cpf,'') = k.c0 and coalesce(p.matricula,'') = k.m0
  and coalesce(p.setor,'') = k.s0 and coalesce(p.cargo_funcao,'') = k.g0
  and p.id <> k.keep;

-- ========================= 4. RAZÃO DE CONTATOS (incremental, validado) =========================
create table if not exists servidor_contatos (
  id uuid primary key default gen_random_uuid(),
  cpf text,                                   -- chave da PESSOA (dígitos) — mascarar na exibição
  painel1_id bigint,                          -- vínculo específico (opcional)
  entidade_id uuid references crm_entidades(id) on delete set null,
  tipo text not null,                         -- email | telefone | celular | rede social | observacao | ...
  valor text not null,
  valor_norm text,
  rede text, complemento text,
  fonte text not null default 'crm',          -- pessoas_obras | painel6 | crm:<usuario> | enriquecimento:<x>
  grau_confianca text default 'B',
  status text not null default 'ativo' check (status in ('ativo','verificado','suspeito','invalido','obsoleto')),
  motivo text,
  origem_input text not null default 'manual' check (origem_input in ('manual','carga')),
  data_coleta date default current_date,
  visto_em timestamptz default now(),
  criado_por uuid default app_me_id(),
  criado_em timestamptz default now(),
  check (cpf is not null or painel1_id is not null or entidade_id is not null)
);
create unique index if not exists ux_svct_fato on servidor_contatos
  (coalesce(cpf,''), coalesce(entidade_id::text,''), tipo, valor_norm);
create index if not exists ix_svct_cpf on servidor_contatos(cpf);

-- validação/normalização por tipo (telefone com DDD, email RFC, CPF com DV)
create or replace function norm_contato(p_tipo text, p_valor text,
  out ok boolean, out norm text, out tipo_out text, out motivo text)
language plpgsql immutable as $$
declare d text; a int; s1 int:=0; s2 int:=0; i int;
begin
  tipo_out := lower(unaccent(coalesce(p_tipo,'contato')));
  if tipo_out like '%mail%' then tipo_out:='email';
  elsif tipo_out like '%celular%' or tipo_out like '%whats%' then tipo_out:='celular';
  elsif tipo_out like '%tele%' or tipo_out like '%fone%' then tipo_out:='telefone';
  end if;
  ok := true;
  if tipo_out = 'email' then
    norm := lower(trim(p_valor));
    ok := norm ~ '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$';
    if not ok then motivo := 'email fora do formato nome@dominio.ext'; end if;
  elsif tipo_out in ('telefone','celular') then
    d := regexp_replace(coalesce(p_valor,''), '\D', '', 'g');
    if length(d) = 13 and d like '55%' then d := substr(d,3); end if;
    if length(d) = 12 and d like '0%'  then d := substr(d,2); end if;
    a := nullif(substr(d,1,2),'')::int;
    if length(d) = 11 and substr(d,3,1) = '9' and a between 11 and 99 then
      tipo_out := 'celular'; norm := d;
    elsif length(d) = 10 and a between 11 and 99 then
      tipo_out := 'telefone'; norm := d;
    else
      ok := false; norm := d;
      motivo := 'telefone deve ter DDD + 8 dígitos (fixo) ou DDD + 9 dígitos começando em 9 (celular)';
    end if;
  elsif tipo_out = 'cpf' then
    d := regexp_replace(coalesce(p_valor,''), '\D', '', 'g'); norm := d;
    if length(d) <> 11 then ok := false; motivo := 'CPF deve ter 11 dígitos';
    elsif d ~ '^(\d)\1{10}$' then ok := false; motivo := 'CPF inválido (dígitos repetidos)';
    else
      for i in 1..9  loop s1 := s1 + substr(d,i,1)::int * (11-i); end loop;
      s1 := ((s1*10) % 11) % 10;
      for i in 1..10 loop s2 := s2 + substr(d,i,1)::int * (12-i); end loop;
      s2 := ((s2*10) % 11) % 10;
      if s1 <> substr(d,10,1)::int or s2 <> substr(d,11,1)::int then
        ok := false; motivo := 'CPF inválido (dígito verificador não confere)';
      end if;
    end if;
  else
    norm := trim(coalesce(p_valor,''));                -- rede social / observação / tipos livres
    if norm = '' then ok := false; motivo := 'valor vazio'; end if;
  end if;
end $$;

-- trigger: manual inválido é REJEITADO; carga inválida entra como 'suspeito' (não se perde dado)
create or replace function trg_servidor_contatos() returns trigger language plpgsql as $$
declare r record;
begin
  select * into r from norm_contato(new.tipo, new.valor);
  new.tipo := r.tipo_out;
  new.valor_norm := coalesce(r.norm, trim(new.valor));
  if not r.ok then
    if new.origem_input = 'manual' then
      raise exception 'Contato inválido: %', r.motivo;
    else
      new.status := 'suspeito'; new.motivo := r.motivo;
    end if;
  end if;
  new.visto_em := now();
  return new;
end $$;
drop trigger if exists t_svct on servidor_contatos;
create trigger t_svct before insert or update of valor, tipo on servidor_contatos
  for each row execute function trg_servidor_contatos();

alter table servidor_contatos enable row level security;
create policy svct_all on servidor_contatos for all to authenticated using (true) with check (true);

-- ========================= 5. CARGA INICIAL DO RAZÃO =========================
-- emails do Painel 11 (pessoas_obras) — chave = CPF da pessoa
insert into servidor_contatos (cpf, tipo, valor, fonte, grau_confianca, origem_input)
select distinct p.cpf, 'email', p.email, 'pessoas_obras', 'B', 'carga'
from pessoas_obras p
where p.email is not null and p.cpf is not null and length(regexp_replace(p.cpf,'\D','','g')) = 11
on conflict do nothing;
-- emails do Painel 6 (responsáveis)
insert into servidor_contatos (cpf, tipo, valor, fonte, grau_confianca, origem_input)
select distinct r.cpf, 'email', r.email, 'painel6', 'B', 'carga'
from painel6_responsaveis r
where r.email is not null and r.cpf is not null and length(regexp_replace(r.cpf,'\D','','g')) = 11
on conflict do nothing;
-- contatos manuais/curados já existentes no CRM (email/telefone da carga + anotações)
insert into servidor_contatos (cpf, entidade_id, tipo, valor, fonte, origem_input)
select distinct s.cpf, s.entidade_id, 'email', s.email, 'crm_carga', 'carga'
from crm_servidores s where s.email is not null on conflict do nothing;
insert into servidor_contatos (cpf, entidade_id, tipo, valor, fonte, origem_input)
select distinct s.cpf, s.entidade_id, 'telefone', s.telefone, 'crm_carga', 'carga'
from crm_servidores s where s.telefone is not null on conflict do nothing;
insert into servidor_contatos (cpf, entidade_id, tipo, valor, rede, complemento, fonte, origem_input, criado_por, criado_em)
select s.cpf, s.entidade_id, c.tipo, c.valor, c.rede, c.complemento, 'crm', 'carga', c.criado_por, c.criado_em
from crm_contatos c join crm_servidores s on s.id = c.servidor_id
where c.servidor_id is not null on conflict do nothing;

-- melhor contato por pessoa+tipo: verificado > ativo, grau, mais recente
create or replace view v_servidor_melhor_contato with (security_invoker = on) as
select distinct on (cpf, tipo) cpf, tipo, valor, valor_norm, fonte, status, grau_confianca, visto_em
from servidor_contatos
where cpf is not null and status in ('ativo','verificado')
order by cpf, tipo, (status = 'verificado') desc, grau_confianca asc, visto_em desc;

-- ========================= 6. RPCs DE BUSCA UNIFICADA =========================
create or replace function crm_buscar_servidores(
  p_nome text default null, p_cargo text default null, p_setor text default null,
  p_resp text default null, p_uf text default null, p_cidade text default null,
  p_esfera text default null, p_tema text default null, p_tem_contato boolean default null,
  p_entidade uuid default null, p_limit int default 200, p_offset int default 0)
returns table(painel1_id bigint, nome text, cargo text, setor text, responsabilidade text, cpf text,
  entidade_id uuid, entidade text, municipio text, uf text, esfera text, tema text,
  email text, telefone text)
language sql stable as $$
  select p.id, p.nome, p.cargo_funcao, p.setor, p.responsabilidade, p.cpf,
         e.id, e.nome, e.municipio, e.uf, e.esfera, e.tema, em.valor, tel.valor
  from painel1_servidores p
  join crm_entidades e on e.id = p.entidade_id
  left join lateral (select v.valor from v_servidor_melhor_contato v
                     where v.cpf = p.cpf and v.tipo = 'email' limit 1) em on true
  left join lateral (select v.valor from v_servidor_melhor_contato v
                     where v.cpf = p.cpf and v.tipo in ('celular','telefone')
                     order by (v.tipo = 'celular') desc limit 1) tel on true
  where p.dup_of is null
    and (p_entidade is null or p.entidade_id = p_entidade)
    and (p_nome  is null or p.nome ilike '%'||p_nome||'%')
    and (p_cargo is null or p.cargo_funcao ilike '%'||p_cargo||'%')
    and (p_setor is null or p.setor ilike '%'||p_setor||'%')
    and (p_resp  is null or p.responsabilidade ilike '%'||p_resp||'%')
    and (p_uf     is null or e.uf = p_uf)
    and (p_cidade is null or e.municipio = p_cidade)
    and (p_esfera is null or e.esfera = p_esfera)
    and (p_tema   is null or e.tema = p_tema)
    and (p_tem_contato is not true or em.valor is not null or tel.valor is not null)
  order by p.nome
  limit least(coalesce(p_limit,200),1000) offset coalesce(p_offset,0);
$$;

create or replace function crm_contar_servidores(
  p_nome text default null, p_cargo text default null, p_setor text default null,
  p_resp text default null, p_uf text default null, p_cidade text default null,
  p_esfera text default null, p_tema text default null, p_tem_contato boolean default null)
returns table(n_servidores bigint, n_entidades bigint)
language sql stable as $$
  select count(*), count(distinct p.entidade_id)
  from painel1_servidores p
  join crm_entidades e on e.id = p.entidade_id
  where p.dup_of is null
    and (p_nome  is null or p.nome ilike '%'||p_nome||'%')
    and (p_cargo is null or p.cargo_funcao ilike '%'||p_cargo||'%')
    and (p_setor is null or p.setor ilike '%'||p_setor||'%')
    and (p_resp  is null or p.responsabilidade ilike '%'||p_resp||'%')
    and (p_uf     is null or e.uf = p_uf)
    and (p_cidade is null or e.municipio = p_cidade)
    and (p_esfera is null or e.esfera = p_esfera)
    and (p_tema   is null or e.tema = p_tema)
    and (p_tem_contato is not true or exists
         (select 1 from servidor_contatos c where c.cpf = p.cpf and c.status in ('ativo','verificado')
            and c.tipo in ('email','telefone','celular')));
$$;

-- ========================= 7. RELATÓRIO PÓS-MIGRAÇÃO =========================
select
  (select count(*) from painel1_servidores where entidade_id is not null)  as p1_vinculados,
  (select count(*) from painel1_servidores where entidade_id is null)      as p1_sem_vinculo,
  (select count(*) from painel1_servidores where dup_of is not null)       as p1_duplicatas,
  (select count(*) from servidor_contatos)                                 as fatos_de_contato;
