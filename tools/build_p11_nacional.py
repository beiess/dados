#!/usr/bin/env python3
"""Painel 11 nacional — acrescenta a pessoas_obras os ENGENHEIROS estaduais/federais do painel1 (ibge nulo) cujo
órgão casa por nome com um órgão que contrata obra (obras_engenharia_orgaos), mesma UF (ou uf='BR' = lotação
desconhecida → 1 órgão por pessoa: o de mais obras). Não apaga nada (MG segue como está); dedup por
(nome normalizado, órgão, cod_ibge). Também cria/backfilla pessoas_obras.uf a partir do IBGE. Credencial: env P1_DB_URL."""
import os, time, psycopg2
def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)
conn=psycopg2.connect(os.environ['P1_DB_URL'],connect_timeout=20); conn.autocommit=False; cur=conn.cursor(); cur.execute('set statement_timeout=0')
UF="""case left(cod_ibge,2) when '11' then 'RO' when '12' then 'AC' when '13' then 'AM' when '14' then 'RR' when '15' then 'PA' when '16' then 'AP' when '17' then 'TO'
 when '21' then 'MA' when '22' then 'PI' when '23' then 'CE' when '24' then 'RN' when '25' then 'PB' when '26' then 'PE' when '27' then 'AL' when '28' then 'SE' when '29' then 'BA'
 when '31' then 'MG' when '32' then 'ES' when '33' then 'RJ' when '35' then 'SP' when '41' then 'PR' when '42' then 'SC' when '43' then 'RS' when '50' then 'MS' when '51' then 'MT' when '52' then 'GO' when '53' then 'DF' end"""
cur.execute("alter table pessoas_obras add column if not exists uf text"); cur.execute(f"update pessoas_obras set uf={UF} where uf is null and cod_ibge is not null"); log(f'uf backfill: {cur.rowcount}')
cur.execute("create index if not exists ix_p11_uf on pessoas_obras (uf)")
cur.execute("""create temp table cand as
with m as (
  select p.id pid, p.nome, p.cpf, p.setor, p.cargo_funcao, p.email, p.uf puf, o.cnpj, o.razao_social, o.municipio, o.cod_ibge, o.uf ouf, o.n_obras,
         row_number() over (partition by p.id, f_unaccent(upper(o.razao_social)) order by (o.uf='DF') desc, o.n_obras desc) rn
  from painel1_servidores p
  join obras_engenharia_orgaos o on f_unaccent(upper(o.razao_social)) = f_unaccent(upper(p.orgao)) and (o.uf=p.uf or p.uf='BR')
  where p.cargo_funcao ilike '%engenheir%' and p.ibge is null)
select * from m where rn=1""")
cur.execute("select count(*), count(distinct pid) from cand"); log(f'candidatos (1 órgão por pessoa×razão): {cur.fetchone()}')
cur.execute(f"""insert into pessoas_obras (nome,cpf,setor,email,orgao,municipio,cod_ibge,origem,fonte_tipo,data_coleta,grau_confianca,uf)
select nome, max(cpf) filter (where cpf ~ '^\\d{{11}}$'), left(string_agg(distinct coalesce(nullif(setor,''),cargo_funcao),'; '),300),
       left(string_agg(distinct email,', ') filter (where email like '%@%'),400), razao_social, municipio, cod_ibge, 'Engenheiro','PNCP+Painel1',current_date::text,'B', ouf
from cand c
where not exists (select 1 from pessoas_obras x where f_unaccent(upper(x.nome))=f_unaccent(upper(c.nome)) and x.orgao=c.razao_social and coalesce(x.cod_ibge,'')=coalesce(c.cod_ibge,''))
group by nome, razao_social, municipio, cod_ibge, ouf""")
log(f'inseridos em pessoas_obras: {cur.rowcount}'); conn.commit()
cur.execute("select count(*), count(distinct uf), count(*) filter (where origem='Engenheiro'), count(email) from pessoas_obras"); log(f'pessoas_obras agora (tot, ufs, engenheiros, c/ email): {cur.fetchone()}')
cur.execute("select uf, count(*) from pessoas_obras group by 1 order by 2 desc limit 8"); log(f'por UF: {cur.fetchall()}')
cur.execute("analyze pessoas_obras"); conn.commit(); cur.execute("select pg_notify('pgrst','reload schema')"); conn.commit(); conn.close()
