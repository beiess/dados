#!/usr/bin/env python3
"""Cadastro Institucional Nacional — varre o PNCP e monta a cascata
UF -> Município -> Órgão(CNPJ) -> Unidades/Setores, enriquecendo por CNPJ na RFB.

Fonte primária (quem publicou): PNCP consulta `/v1/contratacoes/publicacao`
(dedup por CNPJ). Setores completos: `/api/pncp/v1/orgaos/{cnpj}/unidades`.
Enriquecimento: minhareceita.org (email/telefone/endereço/natureza) — cache resumível.

Idempotente/resumível: mantém cache JSON de CNPJs já enriquecidos; a varredura pode ser
repetida (dedup por CNPJ + datas min/max de publicação).

Uso:
  python3 tools/pncp_cadastro_nacional.py --inicio 20260601 --fim 20260603 \
      --modalidades 6,8 [--uf GO] [--max-paginas 5] [--sem-rfb] [--limit-orgaos 50]
Saídas em data_full/: cadastro_nacional.json (cascata) + cadastro_nacional.csv (achatado, 1 linha=órgão).
"""
import os, sys, csv, json, time, argparse, urllib.request, urllib.error
from datetime import date, timedelta

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
PNCP_CONSULTA = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
PNCP_UNIDADES = "https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/unidades"
RFB = "https://minhareceita.org/{cnpj}"
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
OUTDIR = os.path.join(BASE, "data_full")
CACHE = os.path.join(OUTDIR, ".rfb_cache.json")
STATE = os.path.join(OUTDIR, ".sweep_state.json")  # checkpoint da varredura (resumível)
PODER = {"L": "Legislativo", "E": "Executivo", "J": "Judiciário", "M": "Ministério Público"}
ESFERA = {"M": "Municipal", "E": "Estadual", "F": "Federal", "D": "Distrital"}


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


class NetErr(Exception):
    """Falha de rede/DNS persistente (distinta de resposta HTTP de erro)."""


def get(url, timeout=120, tries=8, raise_net=False):
    """Retorna JSON. HTTP 404 -> None. HTTP 4xx com corpo -> devolve o JSON de erro
    (ex.: {message,status}). Erro de REDE/DNS após as tentativas -> None, ou levanta
    NetErr se raise_net=True (usado na paginação p/ abortar de forma resumível)."""
    last = None
    r429 = 0
    for t in range(tries + 20):                   # folga extra p/ ondas de 429 (rate limit)
        try:
            r = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429:                     # rate limit: espera (Retry-After) e tenta de novo
                ra = e.headers.get("Retry-After")
                wait = int(ra) if (ra and str(ra).isdigit()) else min(90, 5 * (r429 + 1))
                r429 += 1
                if r429 <= 20:
                    time.sleep(wait)
                    continue                      # não conta como queda de rede
                last = e
                break
            try:
                return json.loads(e.read())       # corpo de erro da API (400 etc.) -> não é queda de rede
            except Exception:
                last = e
                break
        except Exception as e:                    # DNS/timeout/conn reset
            last = e
        if t - r429 >= tries - 1:                 # esgotou as tentativas de rede reais
            break
        time.sleep(min(60, 3 * (t - r429 + 1)))
    if raise_net:
        raise NetErr(f"{url[:90]}: {last}")
    log(f"  falha em {url[:80]}: {last}")
    return None


def _absorve(orgs, rec, mod):
    oe, un = rec.get("orgaoEntidade") or {}, rec.get("unidadeOrgao") or {}
    cnpj = (oe.get("cnpj") or "").strip()
    if not cnpj:
        return
    dt = (rec.get("dataPublicacaoPncp") or "")[:10]
    o = orgs.get(cnpj)
    if o is None:
        o = {"cnpj": cnpj, "razaoSocial": oe.get("razaoSocial"),
             "poderId": oe.get("poderId"), "esferaId": oe.get("esferaId"),
             "ufSigla": un.get("ufSigla"), "ufNome": un.get("ufNome"),
             "municipioNome": un.get("municipioNome"), "codigoIbge": un.get("codigoIbge"),
             "unidades": {}, "modalidades": [], "primeiraPub": dt, "ultimaPub": dt}
        orgs[cnpj] = o
    cu = un.get("codigoUnidade")
    if cu is not None:
        o["unidades"][str(cu)] = un.get("nomeUnidade")
    if mod not in o["modalidades"]:
        o["modalidades"].append(mod)
    if dt and (not o["primeiraPub"] or dt < o["primeiraPub"]):
        o["primeiraPub"] = dt
    if dt and dt > o["ultimaPub"]:
        o["ultimaPub"] = dt


def _save_state(orgs, ti, pagina):
    os.makedirs(OUTDIR, exist_ok=True)
    tmp = STATE + ".tmp"
    json.dump({"cursor": {"ti": ti, "pagina": pagina}, "orgs": orgs},
              open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, STATE)  # escrita atômica


