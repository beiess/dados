#!/usr/bin/env python3
"""Painel 11 (pessoas_obras) — rebuild MG com a NOVA base de obras (c/ Pregão).
Fonte A: painel6_responsaveis (executivo, com email) · Fonte B: painel1_servidores
engenheiros. Só municípios com obra (do out/obras_MG.json). Agrupa por pessoa
(nome+órgão+município); emails por vírgula; funções por '; '. Truncate+insert (MG-only)."""
import io, json, os, time, unicodedata, psycopg2

JOB = os.path.dirname(os.path.abspath(__file__))
import os
DB = os.environ["SUPABASE_DB_URL"]  # exporte de TCEMG/dados-painel/.supabase_env

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)
def unac(s): return "".join(c for c in unicodedata.normalize("NFD", str(s or "")) if unicodedata.category(c) != "Mn").upper()
def is_exec(o): u = unac(o); return not ("CAMARA" in u or "LEGISLATIV" in u)

def emails_virgula(vals):
    seen, out = set(), []
    for v in vals:
        for part in str(v or "").replace("|", ";").replace(",", ";").split(";"):
            e = part.strip()
            if "@" in e and e.lower() not in seen:
                seen.add(e.lower()); out.append(e)
    return ", ".join(out) or None

def juntar(vals, sep="; "):
    seen, out = set(), []
    for v in vals:
        v = (v or "").strip()
        if v and v.upper() not in seen:
            seen.add(v.upper()); out.append(v)
    return sep.join(out) or None

def melhor_cpf(vals):
    cheio = [v for v in vals if v and sum(c.isdigit() for c in str(v)) == 11]
    if cheio: return cheio[0]
    nv = [v for v in vals if v and str(v).strip()]
    return nv[0] if nv else None

ibmap = json.load(open(os.path.join(JOB, "mg_ibges.json")))
ibges = list(ibmap.keys())
coleta = time.strftime("%Y-%m-%d")
conn = psycopg2.connect(DB, connect_timeout=15); conn.autocommit = False
cur = conn.cursor(); cur.execute("set statement_timeout=0")

# A) responsáveis (executivo, com email)
log("lendo responsáveis (painel6)…")
cur.execute("""select nome,cpf,orgao,tipo_responsabilidade,email,cod_ibge
               from painel6_responsaveis where email is not null and cod_ibge = any(%s)""", (ibges,))
grpA = {}
for nome, cpf, orgao, tipo, email, ib in cur.fetchall():
    if not is_exec(orgao): continue
    key = (ib, (orgao or "").strip(), unac(nome))
    g = grpA.setdefault(key, {"nome": nome, "orgao": orgao, "ib": ib, "tipos": [], "emails": [], "cpfs": []})
    g["tipos"].append(tipo); g["emails"].append(email); g["cpfs"].append(cpf)
log(f"  responsáveis agrupados por pessoa: {len(grpA)}")

# B) engenheiros (painel1)
log("lendo engenheiros (painel1)…")
cur.execute("""select nome,cpf,orgao,setor,cargo_funcao,email,ibge
               from painel1_servidores where ibge = any(%s) and cargo_funcao ilike '%%engenheir%%'""", (ibges,))
grpB = {}
for nome, cpf, orgao, setor, cargo, email, ib in cur.fetchall():
    key = (ib, (orgao or "").strip(), unac(nome))
    g = grpB.setdefault(key, {"nome": nome, "orgao": orgao, "ib": ib, "setores": [], "cargos": [], "emails": [], "cpfs": []})
    g["setores"].append(setor); g["cargos"].append(cargo); g["emails"].append(email); g["cpfs"].append(cpf)
log(f"  engenheiros agrupados por pessoa: {len(grpB)}")

rows = []
for g in grpA.values():
    rows.append((g["nome"], melhor_cpf(g["cpfs"]), juntar(g["tipos"]), emails_virgula(g["emails"]),
                 g["orgao"], ibmap.get(g["ib"]), g["ib"], "Responsável", "PNCP+SICOM", coleta, "B"))
for g in grpB.values():
    setor = juntar(g["setores"]) or juntar(g["cargos"])
    rows.append((g["nome"], melhor_cpf(g["cpfs"]), setor, emails_virgula(g["emails"]),
                 g["orgao"], ibmap.get(g["ib"]), g["ib"], "Engenheiro", "PNCP+Painel1", coleta, "B"))

com_email = sum(1 for r in rows if r[3])
log(f"TOTAL pessoas_obras MG: {len(rows)} · com email: {com_email} ({100*com_email//max(1,len(rows))}%)")

# truncate + COPY (pessoas_obras hoje é 100% MG)
cur.execute("truncate pessoas_obras")
buf = io.StringIO()
def cl(x): return "" if x is None else str(x).replace("\t", " ").replace("\n", " ").replace("\\", " ")
for r in rows:
    buf.write("\t".join(cl(x) if x is not None else "\\N" for x in r) + "\n")
buf.seek(0)
cur.copy_expert("copy pessoas_obras (nome,cpf,setor,email,orgao,municipio,cod_ibge,origem,fonte_tipo,data_coleta,grau_confianca) from stdin with (format text, null '\\N')", buf)
conn.commit()
cur.execute("select count(*), count(*) filter (where email is not null and email<>''), count(distinct cod_ibge) from pessoas_obras")
t, e, m = cur.fetchone()
log(f"GRAVADO: {t} pessoas · {e} com email · {m} municípios")
conn.close()
