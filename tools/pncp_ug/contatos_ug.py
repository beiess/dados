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
    d=org[c]; d.setdefault('email',em); d.setdefault('telefone',(ct or '').split('|')[0].strip() or None); d.setdefault('site',si); d.setdefault('portal',po); d.setdefault('ouvidoria',ou); d.setdefault('fonte','cadastro MG')
    for p in (es or '').split('|'):
        if '@' in p:
            lab,_,mail=p.partition(':'); m=re.search(r'[\w.+-]+@[\w.-]+\.\w+',mail or p)
            if m: setoriais[c].append((keys(lab if ':' in p else ''),lab.strip()[:60],m.group(0).lower()))
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
log(f'órgãos com algum contato (cnpj): {sum(1 for d in org.values() if d.get("email") or d.get("telefone"))}')
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
cur.execute("""select u.id, u.cnpj, u.codigo_unidade, u.nome_unidade, u.cod_ibge, o.razao_social, o.poder, o.esfera, u.municipio from pncp_unidades u join pncp_orgaos o using(cnpj)""")
rows=[]; n_set=n_pes=0
for uid,c,cod,nome,ib,razao,poder,esf,mun in cur.fetchall():
    d=org.get(c,{}); tp='CM' if (poder=='L' or 'CAMARA' in unac(razao)) else 'PM'
    ks=keys(nome)-keys(razao)-keys(mun)   # palavras-chave PROPRIAS da unidade (tira nome do orgao/municipio); vazio = unidade generica
    best=None
    for kk,lab,mail in setoriais.get(c,[]):
        sc=len(ks&kk)
        if sc and (not best or sc>best[0]): best=(sc,lab,mail)
    email_setor=(best[2] if best else None); fonte_setor=('setorial MG: '+best[1]) if best else None
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
    rows.append((uid,d.get('email'),d.get('telefone'),d.get('site'),d.get('portal'),d.get('ouvidoria'),email_setor,contato_pessoa,(1 if d.get('email') or d.get('telefone') else 0)+(1 if email_setor else 0)+len(pes),fonte))
log(f'unidades: {len(rows)} · com e-mail setorial {n_set} · com pessoa {n_pes} · com contato de órgão {sum(1 for r in rows if r[1] or r[2])}')
cur.execute("""create table if not exists pncp_ug_contatos (unidade_id bigint primary key, email_orgao text, telefone_orgao text, site text, portal_transparencia text, ouvidoria text,
  email_setor text, contato_pessoa text, n_contatos int, fonte text); alter table pncp_ug_contatos enable row level security;
  drop policy if exists pncp_ug_contatos_read on pncp_ug_contatos; create policy pncp_ug_contatos_read on pncp_ug_contatos for select to authenticated using (true);
  revoke all on pncp_ug_contatos from anon; grant select on pncp_ug_contatos to authenticated, service_role; truncate pncp_ug_contatos""")
def cl(x): return '\\N' if x is None else str(x).replace('\\',' ').replace('\t',' ').replace('\n',' ').replace('\r',' ')
buf=io.StringIO(); [buf.write('\t'.join(cl(v) for v in r)+'\n') for r in rows]; buf.seek(0)
cur.copy_expert("copy pncp_ug_contatos (unidade_id,email_orgao,telefone_orgao,site,portal_transparencia,ouvidoria,email_setor,contato_pessoa,n_contatos,fonte) from stdin with (format text, null '\\N')",buf)
cur.execute("""create or replace view v_pncp_ug as
select u.id, u.uf, u.municipio, u.cod_ibge, o.razao_social as orgao, o.cnpj, u.codigo_unidade, u.nome_unidade,
  case o.esfera when 'M' then 'municipal' when 'E' then 'estadual' when 'F' then 'federal' when 'D' then 'distrital' else null end as esfera,
  case o.poder when 'E' then 'Executivo' when 'L' then 'Legislativo' when 'J' then 'Judiciário' when 'M' then 'Ministério Público' else null end as poder,
  o.natureza_juridica, o.cod_natureza_juridica,
  c.email_orgao, c.telefone_orgao, c.site, c.portal_transparencia, c.ouvidoria, c.email_setor, c.contato_pessoa, c.n_contatos, c.fonte as fonte_contato,
  a.codigo_uasg, a.nome_uasg, a.uso_sisg, a.codigo_siorg,
  o.orgao_id, o.n_unidades, o.validado, o.publicou_pncp, o.cliente_pncp, u.status_ativo, u.data_inclusao, o.data_inclusao as orgao_data_inclusao,
  o.situacao_cadastral as situacao_rfb, r.logradouro||coalesce(', '||r.numero,'')||coalesce(' - '||r.bairro,'')||coalesce(' · CEP '||r.cep,'') as endereco_rfb
from pncp_unidades u join pncp_orgaos o on o.orgao_id=u.orgao_id
left join pncp_ug_contatos c on c.unidade_id=u.id
left join uasg a on a.codigo_uasg=u.codigo_unidade and a.cnpj_orgao=u.cnpj
left join pncp_orgaos_rfb r on r.cnpj=u.cnpj and r.status=200""")
cur.execute("revoke all on v_pncp_ug from anon; grant select on v_pncp_ug to authenticated, service_role")
conn.commit(); cur.execute("select pg_notify('pgrst','reload schema')"); conn.commit()
cur.execute("select count(*), count(email_orgao), count(email_setor), count(contato_pessoa), count(codigo_uasg) from v_pncp_ug"); log(f'v_pncp_ug: (tot, email_orgao, email_setor, contato_pessoa, uasg) = {cur.fetchone()}')
cur.execute("select nome_unidade, municipio, uf, email_orgao, email_setor, left(contato_pessoa,90) from v_pncp_ug where email_setor is not null or contato_pessoa is not null limit 4"); [log(f'  ex: {r}') for r in cur.fetchall()]
conn.close()