def month_ranges(inicio, fim):
    """Fatia [inicio, fim] (yyyyMMdd) em janelas de mês-calendário — consultas menores,
    página 1 rápida, sem timeout nas modalidades gigantes."""
    y, m, d0 = int(inicio[:4]), int(inicio[4:6]), int(inicio[6:8])
    y1, m1, d1 = int(fim[:4]), int(fim[4:6]), int(fim[6:8])
    out = []
    while (y, m) <= (y1, m1):
        ini = date(y, m, d0) if (y, m) == (int(inicio[:4]), int(inicio[4:6])) else date(y, m, 1)
        nxt = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
        fimm = date(y1, m1, d1) if (y, m) == (y1, m1) else nxt - timedelta(days=1)
        out.append((ini.strftime("%Y%m%d"), fimm.strftime("%Y%m%d")))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def sweep(inicio, fim, modalidades, uf, max_paginas, resume):
    """Varre PNCP deduplicando por CNPJ. Tarefas = modalidade × mês (consultas pequenas).
    Checkpoint a cada 200 páginas; resumível pelo índice de tarefa (ti)."""
    meses = month_ranges(inicio, fim)
    tarefas = [(mod, mi, mf) for mod in modalidades for (mi, mf) in meses]
    orgs, start_ti, start_pag = {}, 0, 1
    if resume and os.path.exists(STATE):
        st = json.load(open(STATE, encoding="utf-8"))
        orgs = st["orgs"]
        cur = st.get("cursor", {})
        start_ti, start_pag = cur.get("ti", cur.get("mi", 0)), cur.get("pagina", 1)
        log(f"RESUME: {len(orgs)} órgãos, retomando tarefa idx {start_ti}/{len(tarefas)} pág {start_pag}")
    npag = 0
    for ti in range(start_ti, len(tarefas)):
        mod, di, df = tarefas[ti]
        pagina = start_pag if ti == start_ti else 1
        total_pag = None
        while True:
            url = (f"{PNCP_CONSULTA}?dataInicial={di}&dataFinal={df}"
                   f"&codigoModalidadeContratacao={mod}&pagina={pagina}&tamanhoPagina=50")
            if uf:
                url += f"&uf={uf}"
            try:
                d = get(url, raise_net=True)
            except NetErr as e:
                _save_state(orgs, ti, pagina)   # resumível exatamente daqui
                raise NetErr(f"modalidade {mod} {di}-{df} pág {pagina}: {e}")
            if not d or "data" not in d:
                break   # fim normal / janela sem resultados (não é queda de rede)
            if total_pag is None:
                total_pag = d.get("totalPaginas", 1)
                tot = d.get("totalRegistros", 0)
                if tot:
                    log(f"  mod {mod} {di[:6]}: {tot} reg / {total_pag} pág (órgãos: {len(orgs)})")
            for rec in d.get("data", []):
                _absorve(orgs, rec, mod)
            time.sleep(0.15)   # educado com o PNCP (evita 429)
            npag += 1
            if npag % 200 == 0:
                _save_state(orgs, ti, pagina)
                log(f"  checkpoint: {npag} pág varridas, {len(orgs)} órgãos distintos")
            pagina += 1
            if pagina > (total_pag or 1) or (max_paginas and pagina > max_paginas):
                break
        _save_state(orgs, ti + 1, 1)
    return orgs


def full_unidades(cnpj):
    """Lista completa de setores do órgão via PNCP."""
    d = get(PNCP_UNIDADES.format(cnpj=cnpj), timeout=40)
    out = {}
    for u in (d or []):
        out[str(u.get("codigoUnidade"))] = u.get("nomeUnidade")
    return out


def enrich_rfb(cnpj, cache):
    if cnpj in cache:
        return cache[cnpj]
    d = get(RFB.format(cnpj=cnpj), timeout=40)
    if not d:
        cache[cnpj] = None
        return None
    tel = (d.get("ddd_telefone_1") or "").strip() or (d.get("ddd_telefone_2") or "").strip()
    r = {"email": d.get("email") or None, "telefone": tel or None,
         "situacao": d.get("descricao_situacao_cadastral"),
         "naturezaJuridica": d.get("natureza_juridica"),
         "logradouro": " ".join(x for x in [d.get("logradouro"), d.get("numero")] if x) or None,
         "bairro": d.get("bairro"), "cep": d.get("cep"),
         "municipio": d.get("municipio"), "uf": d.get("uf"),
         "enteResponsavel": d.get("ente_federativo_responsavel")}
    cache[cnpj] = r
    return r


