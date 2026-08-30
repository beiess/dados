#!/usr/bin/env python3
"""Contatos por Unidade Gestora (PNCP) → tabela pncp_ug_contatos (1 linha por unidade) + view v_pncp_ug.
Nível ÓRGÃO (por CNPJ; prioridade cadastro MG curado > cadastro BR > obras/RFB): email, telefone, site, portal, ouvidoria.
Nível UNIDADE (heurística por palavras-chave do nome da unidade × rótulos): e-mails setoriais do cadastro MG,
pessoas de contatos_orgaos_fontes (cnpj/ibge), painel14 gestores (ibge), email_vinculos (cnpj, ≤3 pessoas).
Também preenche sede (uf/ibge/município) de órgãos sem unidades a partir de uasg/cadastros. Re-executável (truncate+copy)."""
import io, os, re, time, unicodedata, collections, psycopg2
def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)
def unac(s): return ''.join(c for c in unicodedata.normalize('NFD', str(s or '')) if unicodedata.category(c) != 'Mn').upper()
STOP=set('SECRETARIA SEC SECR MUNICIPAL MUN MUNICIPIO ESTADUAL EST FEDERAL DE DA DO DAS DOS E EM A O AS OS FUNDO FUNDACAO GERENCIA DEPARTAMENTO DEPTO COORDENADORIA DIRETORIA SUPERINTENDENCIA SETOR DIVISAO UNIDADE ADMINISTRATIVA GESTORA PREFEITURA CAMARA GABINETE INSTITUTO AUTARQUIA AGENCIA CENTRAL CENTRO NUCLEO SERVICO SERVICOS ADJUNTA ADJ PARA COM SUB SUBSECRETARIA REGIONAL GERAL EXECUTIVA EXECUTIVO PODER PUBLICO PUBLICA NACIONAL ORGAO ENTIDADE'.split())
SYN={'SAUDE':'SAUDE','EDUCACAO':'EDUCACAO','ENSINO':'EDUCACAO','ESCOLA':'EDUCACAO','OBRAS':'OBRAS','INFRAESTRUTURA':'OBRAS','INFRA':'OBRAS','ENGENHARIA':'OBRAS','URBANISMO':'OBRAS','ADMINISTRACAO':'ADMINISTRACAO','ADM':'ADMINISTRACAO','FAZENDA':'FAZENDA','FINANCAS':'FAZENDA','FINANCEIRO':'FAZENDA','TESOURARIA':'FAZENDA','CONTABILIDADE':'CONTABILIDADE','CONTABIL':'CONTABILIDADE','TRIBUTOS':'TRIBUTOS','ARRECADACAO':'TRIBUTOS','TRIBUTACAO':'TRIBUTOS','ASSISTENCIA':'ASSISTENCIA','SOCIAL':'ASSISTENCIA','CRAS':'ASSISTENCIA','CREAS':'ASSISTENCIA','CULTURA':'CULTURA','ESPORTE':'ESPORTE','ESPORTES':'ESPORTE','LAZER':'ESPORTE','TURISMO':'TURISMO','AMBIENTE':'MEIO AMBIENTE','AMBIENTAL':'MEIO AMBIENTE','AGRICULTURA':'AGRICULTURA','AGRICOLA':'AGRICULTURA','PLANEJAMENTO':'PLANEJAMENTO','LICITACAO':'LICITACAO','LICITACOES':'LICITACAO','COMPRAS':'LICITACAO','PREGAO':'LICITACAO','CONTRATOS':'LICITACAO','CONTROLE':'CONTROLE INTERNO','CONTROLADORIA':'CONTROLE INTERNO','JURIDICO':'JURIDICO','JURIDICA':'JURIDICO','PROCURADORIA':'JURIDICO','ADVOCACIA':'JURIDICO','TRANSPORTE':'TRANSPORTE','TRANSPORTES':'TRANSPORTE','TRANSITO':'TRANSPORTE','HABITACAO':'HABITACAO','DESENVOLVIMENTO':'DESENVOLVIMENTO','SEGURANCA':'SEGURANCA','GOVERNO':'GOVERNO','GESTAO':'ADMINISTRACAO','RECURSOS':'RH','HUMANOS':'RH','RH':'RH','PESSOAL':'RH','FOLHA':'RH','COMUNICACAO':'COMUNICACAO','IMPRENSA':'COMUNICACAO','TECNOLOGIA':'TI','INFORMATICA':'TI','TI':'TI','OUVIDORIA':'OUVIDORIA','PREVIDENCIA':'PREVIDENCIA','SANEAMENTO':'SANEAMENTO','AGUA':'SANEAMENTO','SAAE':'SANEAMENTO','LIMPEZA':'SERVICOS URBANOS','URBANOS':'SERVICOS URBANOS','HOSPITAL':'SAUDE','UPA':'SAUDE','VIGILANCIA':'SAUDE','CRIANCA':'ASSISTENCIA','ADOLESCENTE':'ASSISTENCIA','IDOSO':'ASSISTENCIA','MULHER':'ASSISTENCIA','JUVENTUDE':'ASSISTENCIA','PATRIMONIO':'ADMINISTRACAO','ALMOXARIFADO':'ADMINISTRACAO','FROTA':'TRANSPORTE','DEFESA':'DEFESA CIVIL','CIVIL':'DEFESA CIVIL','CONVENIOS':'PLANEJAMENTO','PROJETOS':'PLANEJAMENTO','ILUMINACAO':'SERVICOS URBANOS','CEMITERIO':'SERVICOS URBANOS','MERENDA':'EDUCACAO','ALIMENTACAO':'EDUCACAO','CIENCIA':'CIENCIA','INOVACAO':'CIENCIA','TRABALHO':'TRABALHO','EMPREGO':'TRABALHO','INDUSTRIA':'DESENVOLVIMENTO','COMERCIO':'DESENVOLVIMENTO','ECONOMICO':'DESENVOLVIMENTO','DIREITOS':'DIREITOS HUMANOS','CIDADANIA':'DIREITOS HUMANOS','LEGISLATIVO':'LEGISLATIVO','VEREADOR':'LEGISLATIVO','PRESIDENCIA':'GABINETE','GABINETE':'GABINETE','PREFEITO':'GABINETE','SECRETARIO':'GABINETE','CHEFE':'GABINETE'}
PRIO=['prefeitura','gabinete','contato','ouvidoria','licitacao','licitacoes','compras','administracao','secretaria','camara','presidencia','faleconosco','atendimento','protocolo','sac','geral','adm','cpl','pregao']
GENERIC={'gmail.com','hotmail.com','yahoo.com.br','yahoo.com','outlook.com','bol.com.br','uol.com.br','terra.com.br','live.com','icloud.com','msn.com','globo.com','ig.com.br'}
def split_emails(v):
    seen=[];
    for m in re.findall(r'[\w.+-]+@[\w.-]+\.\w+', str(v or '').lower()):
        if m not in seen: seen.append(m)
    return seen
