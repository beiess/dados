#!/usr/bin/env python3
"""Painel 7 NACIONAL — recarrega obras_engenharia_orgaos/_unidades a partir dos 27
out/obras_<UF>.json (Fase 2, c/ Pregão). Merge por CNPJ (órgão federal aparece em várias
UFs): sede = linha cuja UF == UF da RFB (senão a de mais obras); agregados somados/unidos;
ufs_obras guarda onde publicou. Outliers (valor > R$5 bi = erro de fonte PNCP) → valor NULL,
bruto preservado em valor_alerta. Enriquecimento determinístico por CNPJ: email/site/telefone
de cadastro_institucional (MG, curado) e cadastro_institucional_br (27 UFs).
Truncate+COPY em UMA transação (psycopg2). Credencial: env P1_DB_URL. Uso: [--dry]"""
import glob, io, json, os, re, sys, time, unicodedata, psycopg2

JOB = os.path.dirname(os.path.abspath(__file__))
DB = os.environ["P1_DB_URL"]
DRY = "--dry" in sys.argv
LIMIAR = 5e9

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)
def dig(s): return re.sub(r"\D", "", str(s or ""))

def emails_virgula(*vals):
    seen, out = set(), []
    for v in vals:
        for part in str(v or "").replace("|", ";").replace(",", ";").split(";"):
            e = part.strip()
            if "@" in e and e.lower() not in seen: seen.add(e.lower()); out.append(e)
    return ", ".join(out) or None

def setoriais_virgula(s):
    if not s: return None
    partes = [p.strip() for p in str(s).split("|") if "@" in p]
    return ", ".join(partes) or None

# ---------- 1) ler e mesclar por CNPJ ----------
orgs = {}   # cnpj -> dict mesclado
files = sorted(glob.glob(os.path.join(JOB, "out", "obras_??.json")))
assert len(files) == 27, f"esperava 27 JSONs, achei {len(files)}"
for f in files:
    doc = json.load(open(f, encoding="utf-8"))
    coleta = (doc.get("meta", {}).get("geradoEm") or "")[:10]
    for uf, U in doc["ufs"].items():
        for ibge, M in U["municipios"].items():
            for cnpj, O in M["orgaos"].items():
                r = O.get("rfb") or {}
                setores = {str(cu): s for cu, s in (O.get("setores") or {}).items()}
                linha = {"uf": uf, "uf_nome": U.get("nome"), "municipio": M.get("nome"), "cod_ibge": ibge,
                         "n_obras": O.get("nObras") or 0, "valor": O.get("valorObras") or 0,
                         "modalidades": O.get("modalidades") or [], "primeira": O.get("primeiraObra"),
                         "ultima": O.get("ultimaObra"), "exemplos": O.get("exemplos") or [],
                         "setores": setores, "coleta": coleta}
                g = orgs.setdefault(cnpj, {"cnpj": cnpj, "razao_social": O.get("razaoSocial"),
                                           "nome_fantasia": O.get("nomeFantasia"), "poder": O.get("poder"),
                                           "esfera": O.get("esfera"), "rfb": r, "linhas": []})
                if not g["rfb"] and r: g["rfb"] = r
                g["linhas"].append(linha)

