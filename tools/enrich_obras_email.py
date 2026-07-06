#!/usr/bin/env python3
"""Enriquece obras_engenharia_orgaos.email cruzando por CNPJ com cadastro_institucional (Painel 2),
que tem emails institucionais curados de MG (prefeitura@…mg.gov.br, ouvidoria, setoriais).

Motivo: a RFB (minhareceita/BrasilAPI) NÃO retorna email de órgão público (0%). O email real
institucional já existe no cadastro do Painel 2 — este passo o traz por CNPJ (join determinístico,
grau_confiança preservado). Também copia telefone institucional (contato) quando o da RFB veio vazio.

Idempotente: pode rodar quantas vezes quiser (PATCH por CNPJ). Roda após load_obras_engenharia.py.
Env: SUPABASE_URL, SUPABASE_KEY (service_role).
"""
import os, sys, json, time, urllib.request, urllib.error

U = os.environ.get("SUPABASE_URL", "").rstrip("/")
K = os.environ.get("SUPABASE_KEY", "")
UA = "Mozilla/5.0 (obras-enrich)"
DRY = "--dry" in sys.argv


def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def sb(path, data=None, method="GET", prefer=None, timeout=90):
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
        page = sb(f"{table}?select={select}{extra}&limit=1000&offset={off}")
        out += page
        if len(page) < 1000: break
        off += 1000
    return out


def first_email(s):
    """primeiro email de um campo 'a@x | b@y' (o principal do órgão)."""
    if not s: return None
    for part in str(s).split("|"):
        p = part.strip()
        if "@" in p: return p
    return None


def main():
    if not U or not K: sys.exit("defina SUPABASE_URL e SUPABASE_KEY (service_role)")
    log("lendo cadastro_institucional (emails curados)…")
    cad = {c["cnpj"]: c for c in fetch_all("cadastro_institucional", "cnpj,email,emails_setoriais,contato",
                                           "&email=not.is.null") if c.get("cnpj")}
    log(f"  {len(cad)} CNPJs com email no cadastro")
    log("lendo obras_engenharia_orgaos…")
    obras = fetch_all("obras_engenharia_orgaos", "cnpj,email,telefone")
    log(f"  {len(obras)} órgãos-de-obra")
    n_mail, n_tel = 0, 0
    for o in obras:
        c = cad.get(o["cnpj"])
        if not c: continue
        patch = {}
        if not o.get("email"):
            em = first_email(c.get("email"))
            if em:
                patch["email"] = em
                n_mail += 1
        if not o.get("telefone") and c.get("contato"):
            tel = str(c["contato"]).split("|")[0].strip()
            if tel: patch["telefone"] = tel; n_tel += 1
        if patch and not DRY:
            sb(f"obras_engenharia_orgaos?cnpj=eq.{o['cnpj']}", data=patch, method="PATCH", prefer="return=minimal")
    log(f"OK — email preenchido em {n_mail} órgãos · telefone em +{n_tel}{' (DRY)' if DRY else ''}")
    log(f"cobertura de email agora: {sum(1 for o in obras if o.get('email')) + n_mail}/{len(obras)} "
        f"({100*(sum(1 for o in obras if o.get('email'))+n_mail)/len(obras):.0f}%)")


if __name__ == "__main__":
    main()
