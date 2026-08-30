#!/usr/bin/env python3
"""Carrega/atualiza pncp_orgaos, pncp_unidades, uasg, orgaos_siasg a partir dos ledgers da coleta
(orgaos.jsonl, unidades.jsonl, uasg.jsonl, orgaos_siasg.jsonl, entes_autorizados.json). UPSERT — pode rodar
a qualquer momento (inclusive com a varredura em andamento) e ao final. Sede do órgão = moda do município
das unidades. publicou_pncp = CNPJ presente em cadastro_institucional_br ou obras_engenharia_orgaos.
cliente_pncp = ente autorizado do login do usuário. Credencial: env P1_DB_URL."""
import io, json, os, time, collections, psycopg2
JOB=os.path.dirname(os.path.abspath(__file__))
def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)
NAT={'1015':'Órgão Público do Poder Executivo Federal','1023':'Órgão Público do Poder Executivo Estadual ou do DF','1031':'Órgão Público do Poder Executivo Municipal',
 '1040':'Órgão Público do Poder Legislativo Federal','1058':'Órgão Público do Poder Legislativo Estadual ou do DF','1066':'Órgão Público do Poder Legislativo Municipal',
 '1074':'Órgão Público do Poder Judiciário Federal','1082':'Órgão Público do Poder Judiciário Estadual','1104':'Autarquia Federal','1112':'Autarquia Estadual ou do DF','1120':'Autarquia Municipal',
 '1139':'Fundação Pública de Direito Público Federal','1147':'Fundação Pública de Direito Público Estadual ou do DF','1155':'Fundação Pública de Direito Público Municipal',
 '1163':'Órgão Público Autônomo Federal','1171':'Órgão Público Autônomo Estadual ou do DF','1180':'Órgão Público Autônomo Municipal','1198':'Comissão Polinacional',
 '1210':'Consórcio Público de Direito Público (Associação Pública)','1228':'Consórcio Público de Direito Privado','1236':'Estado ou Distrito Federal','1244':'Município',
 '1252':'Fundação Pública de Direito Privado Federal','1260':'Fundação Pública de Direito Privado Estadual ou do DF','1279':'Fundação Pública de Direito Privado Municipal',
 '1287':'Fundo Público da Administração Indireta Federal','1295':'Fundo Público da Administração Indireta Estadual ou do DF','1309':'Fundo Público da Administração Indireta Municipal',
 '1317':'Fundo Público da Administração Direta Federal','1325':'Fundo Público da Administração Direta Estadual ou do DF','1333':'Fundo Público da Administração Direta Municipal','1341':'União',
 '2011':'Empresa Pública','2038':'Sociedade de Economia Mista','2046':'Sociedade Anônima Aberta','2054':'Sociedade Anônima Fechada','2062':'Sociedade Empresária Limitada','3999':'Associação Privada','3069':'Fundação Privada','3131':'Entidade Sindical','3220':'Organização Religiosa'}
def jl(name):
    p=os.path.join(JOB,name)
    if not os.path.exists(p): return []
    out=[]
    for ln in open(p,encoding='utf-8'):
        try: out.append(json.loads(ln))
        except Exception: pass
    return out
orgs={}
for r in jl('orgaos.jsonl'):
    if r.get('status')==200 and r.get('dados') and r['dados'].get('cnpj'): orgs[r['id']]=r['dados']
unis=jl('unidades.jsonl'); uasg=jl('uasg.jsonl'); siasg=jl('orgaos_siasg.jsonl')
try: entes={e['cnpj'] for e in json.load(open(os.path.join(JOB,'entes_autorizados.json')))['entes']}
except Exception: entes=set()
log(f'ledger: {len(orgs)} órgãos · {len(unis)} respostas de unidades · {len(uasg)} uasg · {len(siasg)} órgãos siasg · {len(entes)} entes autorizados')
# unidades por cnpj (dedup por id)
uni_rows={}; sede={}
for u in unis:
    if u.get('status')!=200 or not u.get('unidades'): continue
    cnt=collections.Counter()
    for x in u['unidades']:
        m=x.get('municipio') or {}; ufo=(m.get('uf') or {})
        uni_rows[x['id']]=(x['id'],u.get('orgao_id'),u['cnpj'],x.get('codigoUnidade'),x.get('nomeUnidade'),ufo.get('siglaUF'),m.get('codigoIbge'),m.get('nome'),x.get('statusAtivo'),x.get('dataInclusao'),x.get('dataAtualizacao'))
        if m.get('codigoIbge'): cnt[(ufo.get('siglaUF'),m.get('codigoIbge'),m.get('nome'))]+=1
    if cnt: sede[u['cnpj']]=(cnt.most_common(1)[0][0],sum(cnt.values()))
conn=psycopg2.connect(os.environ['P1_DB_URL'],connect_timeout=20); conn.autocommit=False; cur=conn.cursor(); cur.execute('set statement_timeout=0')
cur.execute("select cnpj from cadastro_institucional_br union select cnpj from obras_engenharia_orgaos"); pub={r[0] for r in cur.fetchall() if r[0]}
def cl(x): return '\\N' if x is None else str(x).replace('\\',' ').replace('\t',' ').replace('\n',' ').replace('\r',' ')
def copy_upsert(table,cols,rows,key,update_cols):
    if not rows: return 0
    cur.execute(f"create temp table tmp_{table} (like {table} including defaults) on commit drop")
    buf=io.StringIO(); [buf.write('\t'.join(cl(v) for v in r)+'\n') for r in rows]; buf.seek(0)
    cur.copy_expert(f"copy tmp_{table} ({','.join(cols)}) from stdin with (format text, null '\\N')",buf)
    sets=', '.join(f"{c}=excluded.{c}" for c in update_cols)
    cur.execute(f"insert into {table} ({','.join(cols)}) select {','.join(cols)} from tmp_{table} on conflict ({key}) do update set {sets}")
    return len(rows)
