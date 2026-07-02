#!/usr/bin/env python3
"""Retroalimentação do Painel 8 — Servidores do Poder Executivo do Estado de MG.

Auto-contido e IDEMPOTENTE: descobre os meses de <YEAR> na API CKAN do dados.mg.gov.br
(o datapackage.json fica cacheado e não lista meses novos, por isso usamos a API), baixa os
arquivos, consolida por `masp` (1 linha/pessoa; *_atual = último mês; *_periodo = distintos),
recarrega no Supabase (truncate + load via REST) e recomputa `no_painel1` (rpc). Se o último mês
disponível já é o carregado, sai sem fazer nada.

Fonte: dados.mg.gov.br (SEPLAG), dataset 31bd2c27-b64f-447b-95db-83d221874951.
Encoding real dos CSV = cp1252 (o datapackage diz utf-8). Sem CPF/remuneração.

Env obrigatórias: SUPABASE_URL, SUPABASE_KEY (service_role).
Opcionais: P8_DIR (pasta de trabalho/estado; default = pasta atual), P8_YEAR (default 2026).
Uso: python3 tools/retroalimentar_p8.py [--force]
"""
import os, sys, csv, json, re, time, urllib.request, urllib.error

DATASET = "31bd2c27-b64f-447b-95db-83d221874951"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_KEY", "")
YEAR = os.environ.get("P8_YEAR", "2026")
WORK = os.environ.get("P8_DIR", ".")
FORCE = "--force" in sys.argv
csv.field_size_limit(1 << 24)
TABLE = "servidores_estado_2026"
COLS = ["masp", "nome", "situacao_atual", "cargo_efetivo_atual", "comissao_atual",
        "funcao_gratif_atual", "carga_horaria", "sigla_lotacao_atual", "desc_lotacao_atual",
        "sigla_dotacao_atual", "desc_dotacao_atual", "data_inicio", "data_aposentadoria",
        "data_desligamento", "n_vinculos", "vinculos_adm", "cargos_efetivos_periodo",
        "comissoes_periodo", "funcoes_gratif_periodo", "orgaos_lotacao_periodo",
        "situacoes_periodo", "mudou_situacao", "n_meses", "primeiro_mes", "ultimo_mes", "presente_em"]
SEP = " | "
I = {"ano_mes": 0, "masp": 1, "adm": 2, "nome": 3, "sef": 4, "nef": 5, "cdcom": 6, "descom": 7,
     "cdfg": 8, "descfg": 9, "ch": 10, "cddot": 11, "sigdot": 12, "descdot": 13, "cdlot": 14,
     "siglot": 15, "desclot": 16, "sit": 17, "dini": 18, "dapos": 19, "ddesl": 20}


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def req(url, data=None, headers=None, method=None, timeout=600):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    r = urllib.request.Request(url, data=data, method=method, headers=h)
    return urllib.request.urlopen(r, timeout=timeout)