def local_words(e): return e.split('@')[0].replace('.',' ').replace('_',' ').replace('-',' ')
def top_emails(v,n=5):
    es=split_emails(v)
    if not es: return None
    def pr(e):
        lp=e.split('@')[0]
        for i,k in enumerate(PRIO):
            if lp.startswith(k) or lp==k: return i
        return 50+(0 if e.split('@')[1] not in GENERIC else 20)
    es=sorted(es,key=pr)
    return ', '.join(es[:n])
def keys(s):
    ks=set()
    for w in re.findall(r'[A-Z0-9]+',unac(s)):
        if w in STOP or len(w)<3: continue
        ks.add(SYN.get(w,w))
    return ks
conn=psycopg2.connect(os.environ['P1_DB_URL'],connect_timeout=20); conn.autocommit=False; cur=conn.cursor(); cur.execute('set statement_timeout=0')
# 0) sede de órgãos sem unidades: uasg (cnpj_orgao) > cadastro BR > cadastro MG
cur.execute("""update pncp_orgaos o set uf=s.uf, cod_ibge=s.cod_ibge, municipio=s.municipio from (
  select cnpj, uf, cod_ibge, municipio from (
    select cnpj_orgao cnpj, uf, cod_ibge, municipio, 1 pr from uasg where cod_ibge is not null and status_uasg
    union all select cnpj, uf, cod_ibge, municipio, 2 from cadastro_institucional_br where cod_ibge is not null
    union all select regexp_replace(cnpj,'\D','','g'), uf, ibge, cidade, 3 from cadastro_institucional where ibge is not null and cnpj is not null
    union all select cnpj, uf, cod_ibge, initcap(municipio), 4 from pncp_orgaos_rfb where status=200 and cod_ibge is not null) x
  where cnpj is not null qualify_placeholder) s where o.cnpj=s.cnpj and o.uf is null""".replace(' qualify_placeholder',''))
