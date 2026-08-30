#!/usr/bin/env python3
"""UASGs e órgãos do SIASG (Compras.gov.br dados abertos, público, 500/página) → uasg.jsonl / orgaos_siasg.jsonl."""
import json, time, urllib.request, os
JOB=os.path.dirname(os.path.abspath(__file__)); UA={'User-Agent':'Mozilla/5.0'}
def get(url,tries=5):
    for t in range(tries):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=120).read())
        except Exception as e: time.sleep(5*(t+1))
    raise SystemExit(f'falhou: {url}')
def sweep(path,param,out):
    n=0
    with open(os.path.join(JOB,out),'w',encoding='utf-8') as f:
        for st in ('true','false'):
            pg=1
            while True:
                d=get(f'https://dadosabertos.compras.gov.br/modulo-uasg/{path}?pagina={pg}&{param}={st}')
                for r in d.get('resultado') or []: f.write(json.dumps(r,ensure_ascii=False)+'\n'); n+=1
                if pg>=(d.get('totalPaginas') or 0): break
                pg+=1
    print(f'{out}: {n} registros', flush=True)
sweep('1_consultarUasg','statusUasg','uasg.jsonl')
sweep('2_consultarOrgao','statusOrgao','orgaos_siasg.jsonl')
