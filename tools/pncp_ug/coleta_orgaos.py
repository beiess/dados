#!/usr/bin/env python3
"""Cadastro COMPLETO de órgãos do PNCP — enumeração por ID sequencial.
GET https://pncp.gov.br/api/pncp/v1/orgaos/id/{id}  (público, sem chave; 404 = fim/buraco)
+ opcional GET /v1/orgaos/{cnpj}/unidades (setores + município/UF; 404 = órgão sem unidades).
Resumível por ledger (orgaos.jsonl: 1 linha por id tentado, inclusive 404). Uso:
  python3 coleta_orgaos.py --ate 98600 [--de 1] [--conc 32] [--unidades] [--limite N]
Saídas: orgaos.jsonl (id, status, dados), unidades.jsonl (cnpj, status, lista)."""
import argparse, json, os, sys, time, threading, urllib.request, urllib.error, concurrent.futures as cf
JOB=os.path.dirname(os.path.abspath(__file__)); UA={'User-Agent':'Mozilla/5.0 (coleta-pncp-orgaos)'}
ap=argparse.ArgumentParser(); ap.add_argument('--de',type=int,default=1); ap.add_argument('--ate',type=int,required=True)
ap.add_argument('--conc',type=int,default=32); ap.add_argument('--unidades',action='store_true'); ap.add_argument('--limite',type=int,default=0)
a=ap.parse_args()
def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)
def get(url,tries=4):
    for t in range(tries):
        try:
            r=urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=90); return 200,json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (404,204): return e.code,None
            if e.code==429 or e.code>=500: time.sleep(5*(t+1)); continue
            return e.code,None
        except Exception: time.sleep(3*(t+1))
    return -1,None
ORG=os.path.join(JOB,'orgaos.jsonl'); UNI=os.path.join(JOB,'unidades.jsonl'); lock=threading.Lock()
feitos=set()
if os.path.exists(ORG):
    for ln in open(ORG,encoding='utf-8'):
        try: feitos.add(json.loads(ln)['id'])
        except Exception: pass
todo=[i for i in range(a.de,a.ate+1) if i not in feitos]
if a.limite: todo=todo[:a.limite]
log(f'ids a coletar: {len(todo)} (já feitos {len(feitos)}) · conc {a.conc} · unidades={a.unidades}')
uni_feitas=set()
if a.unidades and os.path.exists(UNI):
    for ln in open(UNI,encoding='utf-8'):
        try: uni_feitas.add(json.loads(ln)['cnpj'])
        except Exception: pass
n=0; t0=time.time(); stats={200:0,404:0,-1:0}
def work(i):
    global n
    c,d=get(f'https://pncp.gov.br/api/pncp/v1/orgaos/id/{i}')
    rec={'id':i,'status':c,'dados':d}
    ulin=None
    if a.unidades and c==200 and d and d.get('cnpj') and d['cnpj'] not in uni_feitas:
        cu,du=get(f'https://pncp.gov.br/api/pncp/v1/orgaos/{d["cnpj"]}/unidades')
        ulin={'cnpj':d['cnpj'],'orgao_id':i,'status':cu,'unidades':du}
    with lock:
        if c!=-1:  # -1 (rede) não entra no ledger → tenta de novo na próxima execução
            open(ORG,'a',encoding='utf-8').write(json.dumps(rec,ensure_ascii=False)+'\n')
        if ulin: open(UNI,'a',encoding='utf-8').write(json.dumps(ulin,ensure_ascii=False)+'\n'); uni_feitas.add(ulin['cnpj'])
        stats[c if c in stats else -1]=stats.get(c if c in stats else -1,0)+1; n+=1
        if n%200==0: log(f'{n}/{len(todo)} · {n/(time.time()-t0):.1f} req/s · {stats}')
with cf.ThreadPoolExecutor(a.conc) as ex: list(ex.map(work,todo))
log(f'FIM: {n} ids em {time.time()-t0:.0f}s · {stats}')
