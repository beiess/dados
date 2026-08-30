#!/usr/bin/env python3
"""Enriquece os servidores ESTADUAIS de SC no painel1 (origem p12sc:* e arquivo:tce_sc_servidores) com a
ENTIDADE VINCULADA: CNPJ (de pncp_orgaos SC estadual) + e-mail/telefone/site institucional (de diretorio_orgaos SC).
Modelo do projeto: email/telefone institucionais só-nulos (como federais SIAPE) + 'Entidade: <razão> · CNPJ <x>' e
'Institucional: <email>/<tel>/<site>' em contato_adicional (append, sem duplicar). Por GRUPO de órgão (poucos UPDATEs).
env P1_DB_URL."""
import os, re, time, unicodedata, psycopg2
def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)
def norm(s): return re.sub(r'\s+',' ',''.join(c for c in unicodedata.normalize('NFD',(s or '').upper()) if unicodedata.category(c)!='Mn')).strip()
def base(o):  # tira prefixo de código "2001-" / "801 - " e normaliza
    return norm(re.sub(r'^\s*\d+\s*-?\s*','',o or ''))
c=psycopg2.connect(os.environ['P1_DB_URL'],connect_timeout=30); c.autocommit=False; cur=c.cursor(); cur.execute("set statement_timeout=0")
# 1) CNPJ por órgão: pncp_orgaos SC estadual (menor cnpj por nome normalizado)
cur.execute("select razao_social, cnpj from pncp_orgaos where uf='SC' and esfera='E' and razao_social is not null")
cnpj_by={}
for razao,cnpj in cur.fetchall():
    k=norm(razao)
    if k and (k not in cnpj_by or cnpj<cnpj_by[k][1]): cnpj_by[k]=(razao,cnpj)
# 2) contato por órgão: diretorio SC (nome e sigla)
cur.execute("select nome, sigla, emails, telefones, site, cnpjs_pncp from diretorio_orgaos where uf='SC'")
dir_nome={}; dir_sig={}
for nome,sig,ems,tls,site,cn in cur.fetchall():
    rec={'nome':nome,'email':(ems or [None])[0],'tel':(tls or [None])[0],'site':site,'cnpj':(cn or [None])[0]}
    dir_nome[norm(nome)]=rec
    if sig and len(sig.strip())>=3: dir_sig[norm(sig)]=rec
# 3) órgãos distintos nos registros SC estaduais do painel1
cur.execute("""select orgao, count(*) from painel1_servidores where uf='SC' and esfera='estadual' and orgao is not null
   and origem like 'p12sc:%%' or (uf='SC' and esfera='estadual' and origem='arquivo:tce_sc_servidores') group by 1""")
orgs=cur.fetchall(); log(f'órgãos distintos SC estadual no painel1: {len(orgs)}')
def resolve(orgao):
    b=base(orgao); cnpj=email=tel=site=razao=None
    # CNPJ
    if b in cnpj_by: razao,cnpj=cnpj_by[b]
    else:
        for k,(rz,cj) in cnpj_by.items():
            if b and (b in k or k in b): razao,cnpj=rz,cj; break
    # contato (diretorio por nome contendo, ou sigla)
    d=dir_nome.get(b)
    if not d:
        for k,rec in dir_nome.items():
            if b and (b in k or k in b): d=rec; break
    if not d:
        toks=[t for t in re.findall(r'[A-Z]{3,}',b)]
        for t in toks:
            if t in dir_sig: d=dir_sig[t]; break
    if d:
        email,tel,site=d['email'],d['tel'],d['site']
        if not cnpj and d.get('cnpj'): cnpj=d['cnpj']; razao=razao or d['nome']
    return razao,cnpj,email,tel,site
n_upd=n_org=0
for orgao,cnt in orgs:
    razao,cnpj,email,tel,site=resolve(orgao)
    if not (cnpj or email or tel): continue
    ent=[]
    if razao or cnpj: ent.append('Entidade: '+(razao or orgao)+(f' · CNPJ {cnpj}' if cnpj else ''))
    inst=[x for x in [email,(tel and 'tel '+tel),site] if x]
    if inst: ent.append('Institucional: '+' · '.join(inst))
    nota=' · '.join(ent)
    cur.execute("""update painel1_servidores set
        email=coalesce(nullif(email,''), %s), telefone=coalesce(nullif(telefone,''), %s),
        contato_adicional = case when contato_adicional is null or contato_adicional='' then %s
             when position('Entidade:' in contato_adicional)>0 then contato_adicional else contato_adicional||' · '||%s end
      where uf='SC' and esfera='estadual' and orgao=%s""",(email,tel,nota,nota,orgao))
    n_upd+=cur.rowcount; n_org+= (1 if cur.rowcount else 0)
    if n_org%10==0: c.commit()
c.commit()
log(f'órgãos resolvidos: {n_org} · registros atualizados: {n_upd}')
cur.execute("select count(email), count(telefone), count(*) filter (where contato_adicional like 'Entidade:%%' or contato_adicional like '%% · Entidade:%%') from painel1_servidores where uf='SC' and esfera='estadual'")
log(f'SC estadual agora (c/ email, c/ tel, c/ entidade+cnpj): {cur.fetchone()}')
cur.execute("select nome, orgao, email, telefone, left(contato_adicional,110) from painel1_servidores where uf='SC' and esfera='estadual' and contato_adicional like '%%Entidade:%%CNPJ%%' limit 3")
for r in cur.fetchall(): log(f'  ex: {r[0][:22]} | {r[1][:24]} | {r[2]} | {r[3]} | {r[4]}')
try: cur.execute("select p1_refresh_stats()"); c.commit()
except Exception as e: log('refresh: '+str(e)[:60])
c.close()
