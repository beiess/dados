#!/usr/bin/env python3
"""Painel 11 — constrói pessoas_obras cruzando SICOM com os órgãos que contratam obra.

Duas fontes, só órgãos EXECUTIVOS de municípios que contratam obra (cod_ibge ∈ obras):
  A) painel6_responsaveis COM email  -> origem='Responsável'; setor = função(ões) no processo.
  B) painel1_servidores com cargo de ENGENHEIRO -> origem='Engenheiro'; setor = lotação real.
Agrupa por pessoa (nome+órgão+município); múltiplos emails saem separados por VÍRGULA; múltiplas
funções separadas por "; ". "Executivo" = exclui câmara/legislativo (unaccent). Idempotente
(truncate+insert). Env: SUPABASE_URL, SUPABASE_KEY (service_role).
"""
import os, sys, json, time, unicodedata, urllib.request, urllib.error

U = os.environ.get("SUPABASE_URL", "").rstrip("/")
K = os.environ.get("SUPABASE_KEY", "")
UA = "Mozilla/5.0 (pessoas-obras)"
DRY = "--dry" in sys.argv
BATCH = 1000


def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def sb(path, data=None, method="GET", prefer=None, timeout=120):
    h = {"apikey": K, "Authorization": f"Bearer {K}", "Content-Type": "application/json", "User-Agent": UA}
    if prefer: h["Prefer"] = prefer
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(f"{U}/rest/v1/{path}", data=body, method=method, headers=h)
    for t in range(4):
        try:
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                raw = resp.read()
                return json.loads(raw) if raw and method == "GET" else None
        except urllib.error.HTTPError as e:
            if t == 3: raise RuntimeError(f"HTTP {e.code} {path}: {e.read()[:200]}")
            time.sleep(2 * (t + 1))


def fetch_all(table, select, extra=""):
    out, off = [], 0
    while True:
        page = sb(f"{table}?select={select}{extra}&limit={BATCH}&offset={off}")
        out += page
        if len(page) < BATCH: break
        off += BATCH
    return out


def unac(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s or "")) if unicodedata.category(c) != "Mn").upper()


def is_executivo(orgao):
    """Exclui câmara/legislativo (o resto do universo SICOM é executivo/prefeitura/fundos)."""
    u = unac(orgao)
    return not ("CAMARA" in u or "LEGISLATIV" in u)


def emails_virgula(vals):
    """Distintos, na ordem de aparição, separados por vírgula."""
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
    """CPF do grupo: prefere o completo (11 dígitos) ao mascarado; senão o 1º não-vazio."""
    cheio = [v for v in vals if v and sum(c.isdigit() for c in str(v)) == 11]
    if cheio: return cheio[0]
    naovazio = [v for v in vals if v and str(v).strip()]
    return naovazio[0] if naovazio else None


def main():
    if not U or not K: sys.exit("defina SUPABASE_URL e SUPABASE_KEY (service_role)")
    coleta = time.strftime("%Y-%m-%d")
    log("lendo órgãos que contratam obra (cod_ibge)…")
    obras = fetch_all("obras_engenharia_orgaos", "cod_ibge,municipio")
    ibges = {o["cod_ibge"] for o in obras if o.get("cod_ibge")}
    muni_de = {o["cod_ibge"]: o.get("municipio") for o in obras if o.get("cod_ibge")}
    log(f"  {len(ibges)} municípios com obra")

    rows = []
    # ---- A) Responsáveis (executivo, com email) ----
    log("lendo responsáveis com email (painel6)…")
    resp = fetch_all("painel6_responsaveis", "nome,cpf,orgao,tipo_responsabilidade,email,cod_ibge", "&email=not.is.null")
    log(f"  {len(resp)} responsáveis com email (total MG); filtrando p/ executivo ∩ obra…")
    grpA = {}
    for r in resp:
        ib = r.get("cod_ibge")
        if ib not in ibges or not is_executivo(r.get("orgao")): continue
        key = (ib, (r.get("orgao") or "").strip(), unac(r.get("nome")))
        g = grpA.setdefault(key, {"nome": r.get("nome"), "orgao": r.get("orgao"), "cod_ibge": ib,
                                  "tipos": [], "emails": [], "cpfs": []})
        g["tipos"].append(r.get("tipo_responsabilidade")); g["emails"].append(r.get("email")); g["cpfs"].append(r.get("cpf"))
    for g in grpA.values():
        rows.append({"nome": g["nome"], "cpf": melhor_cpf(g["cpfs"]), "setor": juntar(g["tipos"]),
                     "email": emails_virgula(g["emails"]),
                     "orgao": g["orgao"], "municipio": muni_de.get(g["cod_ibge"]), "cod_ibge": g["cod_ibge"],
                     "origem": "Responsável", "data_coleta": coleta, "grau_confianca": "B"})
    log(f"  -> {len(rows)} responsáveis (executivo, agrupados por pessoa)")

    # ---- B) Engenheiros (servidores) ----
    log("lendo servidores com cargo de ENGENHEIRO (painel1)…")
    eng = fetch_all("painel1_servidores", "nome,cpf,orgao,setor,cargo_funcao,email,ibge",
                    "&cargo_funcao=ilike.*engenheir*")
    log(f"  {len(eng)} servidores engenheiros (total MG); filtrando p/ municípios com obra…")
    grpB = {}
    n0 = len(rows)
    for r in eng:
        ib = r.get("ibge")
        if ib not in ibges: continue
        key = (ib, (r.get("orgao") or "").strip(), unac(r.get("nome")))
        g = grpB.setdefault(key, {"nome": r.get("nome"), "orgao": r.get("orgao"), "cod_ibge": ib,
                                  "setores": [], "cargos": [], "emails": [], "cpfs": []})
        g["setores"].append(r.get("setor")); g["cargos"].append(r.get("cargo_funcao"))
        g["emails"].append(r.get("email")); g["cpfs"].append(r.get("cpf"))
    for g in grpB.values():
        setor = juntar(g["setores"]) or juntar(g["cargos"])
        rows.append({"nome": g["nome"], "cpf": melhor_cpf(g["cpfs"]), "setor": setor,
                     "email": emails_virgula(g["emails"]),
                     "orgao": g["orgao"], "municipio": muni_de.get(g["cod_ibge"]), "cod_ibge": g["cod_ibge"],
                     "origem": "Engenheiro", "data_coleta": coleta, "grau_confianca": "B"})
    log(f"  -> {len(rows) - n0} engenheiros (agrupados por pessoa)")

    com_email = sum(1 for r in rows if r.get("email"))
    log(f"TOTAL pessoas_obras: {len(rows)} · com email: {com_email} ({100*com_email/max(1,len(rows)):.0f}%)")
    if DRY:
        for r in rows[:6]: log(f"  ex: {r['origem']} | {r['nome']} | {r['setor']} | {r['email']}")
        return
    log("truncate + carga…")
    sb("rpc/truncate_pessoas_obras", data={}, method="POST", prefer="return=minimal")
    for i in range(0, len(rows), BATCH):
        sb("pessoas_obras", data=rows[i:i+BATCH], method="POST", prefer="return=minimal")
    log(f"OK — {len(rows)} pessoas carregadas.")


if __name__ == "__main__":
    main()