def build(orgs, args, cache):
    ufs = {}
    items = list(orgs.items())
    if args.limit_orgaos:
        items = items[:args.limit_orgaos]
    for i, (cnpj, o) in enumerate(items, 1):
        if not args.sem_setores:
            fu = full_unidades(cnpj)
            if fu:
                o["unidades"] = fu
        rfb = None if args.sem_rfb else enrich_rfb(cnpj, cache)
        uf = o["ufSigla"] or "??"
        muni = o["codigoIbge"] or "0"
        U = ufs.setdefault(uf, {"nome": o["ufNome"], "municipios": {}})
        M = U["municipios"].setdefault(muni, {"nome": o["municipioNome"], "orgaos": {}})
        M["orgaos"][cnpj] = {
            "razaoSocial": o["razaoSocial"],
            "poder": PODER.get(o["poderId"], o["poderId"]),
            "esfera": ESFERA.get(o["esferaId"], o["esferaId"]),
            "unidades": o["unidades"],
            "rfb": rfb, "site": None,
            "fontePNCP": {"publicou": True, "primeiraPublicacao": o["primeiraPub"],
                          "ultimaPublicacao": o["ultimaPub"], "nModalidades": len(o["modalidades"])},
        }
        if i % 25 == 0:
            log(f"  enriquecidos {i}/{len(items)} órgãos")
            _save_cache(cache)
    return ufs


def _save_cache(cache):
    os.makedirs(OUTDIR, exist_ok=True)
    json.dump(cache, open(CACHE, "w"), ensure_ascii=False)


def write_outputs(ufs):
    os.makedirs(OUTDIR, exist_ok=True)
    n_uf = len(ufs)
    n_muni = sum(len(u["municipios"]) for u in ufs.values())
    n_org = sum(len(m["orgaos"]) for u in ufs.values() for m in u["municipios"].values())
    n_uni = sum(len(o["unidades"]) for u in ufs.values() for m in u["municipios"].values()
                for o in m["orgaos"].values())
    doc = {"meta": {"geradoEm": time.strftime("%Y-%m-%d %H:%M:%S"), "fonte": "PNCP + RFB",
                    "ufs": n_uf, "municipios": n_muni, "orgaos": n_org, "unidades": n_uni}, "ufs": ufs}
    jpath = os.path.join(OUTDIR, "cadastro_nacional.json")
    json.dump(doc, open(jpath, "w", encoding="utf-8"), ensure_ascii=False)
    cpath = os.path.join(OUTDIR, "cadastro_nacional.csv")
    with open(cpath, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["uf", "municipio", "codigo_ibge", "cnpj", "razao_social", "poder", "esfera",
                    "n_setores", "email", "telefone", "situacao", "natureza_juridica", "site",
                    "primeira_pub", "ultima_pub"])
        for uf, U in sorted(ufs.items()):
            for ibge, M in U["municipios"].items():
                for cnpj, o in M["orgaos"].items():
                    r = o.get("rfb") or {}
                    w.writerow([uf, M["nome"], ibge, cnpj, o["razaoSocial"], o["poder"], o["esfera"],
                                len(o["unidades"]), r.get("email"), r.get("telefone"), r.get("situacao"),
                                r.get("naturezaJuridica"), o["site"],
                                o["fontePNCP"]["primeiraPublicacao"], o["fontePNCP"]["ultimaPublicacao"]])
    log(f"OK — {n_uf} UF · {n_muni} municípios · {n_org} órgãos · {n_uni} setores")
    log(f"  -> {jpath}")
    log(f"  -> {cpath}")
    return doc["meta"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", required=True, help="yyyyMMdd")
    ap.add_argument("--fim", required=True, help="yyyyMMdd")
    ap.add_argument("--modalidades", default="6,8", help="csv de códigos (default 6,8)")
    ap.add_argument("--uf", default=None, help="filtrar por UF (opcional)")
    ap.add_argument("--max-paginas", type=int, default=0, help="cap de páginas/modalidade (0=todas)")
    ap.add_argument("--limit-orgaos", type=int, default=0, help="cap de órgãos a enriquecer (0=todos)")
    ap.add_argument("--sem-rfb", action="store_true", help="não enriquecer na RFB")
    ap.add_argument("--sem-setores", action="store_true", help="não buscar setores completos no PNCP")
    ap.add_argument("--resume", action="store_true", help="retomar de checkpoint (.sweep_state.json)")
    args = ap.parse_args()
    mods = [int(x) for x in args.modalidades.split(",") if x.strip()]
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    log(f"varrendo PNCP {args.inicio}..{args.fim} modalidades={mods} uf={args.uf or 'todas'}")
    try:
        orgs = sweep(args.inicio, args.fim, mods, args.uf, args.max_paginas, args.resume)
    except NetErr as e:
        log(f"QUEDA DE REDE — checkpoint salvo; rode de novo com --resume. ({e})")
        sys.exit(1)
    log(f"publicadores distintos (CNPJ): {len(orgs)}")
    ufs = build(orgs, args, cache)
    _save_cache(cache)
    write_outputs(ufs)


if __name__ == "__main__":
    main()
