#!/usr/bin/env python3
"""Painel 2 ← PNCP: colunas pncp_* em cadastro_institucional (MG) e cadastro_institucional_br, atualizadas por CNPJ
a partir de pncp_orgaos (registro completo do PNCP). Re-executável (só UPDATE). Credencial: env P1_DB_URL."""
import os, time, psycopg2
def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)
conn=psycopg2.connect(os.environ['P1_DB_URL'],connect_timeout=20); conn.autocommit=False; cur=conn.cursor(); cur.execute('set statement_timeout=0')
for t in ('cadastro_institucional','cadastro_institucional_br'):
    cur.execute(f"""alter table {t} add column if not exists pncp_orgao_id bigint, add column if not exists pncp_validado boolean,
      add column if not exists pncp_natureza text, add column if not exists pncp_n_unidades int, add column if not exists pncp_cliente boolean,
      add column if not exists pncp_data_inclusao date, add column if not exists pncp_unidades text""")
    key="regexp_replace(t.cnpj,'\\D','','g')" if t=='cadastro_institucional' else 't.cnpj'
    cur.execute(f"""update {t} t set pncp_orgao_id=o.orgao_id, pncp_validado=o.validado, pncp_natureza=coalesce(o.natureza_juridica,o.cod_natureza_juridica),
      pncp_n_unidades=o.n_unidades, pncp_cliente=o.cliente_pncp, pncp_data_inclusao=o.data_inclusao::date,
      pncp_unidades=(select left(string_agg(u.codigo_unidade||' '||u.nome_unidade,' | ' order by u.codigo_unidade),1500) from pncp_unidades u where u.cnpj=o.cnpj)
      from pncp_orgaos o where o.cnpj={key} and t.cnpj is not null""")
    log(f'{t}: {cur.rowcount} linhas enriquecidas'); conn.commit()
cur.execute("select count(*), count(pncp_orgao_id), count(*) filter (where pncp_cliente) from cadastro_institucional"); log(f'cadastro MG (tot, c/pncp, clientes): {cur.fetchone()}')
cur.execute("select count(*), count(pncp_orgao_id), count(*) filter (where pncp_cliente) from cadastro_institucional_br"); log(f'cadastro BR (tot, c/pncp, clientes): {cur.fetchone()}')
cur.execute("select pg_notify('pgrst','reload schema')"); conn.commit(); conn.close()
