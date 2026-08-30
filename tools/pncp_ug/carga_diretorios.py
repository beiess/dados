#!/usr/bin/env python3
"""Carrega a curadoria de diretórios oficiais (agentes web-reach) no banco:
  diretorio_orgaos (1 linha por órgão/entidade; upsert por (uf, nome)), diretorio_orgaos_cnpj (cnpj → diretório),
  apis_orgaos (1 linha por API/portal; upsert por (uf, orgao, url)), apis_orgaos_cnpj (cnpj → api, via cnpjs_pncp do
  órgão de mesmo nome/sigla). Lê todos os <UF>/orgaos.jsonl e <UF>/apis.jsonl em ~/.claude/jobs/diretorios-uf/.
Re-executável. Credencial: env P1_DB_URL."""
import os, json, glob, time, re, unicodedata, psycopg2
from psycopg2.extras import execute_values, Json
def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)
def unac(s): return ''.join(c for c in unicodedata.normalize('NFD', str(s or '')) if unicodedata.category(c) != 'Mn').upper().strip()
JOB=os.path.dirname(os.path.abspath(__file__))
conn=psycopg2.connect(os.environ['P1_DB_URL'],connect_timeout=30); conn.autocommit=True; cur=conn.cursor(); cur.execute('set statement_timeout=0')
cur.execute("""
create table if not exists diretorio_orgaos (id bigserial primary key, uf text, esfera text, nome text, nome_norm text, sigla text, tipo text, poder text, site text,
  emails text[], telefones text[], endereco text, ouvidoria_url text, fale_conosco_url text, redes_sociais text, orgao_pai text, fonte_url text, fontes text[],
  cnpjs_pncp text[], n_unidades_pncp int, publicou_pncp boolean, siorg_codigo text, coletado_em date, extras jsonb, unique (uf, nome));
create index if not exists ix_dir_nome_norm on diretorio_orgaos (uf, nome_norm);
create table if not exists diretorio_orgaos_cnpj (cnpj text, diretorio_id bigint references diretorio_orgaos(id) on delete cascade, primary key (cnpj, diretorio_id));
create index if not exists ix_dirc_cnpj on diretorio_orgaos_cnpj (cnpj);
create table if not exists apis_orgaos (id bigserial primary key, uf text, esfera text, orgao text, nome text, url text, docs_url text, tipo text, auth text, formato text,
  dominio text, status text, obs text, fonte_url text, testado_em date, cnpjs text[], unique (uf, orgao, url));
create table if not exists apis_orgaos_cnpj (cnpj text, api_id bigint references apis_orgaos(id) on delete cascade, primary key (cnpj, api_id));
create index if not exists ix_apic_cnpj on apis_orgaos_cnpj (cnpj);
""")
for t in ('diretorio_orgaos','diretorio_orgaos_cnpj','apis_orgaos','apis_orgaos_cnpj'):
    cur.execute(f"alter table {t} enable row level security; drop policy if exists {t}_read on {t}; create policy {t}_read on {t} for select to authenticated using (true); revoke all on {t} from anon; grant select on {t} to authenticated, service_role")
def jl(p):
    out=[]
    for ln in open(p,encoding='utf-8'):
        try: out.append(json.loads(ln))
        except Exception: pass
    return out
def arr(v):
    if v is None: return []
    if isinstance(v,list): return [str(x).strip() for x in v if str(x).strip()]
    return [x.strip() for x in re.split(r'[|;,]',str(v)) if x.strip()]
tot_o=tot_a=0
for f in sorted(glob.glob(os.path.join(JOB,'*','orgaos.jsonl'))):
    uf=os.path.basename(os.path.dirname(f)); rs=jl(f); rows=[]; seen=set()
    for r in rs:
        nome=(r.get('nome') or '').strip()
        if not nome or (uf,nome) in seen: continue
        seen.add((uf,nome))
        extras={k:v for k,v in r.items() if k not in ('uf','esfera','nome','sigla','tipo','poder','site','emails','telefones','endereco','ouvidoria_url','fale_conosco_url','redes_sociais','orgao_pai','fonte_url','fontes','cnpjs_pncp','n_unidades_pncp','publicou_pncp','siorg_codigo','coletado_em')}
        cn=[re.sub(r'\D','',c) for c in arr(r.get('cnpjs_pncp'))]; cn=[c for c in cn if len(c)==14]
        rows.append((r.get('uf') or uf, r.get('esfera'), nome, unac(nome), r.get('sigla') or None, r.get('tipo'), r.get('poder'), r.get('site') or None, arr(r.get('emails')), arr(r.get('telefones')),
                     r.get('endereco') or None, r.get('ouvidoria_url') or None, r.get('fale_conosco_url') or None, r.get('redes_sociais') or None, r.get('orgao_pai') or None, r.get('fonte_url') or None,
                     arr(r.get('fontes')), cn, r.get('n_unidades_pncp'), r.get('publicou_pncp'), (str(r['siorg_codigo']) if r.get('siorg_codigo') else None), r.get('coletado_em') or None, Json(extras)))
    execute_values(cur,"""insert into diretorio_orgaos (uf,esfera,nome,nome_norm,sigla,tipo,poder,site,emails,telefones,endereco,ouvidoria_url,fale_conosco_url,redes_sociais,orgao_pai,fonte_url,fontes,cnpjs_pncp,n_unidades_pncp,publicou_pncp,siorg_codigo,coletado_em,extras) values %s
      on conflict (uf,nome) do update set esfera=excluded.esfera, nome_norm=excluded.nome_norm, sigla=excluded.sigla, tipo=excluded.tipo, poder=excluded.poder, site=excluded.site, emails=excluded.emails, telefones=excluded.telefones,
      endereco=excluded.endereco, ouvidoria_url=excluded.ouvidoria_url, fale_conosco_url=excluded.fale_conosco_url, redes_sociais=excluded.redes_sociais, orgao_pai=excluded.orgao_pai, fonte_url=excluded.fonte_url, fontes=excluded.fontes,
      cnpjs_pncp=excluded.cnpjs_pncp, n_unidades_pncp=excluded.n_unidades_pncp, publicou_pncp=excluded.publicou_pncp, siorg_codigo=excluded.siorg_codigo, coletado_em=excluded.coletado_em, extras=excluded.extras""",rows,page_size=500)
    tot_o+=len(rows); log(f'{uf}: diretorio_orgaos upsert {len(rows)}')