log(f'sede preenchida por uasg/cadastros/RFB: {cur.rowcount}'); conn.commit()
cur.execute("update pncp_orgaos o set situacao_cadastral=r.situacao from pncp_orgaos_rfb r where r.cnpj=o.cnpj and r.status=200 and r.situacao is not null and o.situacao_cadastral is distinct from r.situacao")
log(f'situação cadastral (RFB) atualizada: {cur.rowcount}'); conn.commit()
# 1) contatos nível órgão por cnpj
org=collections.defaultdict(dict)
cur.execute("select regexp_replace(cnpj,'\D','','g'), email, contato, site_oficial, portal_transparencia, ouvidoria, emails_setoriais from cadastro_institucional where cnpj is not null")
setoriais=collections.defaultdict(list)
for c,em,ct,si,po,ou,es in cur.fetchall():
    if len(c)!=14: continue
    d=org[c]; d.setdefault('email',top_emails(em)); d.setdefault('telefone',(ct or '').split('|')[0].strip() or None); d.setdefault('site',si); d.setdefault('portal',po); d.setdefault('ouvidoria',ou); d.setdefault('fonte','cadastro MG')
    for e in split_emails(em): setoriais[c].append((keys(local_words(e)),e.split('@')[0][:60],e))
    for p in (es or '').split('|'):
        if '@' in p:
            lab,_,mail=p.partition(':'); m=re.search(r'[\w.+-]+@[\w.-]+\.\w+',mail or p)
            if m: setoriais[c].append((keys(lab if ':' in p else ''),lab.strip()[:60],m.group(0).lower()))
cur.execute("select c.cnpj, d.emails, d.telefones, d.site, d.ouvidoria_url, d.endereco from diretorio_orgaos_cnpj c join diretorio_orgaos d on d.id=c.diretorio_id")
for c,ems,tls,si,ou,en in cur.fetchall():
    d=org[c]
    for k,v in (('email',', '.join((ems or [])[:5]) or None),('telefone',(tls or [None])[0]),('site',si),('ouvidoria',ou)):
        if v and not d.get(k): d[k]=v
    d.setdefault('fonte','diretório oficial')
cur.execute("select cnpj, email, telefone, site, portal_transparencia, ouvidoria from cadastro_institucional_br")
for c,em,tl,si,po,ou in cur.fetchall():
    d=org[c]; 
    for k,v in (('email',em),('telefone',tl),('site',si),('portal',po),('ouvidoria',ou)):
        if v and not d.get(k): d[k]=v
    d.setdefault('fonte','cadastro BR')
cur.execute("select cnpj, email, telefone, site from obras_engenharia_orgaos")
for c,em,tl,si in cur.fetchall():
    d=org[c]
    for k,v in (('email',em),('telefone',tl),('site',si)):
        if v and not d.get(k): d[k]=v
    d.setdefault('fonte','obras/RFB')
cur.execute("select cnpj, email, telefone from pncp_orgaos_rfb where status=200 and (email is not null or telefone is not null)")
for c,em,tl in cur.fetchall():
    d=org[c]
    for k,v in (('email',em),('telefone',tl)):
        if v and not d.get(k): d[k]=v
    d.setdefault('fonte','RFB')
cur.execute("""select v.email, v.cnpjs, coalesce(x.role_based,false), x.tipo from email_vinculos v left join email_validacao x using(email)
  where v.cnpjs is not null and cardinality(v.cnpjs)>0 and coalesce(x.smtp_status,'') <> 'invalido' and coalesce(x.descartavel,false)=false""")
vinc_mail=collections.defaultdict(list)
for em,cs,role,tipo in cur.fetchall():
    for c in cs:
        vinc_mail[c].append((0 if role else (1 if tipo in ('institucional','corporativo') else 2),em))
        setoriais[c].append((keys(local_words(em)),em.split('@')[0][:60],em))
