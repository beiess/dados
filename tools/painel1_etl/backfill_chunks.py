#!/usr/bin/env python3
"""Backfill esfera+uf em BLOCOS de id com commit por bloco (à prova de queda)."""
import time, psycopg2

import os
DB = os.environ["SUPABASE_DB_URL"]  # exporte de TCEMG/dados-painel/.supabase_env
IBGE_UF = {"11":"RO","12":"AC","13":"AM","14":"RR","15":"PA","16":"AP","17":"TO","21":"MA","22":"PI",
           "23":"CE","24":"RN","25":"PB","26":"PE","27":"AL","28":"SE","29":"BA","31":"MG","32":"ES",
           "33":"RJ","35":"SP","41":"PR","42":"SC","43":"RS","50":"MS","51":"MT","52":"GO","53":"DF"}
CASE_UF = "case left(ibge,2) " + " ".join(f"when '{k}' then '{v}'" for k, v in IBGE_UF.items()) + " end"
SQL = f"""
  update painel1_servidores set
    uf = coalesce(
      case when origem like 'p12%%' then upper(substring(origem from 4 for 2)) end,
      case when ibge is not null then {CASE_UF} end,
      'MG'),
    esfera = case
      when ibge is not null then 'municipal'
      when origem like 'p12%%' then (
        case
          when split_part(origem,':',2) like 'SIAPE%%'
            or split_part(origem,':',2) like 'MILITARES%%'
            or split_part(origem,':',2) like 'DEFESA%%'
            or split_part(origem,':',2) in ('SENADO','CAMARA_FEDERAL') then 'federal'
          when split_part(origem,':',2) = 'DADOSJUSBR' then 'justica'
          when split_part(origem,':',2) in ('CAMARA','SAPL_MUNICIPAL') then 'municipal'
          else 'estadual'
        end)
      else 'municipal'
    end
  where esfera is null and id between %s and %s"""

def conecta():
    for t in range(20):
        try:
            c = psycopg2.connect(DB, connect_timeout=15, keepalives=1, keepalives_idle=30)
            c.autocommit = True
            k = c.cursor(); k.execute("set statement_timeout=0")
            return c, k
        except Exception as e:
            print(f"conexão falhou ({str(e)[:60]}) — retry {t+1}/20 em 45s", flush=True)
            time.sleep(45)
    raise SystemExit("sem conexão")

conn, cur = conecta()
cur.execute("select min(id), max(id) from painel1_servidores")
lo, hi = cur.fetchone()
PASSO = 300_000
print(f"ids {lo}..{hi} · blocos de {PASSO}", flush=True)
tot = 0
a = lo
while a <= hi:
    b = a + PASSO - 1
    for tent in range(3):
        try:
            t0 = time.time(); cur.execute(SQL, (a, b)); n = cur.rowcount
            tot += n
            print(f"[{time.strftime('%H:%M:%S')}] bloco {a}-{b}: {n} em {time.time()-t0:.0f}s (acum {tot})", flush=True)
            break
        except Exception as e:
            print(f"bloco {a}-{b} falhou ({str(e)[:70]}) — reconectando", flush=True)
            try: conn.close()
            except Exception: pass
            conn, cur = conecta()
    a = b + 1
cur.execute("select esfera, count(*) from painel1_servidores group by 1 order by 2 desc")
print("distribuição final:", cur.fetchall(), flush=True)
conn.close(); print("BACKFILL COMPLETO", flush=True)