cur.execute("delete from diretorio_orgaos_cnpj; insert into diretorio_orgaos_cnpj (cnpj, diretorio_id) select distinct c, d.id from diretorio_orgaos d, unnest(d.cnpjs_pncp) c")
cur.execute("select count(*), count(distinct cnpj) from diretorio_orgaos_cnpj"); log(f'diretorio_orgaos_cnpj: {cur.fetchone()}')
for f in sorted(glob.glob(os.path.join(JOB,'*','apis.jsonl'))):
    uf=os.path.basename(os.path.dirname(f)); rs=jl(f); rows=[]; seen=set()
    for r in rs:
        key=(r.get('uf') or uf, (r.get('orgao') or '').strip(), (r.get('url') or '').strip())
        if not key[2] or key in seen: continue
        seen.add(key)
        rows.append((key[0], r.get('esfera'), key[1], r.get('nome'), key[2], r.get('docs_url') or None, r.get('tipo'), r.get('auth'), r.get('formato'), r.get('dominio'), r.get('status'), r.get('obs') or None, r.get('fonte_url') or None, r.get('testado_em') or None))
    execute_values(cur,"""insert into apis_orgaos (uf,esfera,orgao,nome,url,docs_url,tipo,auth,formato,dominio,status,obs,fonte_url,testado_em) values %s
      on conflict (uf,orgao,url) do update set esfera=excluded.esfera, nome=excluded.nome, docs_url=excluded.docs_url, tipo=excluded.tipo, auth=excluded.auth, formato=excluded.formato, dominio=excluded.dominio, status=excluded.status, obs=excluded.obs, fonte_url=excluded.fonte_url, testado_em=excluded.testado_em""",rows,page_size=500)
    tot_a+=len(rows); log(f'{uf}: apis_orgaos upsert {len(rows)}')
# cnpjs das APIs: pelo órgão de mesmo nome/sigla no diretório (mesma UF)
cur.execute("""update apis_orgaos a set cnpjs = d.cnpjs_pncp from diretorio_orgaos d
  where d.uf=a.uf and cardinality(d.cnpjs_pncp)>0 and (d.nome_norm = f_unaccent(upper(a.orgao)) or (d.sigla is not null and length(d.sigla)>=3 and upper(d.sigla)=upper(a.orgao)))""")
log(f'apis c/ cnpj por nome/sigla: {cur.rowcount}')
cur.execute("delete from apis_orgaos_cnpj; insert into apis_orgaos_cnpj (cnpj, api_id) select distinct c, a.id from apis_orgaos a, unnest(a.cnpjs) c where a.cnpjs is not null")
cur.execute("select count(*) from apis_orgaos_cnpj"); log(f'apis_orgaos_cnpj: {cur.fetchone()[0]}')
for t in ('diretorio_orgaos','diretorio_orgaos_cnpj','apis_orgaos','apis_orgaos_cnpj'): cur.execute(f'analyze {t}')
cur.execute("select pg_notify('pgrst','reload schema')")
cur.execute("select uf, count(*), count(*) filter (where cardinality(emails)>0), count(*) filter (where cardinality(telefones)>0), count(*) filter (where cardinality(cnpjs_pncp)>0) from diretorio_orgaos group by 1"); log(f'diretorio por UF (tot, c/email, c/tel, c/cnpj): {cur.fetchall()}')
cur.execute("select uf, count(*), count(*) filter (where status like '200%') from apis_orgaos group by 1"); log(f'apis por UF (tot, 200): {cur.fetchall()}')