n_fb=0
for c,lst in vinc_mail.items():
    d=org[c]
    if not d.get('email'):
        lst.sort(); d['email']=', '.join(dict.fromkeys(e for _,e in lst[:3])); d.setdefault('fonte','vínculos de e-mail (P15)'); n_fb+=1
log(f'e-mail do órgão via email_vinculos (fallback): {n_fb}')
log(f'órgãos com algum contato (cnpj): {sum(1 for d in org.values() if d.get("email") or d.get("telefone"))}')
# (3) domínio institucional de órgãos federais/estaduais (painel1: domínio mais comum entre ≥5 servidores do órgão)
cur.execute("""select o, dom from (select f_unaccent(upper(orgao)) o, split_part(lower(email),'@',2) dom, count(*) n,
   row_number() over (partition by f_unaccent(upper(orgao)) order by count(*) desc) rn
   from painel1_servidores where esfera in ('federal','estadual') and email like '%@%' group by 1,2) x where rn=1 and n>=5""")
dom_org={o:d for o,d in cur.fetchall() if d and d not in GENERIC}
log(f'domínios institucionais (painel1, fed/est): {len(dom_org)}')
# 2) pessoas candidatas: por cnpj e por ibge
pess_cnpj=collections.defaultdict(list); pess_ibge=collections.defaultdict(list)
cur.execute("select cnpj, ibge, nome_pessoa, cargo, setor, email, telefone1, melhor_contato, tipo_orgao from contatos_orgaos_fontes where email is not null or telefone1 is not null")
for c,ib,nome,cargo,setor,em,tel,best,tp in cur.fetchall():
    rec=(keys((cargo or '')+' '+(setor or '')),nome,cargo,em,tel,2 if best else 1,'contatos')
    c=re.sub(r'\D','',c or '')
    if len(c)==14: pess_cnpj[c].append(rec)
    elif ib: pess_ibge[(ib,tp)].append(rec)
cur.execute("select ibge, orgao, nome, cargo, setor, area, email, telefone from painel14_gestores_rh where ibge is not null and (email is not null or telefone is not null)")
for ib,orgn,nome,cargo,setor,area,em,tel in cur.fetchall():
    pess_ibge[(ib,'PM' if not re.search('CAMARA',unac(orgn)) else 'CM')].append((keys((cargo or '')+' '+(setor or '')+' '+(area or '')),nome,cargo,em,tel,1,'gestores'))
cur.execute("select email, nome, cargo, setor, cnpjs from email_vinculos where n_pessoas between 1 and 3 and cnpjs is not null and cardinality(cnpjs)>0")
for em,nome,cargo,setor,cs in cur.fetchall():
    for c in cs: pess_cnpj[c].append((keys((cargo or '')+' '+(setor or '')),nome,cargo,em,None,1,'vinculos'))
log(f'pessoas candidatas: por cnpj {sum(len(v) for v in pess_cnpj.values())} · por ibge {sum(len(v) for v in pess_ibge.values())}')
# 3) unidades
cur.execute("select uf, nome_norm, sigla, emails, telefones, site, ouvidoria_url from diretorio_orgaos where cardinality(emails)>0 or cardinality(telefones)>0")
dir_nome={}; dir_sigla={}
for uf_,nn,sg,ems,tls,si,ou in cur.fetchall():
    rec={'emails':ems or [],'telefones':tls or [],'site':si,'ouvidoria':ou}
    dir_nome[(uf_,nn)]=rec
    if sg and len(sg)>=3: dir_sigla.setdefault((uf_,unac(sg)),rec)
log(f'diretório p/ casamento por unidade: {len(dir_nome)} nomes · {len(dir_sigla)} siglas')
def dir_unidade(uf_,esf_,nome_u):
    ufs_=[uf_,'BR'] if esf_=='F' else [uf_]
    nn=unac(nome_u)
    for u_ in ufs_:
        if (u_,nn) in dir_nome: return dir_nome[(u_,nn)]
    toks=set(re.findall(r'[A-Z0-9-]{3,}',nn))
    for u_ in ufs_:
        for t in toks:
            if (u_,t) in dir_sigla: return dir_sigla[(u_,t)]
    return None
