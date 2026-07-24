#!/usr/bin/env python3
"""TSE → painel1_servidores.data_nascimento (MG).
Baixa consulta_cand (2024/2022/2020) de MG, casa por CPF (exato) e nome+município
(fallback, só quando a data é única), preenche APENAS nulos. Set-based via COPY+UPDATE."""
import csv, io, json, os, re, sys, time, unicodedata, urllib.request, zipfile

JOB = os.path.dirname(os.path.abspath(__file__))
import os
DB = os.environ["SUPABASE_DB_URL"]  # exporte de TCEMG/dados-painel/.supabase_env
ANOS = [2024, 2022, 2020]
URL = "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_{ano}.zip"

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.upper()).strip()

# município (nome norm) -> ibge, só MG
mun = {}
for m in json.load(open(os.path.join(JOB, "municipios_br.json"), encoding="utf-8")):
    if m["uf"] == "MG":
        mun[norm(m["nome"])] = m["ibge"]
log(f"{len(mun)} municípios MG no mapa")

cands = {}  # cpf -> (nasc, ano)  |  e lista nome+ibge
por_nome = {}  # (nome_norm, ibge) -> set de datas | None=conflito
tot = 0
for ano in ANOS:
    z = os.path.join(JOB, f"cand_{ano}.zip")
    if not os.path.exists(z) or os.path.getsize(z) < 1_000_000:
        log(f"baixando {ano} (zip nacional)…")
        rc = os.system(f'curl -sfL -A "Mozilla/5.0" -o "{z}" "{URL.format(ano=ano)}"')
        if rc != 0:
            log(f"ERRO no download {ano} (rc={rc})"); sys.exit(1)
    with zipfile.ZipFile(z) as zf:
        mg = [n for n in zf.namelist() if n.endswith("_MG.csv")]
        if not mg:
            log(f"{ano}: sem CSV _MG no zip ({zf.namelist()[:3]}…)"); continue
        nome_csv = mg[0]
        with zf.open(nome_csv) as f:
            rd = csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";")
            n_ano = 0
            for r in rd:
                nm = norm(r.get("NM_CANDIDATO", ""))
                dt = (r.get("DT_NASCIMENTO") or "").strip()
                cpf = re.sub(r"\D", "", r.get("NR_CPF_CANDIDATO") or "")
                mm = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", dt)
                if not mm or not nm:
                    continue
                iso = f"{mm.group(3)}-{mm.group(2)}-{mm.group(1)}"
                if not (1900 <= int(mm.group(3)) <= 2010):
                    continue
                n_ano += 1
                if len(cpf) == 11 and cpf != "00000000000":
                    cur = cands.get(cpf)
                    if cur is None or ano > cur[1]:
                        cands[cpf] = (iso, ano)
                ib = mun.get(norm(r.get("NM_UE", "")))  # 2022: UE=MG → sem município
                if ib:
                    k = (nm, ib)
                    s = por_nome.get(k)
                    if s is None:
                        por_nome[k] = {iso}
                    else:
                        s.add(iso)
            log(f"{ano}: {n_ano} candidaturas válidas")
            tot += n_ano

nome_uni = [(k[0], k[1], list(v)[0]) for k, v in por_nome.items() if len(v) == 1]
log(f"CPFs únicos c/ nascimento: {len(cands)} · nome+município únicos: {len(nome_uni)} (de {len(por_nome)})")

import psycopg2
conn = psycopg2.connect(DB); conn.autocommit = False
cur = conn.cursor(); cur.execute("set statement_timeout=0")

cur.execute("create temp table tse_cpf (cpf text primary key, nasc date, ano int)")
buf = io.StringIO()
for cpf, (iso, ano) in cands.items():
    buf.write(f"{cpf}\t{iso}\t{ano}\n")
buf.seek(0)
cur.copy_expert("copy tse_cpf from stdin", buf)

cur.execute("create temp table tse_nom (nome_norm text, ibge text, nasc date, primary key (nome_norm, ibge))")
buf = io.StringIO()
for nm, ib, iso in nome_uni:
    buf.write(f"{nm}\t{ib}\t{iso}\n")
buf.seek(0)
cur.copy_expert("copy tse_nom from stdin", buf)
log("temp tables carregadas")

t0 = time.time()
cur.execute("""
  update painel1_servidores p
     set data_nascimento = c.nasc, nasc_fonte = 'TSE:'||c.ano
    from tse_cpf c
   where p.cpf = c.cpf and p.data_nascimento is null""")
n_cpf = cur.rowcount
log(f"por CPF: {n_cpf} linhas em {time.time()-t0:.0f}s")

t0 = time.time()
cur.execute("""
  update painel1_servidores p
     set data_nascimento = c.nasc, nasc_fonte = 'TSE:nome'
    from tse_nom c
   where p.ibge = c.ibge
     and f_unaccent(upper(p.nome)) = c.nome_norm
     and p.data_nascimento is null""")
n_nom = cur.rowcount
log(f"por nome+município: {n_nom} linhas em {time.time()-t0:.0f}s")

conn.commit()
cur.execute("select count(*), count(distinct cpf) from painel1_servidores where data_nascimento is not null")
tot_pre, tot_cpfd = cur.fetchone()
log(f"TOTAL preenchido na base: {tot_pre} linhas ({tot_cpfd} CPFs distintos)")
conn.close()
log("CONCLUÍDO")
