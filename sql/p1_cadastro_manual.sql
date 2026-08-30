-- v11.17 (30/08/2026) — Painel 1: cadastro manual com dedup + regra "equipe não edita dado existente"
-- (aplicado no projeto ntkntgcegvqqlarjspjp em 30/08; aqui para referência/reaplicação)
create or replace function p1_is_admin() returns boolean language sql stable security definer set search_path=public as $$
  select exists (select 1 from funcionarios f where f.auth_user_id = auth.uid() and (f.funcao = 'admin' or coalesce(f.acesso_irrestrito,false)))
$$;
revoke all on function p1_is_admin() from public; grant execute on function p1_is_admin() to authenticated;
drop policy if exists p1_auth_update on painel1_servidores;
create policy p1_auth_update on painel1_servidores for update to authenticated
  using (p1_is_admin() or origem = 'manual:' || auth.email()) with check (p1_is_admin() or origem = 'manual:' || auth.email());
drop policy if exists p1_auth_insert on painel1_servidores;
create policy p1_auth_insert on painel1_servidores for insert to authenticated with check (origem = 'manual:' || auth.email());
-- duplicidade EXATA (rápida, índices ix_p1_cpf e ix_p1_nome_norm): CPF exato · nome normalizado exato
create or replace function p1_duplicidade(p_nome text, p_uf text default null, p_ibge text default null, p_cpf text default null)
returns table (id bigint, nome text, cpf text, orgao text, cargo_funcao text, esfera text, uf text, ibge text, origem text, criterio text, similaridade real)
language plpgsql stable set search_path=public as $$
declare v_cpf text := nullif(regexp_replace(coalesce(p_cpf,''),'\D','','g'),''); v_nome text := f_unaccent(upper(trim(coalesce(p_nome,''))));
begin
  if length(v_cpf) = 11 then
    return query select s.id, s.nome, s.cpf, s.orgao, s.cargo_funcao, s.esfera, s.uf, s.ibge, s.origem, 'cpf'::text, 1.0::real from painel1_servidores s where s.cpf = v_cpf limit 10;
  end if;
  if length(v_nome) >= 8 then
    return query select s.id, s.nome, s.cpf, s.orgao, s.cargo_funcao, s.esfera, s.uf, s.ibge, s.origem, 'nome exato'::text, 1.0::real
      from painel1_servidores s where f_unaccent(upper(s.nome)) = v_nome and (p_uf is null or s.uf = p_uf or s.uf = 'BR') limit 10;
  end if;
end $$;
-- duplicidade APROXIMADA (trigram GIN ix_p1_nome_trgm, limiar 0,6): pode levar 10–40 s em nomes muito comuns — o app chama
-- em segundo plano com timeout de 20 s. (Índice text_pattern_ops no nome não pôde ser criado: o pooler derruba builds longos.)
create or replace function p1_duplicidade_fuzzy(p_nome text, p_uf text default null)
returns table (id bigint, nome text, cpf text, orgao text, cargo_funcao text, esfera text, uf text, ibge text, origem text, criterio text, similaridade real)
language plpgsql volatile set search_path=public set work_mem='128MB' as $$
begin
  perform set_limit(0.6);
  return query select s.id, s.nome, s.cpf, s.orgao, s.cargo_funcao, s.esfera, s.uf, s.ibge, s.origem, 'nome parecido'::text, similarity(s.nome, p_nome)::real
    from painel1_servidores s where s.nome % p_nome and f_unaccent(upper(s.nome)) <> f_unaccent(upper(trim(p_nome))) and (p_uf is null or s.uf = p_uf or s.uf = 'BR')
    order by 11 desc limit 8;
end $$;
revoke all on function p1_duplicidade(text,text,text,text) from public; grant execute on function p1_duplicidade(text,text,text,text) to authenticated;
revoke all on function p1_duplicidade_fuzzy(text,text) from public; grant execute on function p1_duplicidade_fuzzy(text,text) to authenticated;