# órgãos
O_COLS=['orgao_id','cnpj','razao_social','nome_fantasia','cod_natureza_juridica','natureza_juridica','poder','esfera','situacao_cadastral','validado','status_ativo','data_inclusao','data_atualizacao','n_unidades','uf','cod_ibge','municipio','publicou_pncp','cliente_pncp']
rows=[]
for oid,d in orgs.items():
    s=sede.get(d['cnpj']); (uf,ib,mun),n=(s if s else ((None,None,None),0))
    rows.append((oid,d['cnpj'],d.get('razaoSocial'),d.get('nomeFantasia'),d.get('codigoNaturezaJuridica'),NAT.get(str(d.get('codigoNaturezaJuridica')),None),d.get('poderId'),d.get('esferaId'),d.get('situacaoCadastral'),d.get('validado'),d.get('statusAtivo'),d.get('dataInclusao'),d.get('dataAtualizacao'),n,uf,ib,mun,d['cnpj'] in pub,d['cnpj'] in entes))
n=copy_upsert('pncp_orgaos',O_COLS,rows,'orgao_id',[c for c in O_COLS if c!='orgao_id']); conn.commit(); log(f'pncp_orgaos: upsert {n}')
U_COLS=['id','orgao_id','cnpj','codigo_unidade','nome_unidade','uf','cod_ibge','municipio','status_ativo','data_inclusao','data_atualizacao']
urows=[r for r in uni_rows.values() if r[1] in orgs]   # FK: só de órgãos já carregados
n=copy_upsert('pncp_unidades',U_COLS,urows,'id',[c for c in U_COLS if c!='id']); conn.commit(); log(f'pncp_unidades: upsert {n} (de {len(uni_rows)} lidas)')
# uasg / siasg
A_COLS=['codigo_uasg','nome_uasg','uso_sisg','adesao_siasg','uf','cod_ibge','municipio','cnpj_uasg','codigo_orgao','cnpj_orgao','cnpj_orgao_vinculado','cnpj_orgao_superior','codigo_siorg','status_uasg','data_implantacao']
arows={u['codigoUasg']:(u['codigoUasg'],u.get('nomeUasg'),u.get('usoSisg'),u.get('adesaoSiasg'),u.get('siglaUf'),(str(u['codigoMunicipioIbge']) if u.get('codigoMunicipioIbge') else None),u.get('nomeMunicipioIbge'),u.get('cnpjCpfUasg') or None,(str(u['codigoOrgao']) if u.get('codigoOrgao') is not None else None),(u.get('cnpjCpfOrgao') if (u.get('cnpjCpfOrgao') or '0')!='0' else None),u.get('cnpjCpfOrgaoVinculado'),u.get('cnpjCpfOrgaoSuperior'),u.get('codigoSiorg') or None,u.get('statusUasg'),(u.get('dataImplantacaoSidec') or '')[:10] or None) for u in uasg}
n=copy_upsert('uasg',A_COLS,list(arows.values()),'codigo_uasg',[c for c in A_COLS if c!='codigo_uasg']); conn.commit(); log(f'uasg: upsert {n}')
S_COLS=['codigo_orgao','nome_orgao','mnemonico','cnpj_orgao','codigo_orgao_vinculado','cnpj_orgao_vinculado','nome_orgao_vinculado','codigo_orgao_superior','cnpj_orgao_superior','nome_orgao_superior','tipo_administracao','poder','esfera','uso_sisg','status_orgao']
srows={str(s['codigoOrgao']):(str(s['codigoOrgao']),s.get('nomeOrgao'),s.get('nomeMnemonicoOrgao'),(s.get('cnpjCpfOrgao') if (s.get('cnpjCpfOrgao') or '0')!='0' else None),(str(s['codigoOrgaoVinculado']) if s.get('codigoOrgaoVinculado') is not None else None),s.get('cnpjCpfOrgaoVinculado'),s.get('nomeOrgaoVinculado'),(str(s['codigoOrgaoSuperior']) if s.get('codigoOrgaoSuperior') is not None else None),s.get('cnpjCpfOrgaoSuperior'),s.get('nomeOrgaoSuperior'),s.get('nomeTipoAdministracao'),s.get('poder'),s.get('esfera'),s.get('usoSisg'),s.get('statusOrgao')) for s in siasg}
n=copy_upsert('orgaos_siasg',S_COLS,list(srows.values()),'codigo_orgao',[c for c in S_COLS if c!='codigo_orgao']); conn.commit(); log(f'orgaos_siasg: upsert {n}')
for t in ('pncp_orgaos','pncp_unidades','uasg','orgaos_siasg'): cur.execute(f'analyze {t}')
conn.commit()
cur.execute("select count(*), count(uf), count(*) filter (where n_unidades>0), count(*) filter (where publicou_pncp), count(*) filter (where cliente_pncp) from pncp_orgaos"); log(f'pncp_orgaos agora: (tot, c/uf, c/unidades, publicou, cliente) = {cur.fetchone()}')
cur.execute("select count(*), count(distinct cnpj) from pncp_unidades"); log(f'pncp_unidades agora: {cur.fetchone()}')
conn.close()