rows_org, rows_uni, n_multi, n_outl = [], [], 0, 0
for cnpj, g in orgs.items():
    L = g["linhas"]; r = g["rfb"]
    if len(L) > 1:
        n_multi += 1
        casa = [l for l in L if l["uf"] == (r.get("uf") or "").upper()]
        sede = casa[0] if casa else max(L, key=lambda l: l["n_obras"])
    else:
        sede = L[0]
    n_obras = sum(l["n_obras"] for l in L)
    valor = round(sum(l["valor"] for l in L), 2)
    mods = []; [mods.append(m) for l in L for m in l["modalidades"] if m and m not in mods]
    exs = []; [exs.append(e) for l in L for e in l["exemplos"] if e and e not in exs]
    setores = {}
    for l in L:
        for cu, s in l["setores"].items():
            if cu in setores:   # mesmo setor em 2 UFs (não esperado) → soma
                setores[cu]["nObras"] = (setores[cu].get("nObras") or 0) + (s.get("nObras") or 0)
                setores[cu]["valorObras"] = (setores[cu].get("valorObras") or 0) + (s.get("valorObras") or 0)
                setores[cu]["ultimaObra"] = max(setores[cu].get("ultimaObra") or "", s.get("ultimaObra") or "") or None
            else:
                setores[cu] = dict(s)
    ufs = sorted({l["uf"] for l in L})
    valor_alerta = None
    if valor > LIMIAR:
        n_outl += 1
        valor_alerta = f"PNCP: R$ {valor:,.2f} desconsiderado (> R$ 5 bi, inconsistente na fonte)"
        valor = None
    nomes_set = [s.get("nomeUnidade") for s in setores.values() if s.get("nomeUnidade")]
    rows_org.append({
        "cnpj": cnpj, "razao_social": g["razao_social"], "nome_fantasia": g["nome_fantasia"],
        "poder": g["poder"], "esfera": g["esfera"], "natureza_juridica": r.get("naturezaJuridica"),
        "uf": sede["uf"], "uf_nome": sede["uf_nome"], "municipio": sede["municipio"], "cod_ibge": sede["cod_ibge"],
        "n_obras": n_obras, "n_setores_obras": len(setores), "valor_estimado_obras": valor,
        "modalidades_obras": "; ".join(mods) or None,
        "primeira_obra": min((l["primeira"] for l in L if l["primeira"]), default=None),
        "ultima_obra": max((l["ultima"] for l in L if l["ultima"]), default=None),
        "exemplos_objeto": " | ".join(exs[:3]) or None, "setores_obras": "; ".join(nomes_set) or None,
        "email": None, "telefone": r.get("telefone") or None, "situacao_cadastral": r.get("situacao"),
        "logradouro": r.get("logradouro"), "bairro": r.get("bairro"), "cep": r.get("cep"), "site": None,
        "data_coleta": max(l["coleta"] for l in L), "grau_confianca": "B", "emails_setoriais": None,
        "ufs_obras": "; ".join(ufs), "n_ufs_obras": len(ufs), "valor_alerta": valor_alerta,
    })
    for cu, s in setores.items():
        rows_uni.append({"cnpj": cnpj, "codigo_unidade": cu, "nome_unidade": s.get("nomeUnidade"),
                         "uf": s.get("ufSigla") or sede["uf"], "municipio": s.get("municipioNome") or sede["municipio"],
                         "cod_ibge": s.get("codigoIbge") or sede["cod_ibge"], "n_obras": s.get("nObras") or 0,
                         "valor_estimado_obras": round(s.get("valorObras") or 0, 2) or None,
                         "ultima_obra": s.get("ultimaObra")})
log(f"mesclado: {len(rows_org)} órgãos (de {sum(len(g['linhas']) for g in orgs.values())} linhas UF) · "
    f"{n_multi} multi-UF · {len(rows_uni)} setores · {n_outl} outliers > R$5 bi")

# ---------- 2) enriquecimento por CNPJ (cadastros MG + BR) ----------
conn = psycopg2.connect(DB, connect_timeout=20); conn.autocommit = False
cur = conn.cursor(); cur.execute("set statement_timeout=0")
cur.execute("select cnpj,email,emails_setoriais,contato,site_oficial from cadastro_institucional where cnpj is not null")
cad_mg = {}
for c, em, es, ct, si in cur.fetchall():
    k = dig(c)
    if len(k) == 14: cad_mg.setdefault(k, (em, es, ct, si))
cur.execute("select cnpj,email,telefone,site from cadastro_institucional_br where cnpj is not null")
cad_br = {}
for c, em, tl, si in cur.fetchall():
    k = dig(c)
    if len(k) == 14: cad_br.setdefault(k, (em, tl, si))
