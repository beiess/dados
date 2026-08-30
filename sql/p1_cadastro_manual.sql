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
-- duplicidade: CPF exato · nome normalizado exato · nome parecido (mesmo 1º nome + último sobrenome, similaridade ≥ 0,6)
-- precisa de: ix_p1_nome_norm (btree f_unaccent(upper(nome))) e ix_p1_nome_norm_tpo (idem, text_pattern_ops — prefixo do LIKE)
create index concurrently if not exists ix_p1_nome_norm_tpo on painel1_servidores (f_unaccent(upper(nome)) text_pattern_ops);
create or replace function p1_duplicidade(p_nome text, p_uf text default null, p_ibge text default null, p_cpf text default null)
returns table (id bigint, nome text, cpf text, orgao text, cargo_funcao text, esfera text, uf text, ibge text, origem text, criterio text, similaridade real)
language plpgsql stable set search_path=public as $$
declare v_cpf text := nullif(regexp_replace(coalesce(p_cpf,''),'\D','','g'),''); v_nome text := f_unaccent(upper(trim(coalesce(p_nome,'')))); toks text[]; pat text;
begin
  if length(v_cpf) = 11 then
    return query select s.id, s.nome, s.cpf, s.orgao, s.cargo_funcao, s.esfera, s.uf, s.ibge, s.origem, 'cpf'::text, 1.0::real from painel1_servidores s where s.cpf = v_cpf limit 10;
  end if;
  if length(v_nome) >= 8 then
    return query select s.id, s.nome, s.cpf, s.orgao, s.cargo_funcao, s.esfera, s.uf, s.ibge, s.origem, 'nome exato'::text, 1.0::real
      from painel1_servidores s where f_unaccent(upper(s.nome)) = v_nome and (p_uf is null or s.uf = p_uf or s.uf = 'BR') limit 10;
    toks := regexp_split_to_array(v_nome, '\s+');
    if array_length(toks,1) >= 2 then
      pat := toks[1] || ' %' || toks[array_length(toks,1)];
      return query select s.id, s.nome, s.cpf, s.orgao, s.cargo_funcao, s.esfera, s.uf, s.ibge, s.origem, 'nome parecido'::text, similarity(f_unaccent(upper(s.nome)), v_nome)::real
        from painel1_servidores s where f_unaccent(upper(s.nome)) like pat and f_unaccent(upper(s.nome)) <> v_nome
          and (p_uf is null or s.uf = p_uf or s.uf = 'BR') and similarity(f_unaccent(upper(s.nome)), v_nome) >= 0.6 order by 11 desc limit 8;
    end if;
  end if;
end $$;
revoke all on function p1_duplicidade(text,text,text,text) from public; grant execute on function p1_duplicidade(text,text,text,text) to authenticated;