n_dir=0
cur.execute("""select u.id, u.cnpj, u.codigo_unidade, u.nome_unidade, u.cod_ibge, o.razao_social, o.poder, o.esfera, u.municipio, u.uf from pncp_unidades u join pncp_orgaos o using(cnpj)""")
rows=[]; n_set=n_pes=0
for uid,c,cod,nome,ib,razao,poder,esf,mun,uuf in cur.fetchall():
    d=org.get(c,{}); tp='CM' if (poder=='L' or 'CAMARA' in unac(razao)) else 'PM'
    ks=keys(nome)-keys(razao)-keys(mun)   # palavras-chave PROPRIAS da unidade (tira nome do orgao/municipio); vazio = unidade generica
    best=None
    for kk,lab,mail in setoriais.get(c,[]):
        sc=len(ks&kk)
        if sc and (not best or sc>best[0]): best=(sc,lab,mail)
    email_setor=(best[2] if best else None); fonte_setor=('setorial MG: '+best[1]) if best else None
    du=dir_unidade(uuf,esf,nome) if nome else None   # diretório oficial casado pelo nome/sigla da própria unidade (secretaria, autarquia…)
    if du:
        if du['emails'] and not email_setor: email_setor=', '.join(du['emails'][:3]); fonte_setor='diretório oficial (unidade)'
        if du['telefones'] and not d.get('telefone'): d=dict(d); d['telefone']=du['telefones'][0]
        if du['site'] and not d.get('site'): d=dict(d); d['site']=du['site']
        n_dir+=1
    sc_=lambda kk,pr,src: len(ks&kk)*10+(2 if pr==2 else 0)+(1 if src=='contatos' else 0)
    cand=[(sc_(kk,pr,src),nome_p,cargo,em,tel,src) for kk,nome_p,cargo,em,tel,pr,src in pess_cnpj.get(c,[])]
    if not cand and ib and esf=='M': cand=[(sc_(kk,pr,src),nome_p,cargo,em,tel,src) for kk,nome_p,cargo,em,tel,pr,src in pess_ibge.get((ib,tp),[])]   # municipio: so p/ orgaos municipais
    if ks: cand=[x for x in cand if x[0]>=10]          # unidade especifica (ex.: SAUDE): exige afinidade de palavra-chave
    else:  cand=[x for x in cand if x[0]>=2] or cand   # unidade generica: prefere melhor contato; senao qualquer do orgao
    cand.sort(key=lambda x:-x[0]); seen=set(); pes=[]
    for sc,nome_p,cargo,em,tel,src in cand:
        k=(unac(nome_p),(em or '').lower())
        if k in seen: continue
        seen.add(k); pes.append(' · '.join(x for x in [nome_p,cargo,em,tel] if x)+f' [{src}]')
        if len(pes)>=3: break
    contato_pessoa=' | '.join(pes) or None
    if email_setor: n_set+=1
    if contato_pessoa: n_pes+=1
    fonte=', '.join(x for x in [d.get('fonte'),fonte_setor] if x) or None
    dom=dom_org.get(unac(razao)) if esf in ('E','F') else None
    if not dom and d.get('email'): dom=d['email'].split(',')[0].split('@')[-1].strip() or None
    rows.append((uid,d.get('email'),d.get('telefone'),d.get('site'),d.get('portal'),d.get('ouvidoria'),email_setor,contato_pessoa,(1 if d.get('email') or d.get('telefone') else 0)+(1 if email_setor else 0)+len(pes),fonte,dom))
log(f'unidades: {len(rows)} · com e-mail setorial {n_set} · com pessoa {n_pes} · casadas c/ diretório {n_dir} · com contato de órgão {sum(1 for r in rows if r[1] or r[2])}')
cur.execute("""create table if not exists pncp_ug_contatos (unidade_id bigint primary key, email_orgao text, telefone_orgao text, site text, portal_transparencia text, ouvidoria text,
  email_setor text, contato_pessoa text, n_contatos int, fonte text, dominio_institucional text); alter table pncp_ug_contatos enable row level security;
  alter table pncp_ug_contatos add column if not exists dominio_institucional text;
  drop policy if exists pncp_ug_contatos_read on pncp_ug_contatos; create policy pncp_ug_contatos_read on pncp_ug_contatos for select to authenticated using (true);
  revoke all on pncp_ug_contatos from anon; grant select on pncp_ug_contatos to authenticated, service_role; truncate pncp_ug_contatos""")