n_em = n_es = n_tl = n_si = 0
for o in rows_org:
    mg = cad_mg.get(o["cnpj"]); br = cad_br.get(o["cnpj"])
    em = emails_virgula(mg[0] if mg else None, br[0] if br else None)
    if em: o["email"] = em; n_em += 1
    es = setoriais_virgula(mg[1]) if mg else None
    if es: o["emails_setoriais"] = es; n_es += 1
    if not o["telefone"]:
        tl = (str(mg[2]).split("|")[0].strip() if mg and mg[2] else None) or (br[1] if br else None)
        if tl: o["telefone"] = tl; n_tl += 1
    si = (mg[3] if mg else None) or (br[2] if br else None)
    if si: o["site"] = si; n_si += 1
tot = len(rows_org)
log(f"enriquecido: email {n_em} ({100*n_em//tot}%) · emails_setoriais {n_es} · telefone +{n_tl} "
    f"(total {sum(1 for o in rows_org if o['telefone'])}, {100*sum(1 for o in rows_org if o['telefone'])//tot}%) · site {n_si}")
por_uf = {}
for o in rows_org: por_uf[o["uf"]] = por_uf.get(o["uf"], 0) + 1
log("por UF (sede): " + ", ".join(f"{k}:{v}" for k, v in sorted(por_uf.items())))
log(f"valor total limpo: R$ {sum(o['valor_estimado_obras'] or 0 for o in rows_org)/1e9:,.1f} bi · n_obras {sum(o['n_obras'] for o in rows_org)}")
if DRY:
    log("DRY — nada gravado"); sys.exit(0)

# ---------- 3) DDL aditivo + truncate + COPY (1 transação) ----------
cur.execute("""alter table obras_engenharia_orgaos
                 add column if not exists ufs_obras text,
                 add column if not exists n_ufs_obras int,
                 add column if not exists valor_alerta text""")
cur.execute("truncate obras_engenharia_unidades, obras_engenharia_orgaos restart identity")
def cl(x): return "\\N" if x is None else str(x).replace("\\", " ").replace("\t", " ").replace("\n", " ").replace("\r", " ")
COLS_O = ["cnpj","razao_social","nome_fantasia","poder","esfera","natureza_juridica","uf","uf_nome","municipio","cod_ibge",
          "n_obras","n_setores_obras","valor_estimado_obras","modalidades_obras","primeira_obra","ultima_obra",
          "exemplos_objeto","setores_obras","email","telefone","situacao_cadastral","logradouro","bairro","cep","site",
          "data_coleta","grau_confianca","emails_setoriais","ufs_obras","n_ufs_obras","valor_alerta"]
COLS_U = ["cnpj","codigo_unidade","nome_unidade","uf","municipio","cod_ibge","n_obras","valor_estimado_obras","ultima_obra"]
buf = io.StringIO(); [buf.write("\t".join(cl(o[c]) for c in COLS_O) + "\n") for o in rows_org]; buf.seek(0)
cur.copy_expert(f"copy obras_engenharia_orgaos ({','.join(COLS_O)}) from stdin with (format text, null '\\N')", buf)
buf = io.StringIO(); [buf.write("\t".join(cl(u[c]) for c in COLS_U) + "\n") for u in rows_uni]; buf.seek(0)
cur.copy_expert(f"copy obras_engenharia_unidades ({','.join(COLS_U)}) from stdin with (format text, null '\\N')", buf)
cur.execute("select count(*), count(email), count(telefone), count(site), count(distinct uf), sum(n_obras), round(sum(valor_estimado_obras)/1e9,1) from obras_engenharia_orgaos")
a = cur.fetchone(); cur.execute("select count(*) from obras_engenharia_unidades"); b = cur.fetchone()[0]
assert a[0] == len(rows_org) and b == len(rows_uni), f"contagem divergente {a[0]}/{len(rows_org)} {b}/{len(rows_uni)}"
conn.commit()
cur.execute("analyze obras_engenharia_orgaos"); cur.execute("analyze obras_engenharia_unidades"); conn.commit()
log(f"GRAVADO: órgãos {a[0]} (email {a[1]}, tel {a[2]}, site {a[3]}, {a[4]} UFs, n_obras {a[5]}, R$ {a[6]} bi) · setores {b}")
conn.close()