def sb(path, data=None, method="POST", prefer=None, timeout=120):
    h = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    if prefer:
        h["Prefer"] = prefer
    body = json.dumps(data).encode() if data is not None else None
    for t in range(4):
        try:
            with req(f"{URL}/rest/v1/{path}", data=body, headers=h, method=method, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if t == 3:
                raise RuntimeError(f"HTTP {e.code} em {path}: {e.read()[:300]}")
            time.sleep(2 * (t + 1))


def ckan_months():
    j = json.load(req(f"https://dados.mg.gov.br/api/3/action/package_show?id={DATASET}"))
    out = {}
    for r in j["result"]["resources"]:
        m = re.match(r"dados_serv_(\d{6})\.csv$", r.get("name") or "")
        if m and m.group(1).startswith(YEAR):
            out[m.group(1)] = r["url"]
    return dict(sorted(out.items()))


def download(month, url, path):
    for t in range(5):
        try:
            with req(url) as r, open(path, "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            if os.path.getsize(path) > 50_000_000:
                return
        except Exception as e:
            log(f"  {month} tentativa {t+1} falhou: {e}")
        time.sleep(4)
    raise RuntimeError(f"download {month} incompleto")


def consolidate(files, out):
    agg = {}
    for f in files:
        raw = open(f, "rb").read()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("cp1252")
        del raw
        rd = csv.reader(text.splitlines(), delimiter=";")
        next(rd)
        mi = int(re.search(r"(\d{6})", os.path.basename(f)).group(1))
        for row in rd:
            if len(row) < 21:
                continue
            masp = row[I["masp"]].strip()
            if not masp:
                continue
            a = agg.get(masp)
            if a is None:
                a = {"nome": "", "meses": set(), "adms": set(), "cef": set(), "com": set(),
                     "fg": set(), "lot": set(), "sit": set(), "lastm": 0, "atual": []}
                agg[masp] = a
            if row[I["nome"]].strip():
                a["nome"] = row[I["nome"]].strip()
            m6 = str(mi)
            a["meses"].add(m6)
            if row[I["adm"]].strip():
                a["adms"].add(row[I["adm"]].strip())
            nef, sef = row[I["nef"]].strip(), row[I["sef"]].strip()
            if nef:
                a["cef"].add((sef + " - " + nef) if sef else nef)
            if row[I["descom"]].strip():
                a["com"].add(row[I["descom"]].strip())
            if row[I["descfg"]].strip():
                a["fg"].add(row[I["descfg"]].strip())
            if row[I["siglot"]].strip():
                a["lot"].add(row[I["siglot"]].strip())
            if row[I["sit"]].strip():
                a["sit"].add(row[I["sit"]].strip())
            if mi > a["lastm"]:
                a["lastm"] = mi
                a["atual"] = [row]
            elif mi == a["lastm"]:
                a["atual"].append(row)
        del text

    def jd(rows, idx):
        seen = []
        for r in rows:
            v = r[idx].strip()
            if v and v not in seen:
                seen.append(v)
        return SEP.join(seen)

    def jcef(rows):
        seen = []
        for r in rows:
            nef, sef = r[I["nef"]].strip(), r[I["sef"]].strip()
            if not nef:
                continue
            v = (sef + " - " + nef) if sef else nef
            if v not in seen:
                seen.append(v)
        return SEP.join(seen)

    n = 0
    with open(out, "w", encoding="utf-8-sig", newline="") as g:
        w = csv.writer(g, delimiter=";")
        w.writerow(COLS)
        for masp, a in agg.items():
            at, ms = a["atual"], sorted(a["meses"])
            w.writerow([masp, a["nome"], jd(at, I["sit"]), jcef(at), jd(at, I["descom"]),
                jd(at, I["descfg"]), jd(at, I["ch"]), jd(at, I["siglot"]), jd(at, I["desclot"]),
                jd(at, I["sigdot"]), jd(at, I["descdot"]), jd(at, I["dini"]), jd(at, I["dapos"]),
                jd(at, I["ddesl"]), len(a["adms"]), SEP.join(sorted(a["adms"])),
                SEP.join(sorted(a["cef"])), SEP.join(sorted(a["com"])), SEP.join(sorted(a["fg"])),
                SEP.join(sorted(a["lot"])), SEP.join(sorted(a["sit"])),
                "Sim" if len(a["sit"]) > 1 else "Não", len(a["meses"]), ms[0], ms[-1], ",".join(ms)])
            n += 1
    return n


def load(csv_path):
    log("truncate servidores_estado_2026")
    sb("rpc/truncate_servidores_estado", data={}, prefer="return=minimal")
    buf, n = [], 0
    with open(csv_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            buf.append({c: (row.get(c) or None) for c in COLS})
            if len(buf) >= 1000:
                sb(TABLE, data=buf, prefer="return=minimal")
                n += len(buf); buf = []
                if n % 50000 == 0:
                    log(f"  {n} linhas")
    if buf:
        sb(TABLE, data=buf, prefer="return=minimal"); n += len(buf)
    log(f"carregadas {n} linhas; recomputando no_painel1…")
    sb("rpc/refresh_p8_no_painel1", data={}, prefer="return=minimal")
    return n


def main():
    if not URL or not KEY:
        sys.exit("defina SUPABASE_URL e SUPABASE_KEY")
    os.makedirs(os.path.join(WORK, "brutos"), exist_ok=True)
    statef = os.path.join(WORK, ".p8_last_month")
    last = open(statef).read().strip() if os.path.exists(statef) else ""
    months = ckan_months()
    if not months:
        sys.exit("nenhum recurso mensal encontrado na API CKAN")
    latest = max(months)
    log(f"CKAN: meses {min(months)}..{latest} ({len(months)}); último carregado: {last or '(nenhum)'}")
    if latest <= last and not FORCE:
        log("sem mês novo — nada a fazer.")
        return
    files = []
    for m, url in months.items():
        p = os.path.join(WORK, "brutos", f"dados_serv_{m}.csv")
        if not os.path.exists(p) or os.path.getsize(p) < 50_000_000:
            log(f"baixando {m}…")
            download(m, url, p)
        files.append(p)
    out = os.path.join(WORK, "consolidado_pessoa_2026.csv")
    log(f"consolidando {len(files)} meses por masp…")
    n = consolidate(files, out)
    log(f"consolidado: {n} pessoas -> {out}")
    load(out)
    open(statef, "w").write(latest)
    log(f"OK — Painel 8 retroalimentado até {latest}.")


if __name__ == "__main__":
    main()