def cl(x): return '\\N' if x is None else str(x).replace('\\',' ').replace('\t',' ').replace('\n',' ').replace('\r',' ')
buf=io.StringIO(); [buf.write('\t'.join(cl(v) for v in r)+'\n') for r in rows]; buf.seek(0)
cur.copy_expert("copy pncp_ug_contatos (unidade_id,email_orgao,telefone_orgao,site,portal_transparencia,ouvidoria,email_setor,contato_pessoa,n_contatos,fonte,dominio_institucional) from stdin with (format text, null '\\N')",buf)
cur.execute("drop view if exists v_pncp_ug")
cur.execute("""create view v_pncp_ug as
select u.id, u.uf, u.municipio, u.cod_ibge, o.razao_social as orgao, o.cnpj, u.codigo_unidade, u.nome_unidade,
  case o.esfera when 'M' then 'municipal' when 'E' then 'estadual' when 'F' then 'federal' when 'D' then 'distrital' else null end as esfera,
  case o.poder when 'E' then 'Executivo' when 'L' then 'Legislativo' when 'J' then 'Judiciário' when 'M' then 'Ministério Público' else null end as poder,
  o.natureza_juridica, o.cod_natureza_juridica,
  c.email_orgao, c.telefone_orgao, c.site, c.portal_transparencia, c.ouvidoria, c.email_setor, c.contato_pessoa, c.n_contatos, c.fonte as fonte_contato, c.dominio_institucional,
  a.codigo_uasg, a.nome_uasg, a.uso_sisg, a.codigo_siorg,
  o.orgao_id, o.n_unidades, o.validado, o.publicou_pncp, o.cliente_pncp, u.status_ativo, u.data_inclusao, o.data_inclusao as orgao_data_inclusao,
  o.situacao_cadastral as situacao_rfb, r.logradouro||coalesce(', '||r.numero,'')||coalesce(' - '||r.bairro,'')||coalesce(' · CEP '||r.cep,'') as endereco_rfb,
  greatest(u.data_alteracao, o.data_alteracao) as data_alteracao
from pncp_unidades u join pncp_orgaos o on o.orgao_id=u.orgao_id
left join pncp_ug_contatos c on c.unidade_id=u.id
left join uasg a on a.codigo_uasg=u.codigo_unidade and a.cnpj_orgao=u.cnpj
left join pncp_orgaos_rfb r on r.cnpj=u.cnpj and r.status=200""")
cur.execute("revoke all on v_pncp_ug from anon; grant select on v_pncp_ug to authenticated, service_role")
cur.execute("""create or replace view v_diretorio_cnpj as select c.cnpj, d.uf, d.nome, d.sigla, d.tipo, d.site, array_to_string(d.emails,', ') emails, array_to_string(d.telefones,' / ') telefones,
  d.ouvidoria_url, d.fale_conosco_url, d.endereco, d.redes_sociais, d.fonte_url from diretorio_orgaos_cnpj c join diretorio_orgaos d on d.id=c.diretorio_id;
  create or replace view v_apis_cnpj as select c.cnpj, a.nome, a.url, a.tipo, a.auth, a.formato, a.dominio, a.status, a.docs_url from apis_orgaos_cnpj c join apis_orgaos a on a.id=c.api_id;
  revoke all on v_diretorio_cnpj, v_apis_cnpj from anon; grant select on v_diretorio_cnpj, v_apis_cnpj to authenticated, service_role""")
conn.commit(); cur.execute("select pg_notify('pgrst','reload schema')"); conn.commit()
cur.execute("select count(*), count(email_orgao), count(email_setor), count(contato_pessoa), count(codigo_uasg) from v_pncp_ug"); log(f'v_pncp_ug: (tot, email_orgao, email_setor, contato_pessoa, uasg) = {cur.fetchone()}')
cur.execute("select nome_unidade, municipio, uf, email_orgao, email_setor, left(contato_pessoa,90) from v_pncp_ug where email_setor is not null or contato_pessoa is not null limit 4"); [log(f'  ex: {r}') for r in cur.fetchall()]
conn.close()
