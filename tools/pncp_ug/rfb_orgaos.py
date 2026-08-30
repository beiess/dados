#!/usr/bin/env python3
"""RFB (minhareceita.org, espelho público) p/ órgãos do PNCP sem sede/contato → tabela pncp_orgaos_rfb (cnpj PK).
Resumível (só CNPJs ainda não consultados); --limite N; --conc 6. Depois: carga_pncp/contatos_ug usam a tabela.
Credencial do banco: env P1_DB_URL."""
import argparse, json, os, time, threading, urllib.request, urllib.error, concurrent.futures as cf, psycopg2, io
ap=argparse.ArgumentParser(); ap.add_argument('--limite',type=int,default=0); ap.add_argument('--conc',type=int,default=6); a=ap.parse_args()
def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)
conn=psycopg2.connect(os.environ['P1_DB_URL'],connect_timeout=20); conn.autocommit=True; cur=conn.cursor(); cur.execute('set statement_timeout=0')
cur.execute("""create table if not exists pncp_orgaos_rfb (cnpj text primary key, status int, razao_social text, nome_fantasia text, situacao text,
  natureza_juridica text, uf text, cod_ibge text, municipio text, logradouro text, numero text, bairro text, cep text, telefone text, email text,
  ente_federativo text, consultado_em timestamp default now()); alter table pncp_orgaos_rfb enable row level security;
  drop policy if exists pncp_orgaos_rfb_read on pncp_orgaos_rfb; create policy pncp_orgaos_rfb_read on pncp_orgaos_rfb for select to authenticated using (true);
  revoke all on pncp_orgaos_rfb from anon; grant select on pncp_orgaos_rfb to authenticated, service_role""")
cur.execute("""select o.cnpj from pncp_orgaos o left join pncp_orgaos_rfb r using(cnpj) where r.cnpj is null
  and (o.uf is null or not exists (select 1 from cadastro_institucional_br b where b.cnpj=o.cnpj and b.telefone is not null)
       and not exists (select 1 from cadastro_institucional m where regexp_replace(m.cnpj,'\D','','g')=o.cnpj and m.contato is not null)) order by o.orgao_id""")
todo=[r[0] for r in cur.fetchall()]
if a.limite: todo=todo[:a.limite]
log(f'CNPJs a consultar na RFB: {len(todo)} (conc {a.conc})')
lock=threading.Lock(); n=0; t0=time.time(); ok=0
def rfb(c):
    for t in range(4):
        try:
            r=urllib.request.urlopen(urllib.request.Request(f'https://minhareceita.org/{c}',headers={'User-Agent':'Mozilla/5.0'}),timeout=60); return 200,json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code==404: return 404,None
            if e.code==429: time.sleep(10*(t+1)); continue
            time.sleep(3*(t+1))
        except Exception: time.sleep(3*(t+1))
    return -1,None
def ins(c,st,d):
    global n,ok
    d=d or {}; tel=' / '.join(x for x in [d.get('ddd_telefone_1'),d.get('ddd_telefone_2')] if x) or None
    with lock:
        cur.execute("""insert into pncp_orgaos_rfb (cnpj,status,razao_social,nome_fantasia,situacao,natureza_juridica,uf,cod_ibge,municipio,logradouro,numero,bairro,cep,telefone,email,ente_federativo)
          values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) on conflict (cnpj) do nothing""",
          (c,st,d.get('razao_social'),d.get('nome_fantasia'),d.get('descricao_situacao_cadastral'),d.get('natureza_juridica'),d.get('uf'),(str(d['codigo_municipio_ibge']) if d.get('codigo_municipio_ibge') else None),d.get('municipio'),
           ((d.get('descricao_tipo_de_logradouro') or '')+' '+(d.get('logradouro') or '')).strip() or None,d.get('numero'),d.get('bairro'),d.get('cep'),tel,(d.get('email') or None),d.get('ente_federativo_responsavel')))
        n+=1; ok+=(st==200)
        if n%100==0: log(f'{n}/{len(todo)} · ok {ok} · {n/(time.time()-t0):.1f} req/s')
def work(c):
    st,d=rfb(c)
    if st!=-1: ins(c,st,d)
with cf.ThreadPoolExecutor(a.conc) as ex: list(ex.map(work,todo))
log(f'FIM: {n} consultados · {ok} com dados · {time.time()-t0:.0f}s')
