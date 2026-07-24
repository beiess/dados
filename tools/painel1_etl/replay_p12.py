#!/usr/bin/env python3
"""Replay Painel 12 → Painel 1 (drift pós-13/07 + fontes nunca promovidas, ex. SIAPE).
Por FONTE, com commit por fonte (retomável): dedup interno distinct-on
(fonte, coalesce(matricula,nome), orgao) — a MESMA chave da promoção original —
+ anti-join contra o painel1 (origem='p12<uf>:<fonte>'). Nunca apaga nem sobrescreve."""
import time, psycopg2

import os
DB = os.environ["SUPABASE_DB_URL"]  # exporte de TCEMG/dados-painel/.supabase_env

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

SQL = """
insert into painel1_servidores
  (nome, cpf, matricula, orgao, setor, cargo_funcao, remuneracao,
   email, telefone, origem, consta_site, esfera, uf)
select s.nome,
       case when s.cpf ~ '^[0-9]{11}$' then s.cpf end,
       s.matricula,
       coalesce(s.orgao, s.entidade), s.setor,
       coalesce(s.cargo, s.funcao),
       s.remuneracao::text,
       coalesce(nullif(s.email,''), nullif(s.email_institucional,'')),
       coalesce(nullif(s.telefone,''), nullif(s.telefone_institucional,'')),
       'p12'||lower(coalesce(s.uf,'br'))||':'||s.fonte, 'nao',
       case
         when s.esfera in ('municipal','estadual','federal','justica') then s.esfera
         when s.fonte like 'SIAPE%%' or s.fonte like 'MILITARES%%' or s.fonte like 'DEFESA%%'
           or s.fonte in ('SENADO','CAMARA_FEDERAL') then 'federal'
         when s.fonte = 'DADOSJUSBR' then 'justica'
         else 'estadual'
       end,
       coalesce(s.uf,'BR')
  from (select distinct on (coalesce(matricula,'')||'|'||nome, coalesce(orgao,entidade,''))
               * from servidores_brasil_2026 where fonte = %s and nome is not null) s
 where not exists (
   select 1 from painel1_servidores p
    where p.origem = 'p12'||lower(coalesce(s.uf,'br'))||':'||s.fonte
      and coalesce(p.matricula,'')||'|'||p.nome = coalesce(s.matricula,'')||'|'||s.nome
      and coalesce(p.orgao,'') = coalesce(s.orgao, s.entidade, ''))"""

conn, cur = conecta()
cur.execute("select fonte, count(*) from servidores_brasil_2026 group by 1 order by 2")
fontes = cur.fetchall()
print(f"{len(fontes)} fontes no Painel 12", flush=True)
FEITAS = set()
try:
    FEITAS = {l.strip() for l in open("/Users/israelsantiago/.claude/jobs/nasc-arquivos/replay_feitas.txt")}
except FileNotFoundError:
    pass
tot = 0
for fonte, n in fontes:
    if fonte in FEITAS:
        continue
    ok = False
    for tent in range(3):
        try:
            t0 = time.time(); cur.execute(SQL, (fonte,)); ins = cur.rowcount
            tot += ins
            print(f"[{time.strftime('%H:%M:%S')}] {fonte}: {ins} novos de {n} (em {time.time()-t0:.0f}s; acum {tot})", flush=True)
            ok = True; break
        except Exception as e:
            print(f"{fonte} falhou ({str(e)[:80]}) — reconectando", flush=True)
            try: conn.close()
            except Exception: pass
            conn, cur = conecta()
    if ok:
        open("/Users/israelsantiago/.claude/jobs/nasc-arquivos/replay_feitas.txt", "a").write(fonte + "\n")
cur.execute("select count(*), count(*) filter (where esfera='federal') from painel1_servidores")
t, f = cur.fetchone()
print(f"REPLAY P12 COMPLETO · {tot} novos · base: {t} · federais: {f}", flush=True)
conn.close()
