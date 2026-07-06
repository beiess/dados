#!/usr/bin/env python3
"""Painel 7 — Obras e Serviços de Engenharia. Varre o PNCP, classifica cada contratação
como obra/serviço de engenharia (heurística por objetoCompra) e monta a cascata
UF -> Município -> Órgão(CNPJ) -> Setores que contratam obra, enriquecendo por CNPJ na RFB.

Só entram na base os ÓRGÃOS que publicaram >=1 contratação classificada como obra/engenharia.
O grão é o órgão/setor (lead B2G): "quem demanda obra + como contatar (email/tel/site)".

Classificação (transparente e auditável): léxico POS de obra/engenharia sobre `objetoCompra`,
com NEG mínimo e específico p/ confusáveis (reforma agrária, obra literária, compra pura de
material). O PNCP NÃO expõe categoria de obra na consulta pública (item vem "Não se aplica"),
por isso o recorte é heurístico -> grau_confianca='B'. Cada órgão guarda exemplos de objeto
(evidência) e a data de coleta.

Fonte primária (quem publicou): PNCP consulta `/v1/contratacoes/publicacao` (dedup por CNPJ).
Enriquecimento: minhareceita.org (email/telefone/endereço/natureza) — cache resumível.
Idempotente/resumível: checkpoint da varredura + cache de CNPJs enriquecidos.

Uso:
  python3 tools/pncp_obras_engenharia.py --inicio 20260101 --fim 20260706 \
      --modalidades 1,2,4,5,6,7,8,9,12 [--uf MG] [--max-paginas N] [--sem-rfb] [--limit-orgaos N] [--resume]
Saídas em data_full/: obras_engenharia.json (cascata) + obras_engenharia.csv (achatado, 1 linha=órgão).
"""
import os, sys, csv, json, re, time, argparse, urllib.request, urllib.error

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
PNCP_CONSULTA = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
PNCP_UNIDADES = "https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/unidades"
RFB = "https://minhareceita.org/{cnpj}"
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
OUTDIR = os.path.join(BASE, "data_full")
CACHE = os.path.join(OUTDIR, ".rfb_cache.json")                 # compartilhado com o P2N (mesma RFB)
STATE = os.path.join(OUTDIR, ".sweep_obras_state.json")         # checkpoint próprio (resumível)
PODER = {"L": "Legislativo", "E": "Executivo", "J": "Judiciário", "M": "Ministério Público", "N": "Não informado"}
ESFERA = {"M": "Municipal", "E": "Estadual", "F": "Federal", "D": "Distrital", "N": "Não informado"}
MODAL_NOME = {1: "Leilão-eletrônico", 2: "Diálogo competitivo", 3: "Concurso",
              4: "Concorrência-eletrônica", 5: "Concorrência-presencial", 6: "Pregão-eletrônico",
              7: "Pregão-presencial", 8: "Dispensa", 9: "Inexigibilidade", 12: "Credenciamento",
              13: "Leilão-presencial"}

# ---- Classificador de OBRA / SERVIÇO DE ENGENHARIA (heurística sobre objetoCompra) ----
# Estratégia em 3 camadas (precisão > recall, regra "não inventar/não confundir" do CLAUDE.md):
#   NEG    -> confusáveis (insumo agrícola, merenda, material escolar...) => NÃO é obra.
#   STRONG -> termo inequívoco de obra/engenharia (basta 1) => é obra.
#   STRUCT + BUILDV -> substantivo estrutural (escola, ponte, estrada, quadra...) SÓ conta como
#             obra se houver também um VERBO de construção/execução no mesmo objeto (evita
#             "merenda escolar", "transporte escolar", "herbicida em estradas vicinais" etc.).
STRONG = re.compile(
    r"\b(obra|obras|constru[cç]|reconstru[cç]|pavimenta[cç]|recapeament|repavimenta|terraplen|"
    r"drenagem|cal[cç]ament|edifica[cç]|empreitada|adutora|barragem|a[cç]ude|"
    r"muro de (arrimo|conten[cç])|galeria (pluvial|de [aá]guas)|meio-?fio|sarjeta|esgotament|"
    r"infraestrutura|urbaniza[cç]|reforma predial|restaura[cç][aã]o predial|manuten[cç][aã]o predial|"
    r"servi[cç]os? (comuns )?de engenharia|obra de engenharia|projeto (b[aá]sico|executivo) de engenharia|"
    r"perfura[cç][aã]o de po[cç]o|revitaliza[cç]|requalifica[cç]|"
    # estruturas de engenharia civil (inerentemente obra, independem de verbo):
    r"ponte(?! rolante)|passarela|viaduto|pontilh[aã]o|bueiro|tubul[aã]o|encabe[cç]ament|"
    r"po[cç]o (artesiano|tubular)|esta[cç][aã]o elevat[oó]ria)",
    re.IGNORECASE)
ENG = re.compile(r"\bengenharia\b", re.IGNORECASE)          # "engenharia" sozinho já é forte sinal
STRUCT = re.compile(
    r"\b(escola|creche|posto de sa[uú]de|unidade b[aá]sica|ubs|hospital|pra[cç]a|cemit[eé]rio|"
    r"quadra|gin[aá]sio|est[aá]dio|ginasio|galp[aã]o|pavilh[aã]o|mercado municipal|"
    r"rodovi|estrada|via p[uú]blica|vias urbanas|cal[cç]ada|"
    r"sistema de abastecimento de [aá]gua|abastecimento de [aá]gua|rede de (esgoto|[aá]gua|drenagem)|"
    r"ilumina[cç][aã]o p[uú]blica|telhado|cobertura|pr[eé]dio|edif[ií]cio)",
    re.IGNORECASE)
BUILDV = re.compile(
    r"\b(constru|reconstru|reforma|amplia[cç]|repar|restaura|revitaliza|requalifica|recupera[cç]|"
    r"implanta[cç]|execu[cç][aã]o|edifica[cç]|adequa[cç]|melhoramento|instala[cç][aã]o de|"
    r"pavimenta[cç]|cobertura de|substitui[cç][aã]o de (telhado|cobertura))",
    re.IGNORECASE)
NEG = re.compile(
    r"(reforma agr[aá]ria|obra liter[aá]ria|obras? de arte (liter|do acervo)|acervo bibliogr|"
    r"aquisi[cç][aã]o de material de constru[cç][aã]o|"          # compra pura de material, sem execução
    r"material escolar|obras? did[aá]ticas?|merenda|transporte escolar|"
    r"herbicida|defensivo|agrot[oó]xico|insumo agr[ií]cola|calc[aá]rio agr|adubo|fertilizante|"
    r"semente|muda de|g[eê]nero aliment|medicament|combust[ií]vel)",
    re.IGNORECASE)


def eh_obra(objeto):
    """True se o objeto é obra/serviço de engenharia (heurística textual em 3 camadas)."""
    o = objeto or ""
    if NEG.search(o):
        return False
    if STRONG.search(o) or ENG.search(o):
        return True
    return bool(STRUCT.search(o) and BUILDV.search(o))


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


class NetErr(Exception):
    """Falha de rede/DNS persistente (distinta de resposta HTTP de erro)."""


THROTTLE = float(os.environ.get("PNCP_THROTTLE", "0.34"))  # s entre requisições (evita 429)


def get(url, timeout=90, tries=8, raise_net=False):
    """Retorna JSON. HTTP 404 -> None. HTTP 429/5xx -> backoff e retry (respeita Retry-After).
    HTTP 4xx não-retryable c/ corpo JSON -> devolve o erro. Queda de rede após as tentativas ->
    None, ou levanta NetErr se raise_net=True (paginação resumível)."""
    last = None
    time.sleep(THROTTLE)  # throttle educado ANTES de cada chamada
    for t in range(tries):
        try:
            r = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                body = resp.read()
                if not body or not body.strip():
                    return None          # 204/corpo vazio = "sem dados" (ex.: modalidade sem obra), não é erro
                return json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429 or e.code >= 500:      # rate limit / erro do servidor -> backoff e retry
                ra = e.headers.get("Retry-After")
                wait = int(ra) if (ra and ra.isdigit()) else min(90, 5 * (t + 1) ** 2)
                last = e
                time.sleep(wait)
                continue
            try:
                return json.loads(e.read())         # 400/403 etc. com corpo -> não é queda de rede
            except Exception:
                last = e
                break
        except Exception as e:                       # DNS/timeout/conn reset
            last = e
        time.sleep(min(60, 3 * (t + 1)))
    if raise_net:
        raise NetErr(f"{url[:90]}: {last}")
    log(f"  falha em {url[:80]}: {last}")
    return None


def _absorve(orgs, rec, mod):
    """Absorve UMA contratação já confirmada como obra. Agrega por órgão(cnpj) e por setor."""
    oe, un = rec.get("orgaoEntidade") or {}, rec.get("unidadeOrgao") or {}
    cnpj = (oe.get("cnpj") or "").strip()
    if not cnpj:
        return
    dt = (rec.get("dataPublicacaoPncp") or rec.get("dataInclusao") or "")[:10]
    obj = (rec.get("objetoCompra") or "").strip()
    val = rec.get("valorTotalEstimado")
    val = float(val) if isinstance(val, (int, float)) else None
    o = orgs.get(cnpj)
    if o is None:
        o = {"cnpj": cnpj, "razaoSocial": oe.get("razaoSocial"),
             "poderId": oe.get("poderId"), "esferaId": oe.get("esferaId"),
             "ufSigla": un.get("ufSigla"), "ufNome": un.get("ufNome"),
             "municipioNome": un.get("municipioNome"), "codigoIbge": un.get("codigoIbge"),
             "nObras": 0, "valorObras": 0.0, "modalidades": [], "exemplos": [],
             "primeiraObra": dt, "ultimaObra": dt, "setores": {}}
        orgs[cnpj] = o
    o["nObras"] += 1
    if val:
        o["valorObras"] += val
    if mod not in o["modalidades"]:
        o["modalidades"].append(mod)
    if obj and len(o["exemplos"]) < 3 and obj not in o["exemplos"]:
        o["exemplos"].append(obj[:180])
    if dt and (not o["primeiraObra"] or dt < o["primeiraObra"]):
        o["primeiraObra"] = dt
    if dt and dt > o["ultimaObra"]:
        o["ultimaObra"] = dt
    # setor (unidade que publicou a obra) — é aqui que aparece a "Secretaria de Obras"
    cu = un.get("codigoUnidade")
    if cu is not None:
        s = o["setores"].get(str(cu))
        if s is None:
            s = {"codigoUnidade": str(cu), "nomeUnidade": un.get("nomeUnidade"),
                 "codigoIbge": un.get("codigoIbge"), "municipioNome": un.get("municipioNome"),
                 "ufSigla": un.get("ufSigla"), "nObras": 0, "valorObras": 0.0, "ultimaObra": dt}
            o["setores"][str(cu)] = s
        s["nObras"] += 1
        if val:
            s["valorObras"] += val
        if dt and dt > (s["ultimaObra"] or ""):
            s["ultimaObra"] = dt


def _save_state(orgs, mi, pagina, stats):
    os.makedirs(OUTDIR, exist_ok=True)
    tmp = STATE + ".tmp"
    json.dump({"cursor": {"mi": mi, "pagina": pagina}, "stats": stats, "orgs": orgs},
              open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, STATE)  # escrita atômica


def sweep(inicio, fim, modalidades, uf, max_paginas, resume):
    """Varre PNCP, mantém só contratações de obra (dedup/agrega por CNPJ). Resumível."""
    orgs, start_mi, start_pag = {}, 0, 1
    stats = {"vistas": 0, "obras": 0}
    if resume and os.path.exists(STATE):
        st = json.load(open(STATE, encoding="utf-8"))
        orgs = st["orgs"]
        stats = st.get("stats", stats)
        start_mi, start_pag = st["cursor"]["mi"], st["cursor"]["pagina"]
        log(f"RESUME: {len(orgs)} órgãos-de-obra, {stats['obras']}/{stats['vistas']} obras, "
            f"retomando modalidade idx {start_mi} pág {start_pag}")
    npag = 0
    for mi in range(start_mi, len(modalidades)):
        mod = modalidades[mi]
        pagina = start_pag if mi == start_mi else 1
        total_pag = None
        while True:
            url = (f"{PNCP_CONSULTA}?dataInicial={inicio}&dataFinal={fim}"
                   f"&codigoModalidadeContratacao={mod}&pagina={pagina}&tamanhoPagina=50")
            if uf:
                url += f"&uf={uf}"
            try:
                d = get(url, raise_net=True)
            except NetErr as e:
                _save_state(orgs, mi, pagina, stats)
                raise NetErr(f"modalidade {mod} pág {pagina}: {e}")
            if not d or "data" not in d:
                break
            if total_pag is None:
                total_pag = d.get("totalPaginas", 1)
                log(f"  modalidade {mod} ({MODAL_NOME.get(mod, mod)}): "
                    f"{d.get('totalRegistros', 0)} reg / {total_pag} pág "
                    f"(órgãos-de-obra até agora: {len(orgs)})")
            for rec in d.get("data", []):
                stats["vistas"] += 1
                if eh_obra(rec.get("objetoCompra")):
                    stats["obras"] += 1
                    _absorve(orgs, rec, mod)
            npag += 1
            if npag % 200 == 0:
                _save_state(orgs, mi, pagina, stats)
                log(f"  checkpoint: {npag} pág · {stats['obras']}/{stats['vistas']} obras · "
                    f"{len(orgs)} órgãos-de-obra")
            pagina += 1
            if pagina > (total_pag or 1) or (max_paginas and pagina > max_paginas):
                break
        _save_state(orgs, mi + 1, 1, stats)
    log(f"varredura concluída: {stats['obras']}/{stats['vistas']} contratações classificadas como obra")
    return orgs, stats


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


def _save_cache(cache):
    os.makedirs(OUTDIR, exist_ok=True)
    json.dump(cache, open(CACHE, "w"), ensure_ascii=False)


def build(orgs, args, cache):
    ufs = {}
    items = list(orgs.items())
    # órgãos com mais obras primeiro (leads mais quentes enriquecidos antes)
    items.sort(key=lambda kv: kv[1].get("nObras", 0), reverse=True)
    if args.limit_orgaos:
        items = items[:args.limit_orgaos]
    for i, (cnpj, o) in enumerate(items, 1):
        rfb = None if args.sem_rfb else enrich_rfb(cnpj, cache)
        uf = o["ufSigla"] or "??"
        muni = o["codigoIbge"] or "0"
        U = ufs.setdefault(uf, {"nome": o["ufNome"], "municipios": {}})
        M = U["municipios"].setdefault(muni, {"nome": o["municipioNome"], "orgaos": {}})
        M["orgaos"][cnpj] = {
            "razaoSocial": o["razaoSocial"],
            "poder": PODER.get(o["poderId"], o["poderId"]),
            "esfera": ESFERA.get(o["esferaId"], o["esferaId"]),
            "nObras": o["nObras"], "valorObras": round(o["valorObras"], 2) or None,
            "modalidades": [MODAL_NOME.get(m, str(m)) for m in sorted(o["modalidades"])],
            "primeiraObra": o["primeiraObra"], "ultimaObra": o["ultimaObra"],
            "exemplos": o["exemplos"], "setores": o["setores"],
            "rfb": rfb, "site": None,
        }
        if i % 25 == 0:
            log(f"  enriquecidos {i}/{len(items)} órgãos-de-obra")
            _save_cache(cache)
    return ufs


def write_outputs(ufs, stats):
    os.makedirs(OUTDIR, exist_ok=True)
    n_uf = len(ufs)
    n_muni = sum(len(u["municipios"]) for u in ufs.values())
    n_org = sum(len(m["orgaos"]) for u in ufs.values() for m in u["municipios"].values())
    n_set = sum(len(o["setores"]) for u in ufs.values() for m in u["municipios"].values()
                for o in m["orgaos"].values())
    n_obras = sum(o["nObras"] for u in ufs.values() for m in u["municipios"].values()
                  for o in m["orgaos"].values())
    doc = {"meta": {"geradoEm": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "fonte": "PNCP + classificação heurística de obra + RFB",
                    "classificacao": "heurística por léxico sobre objetoCompra (grau_confianca=B)",
                    "contratacoes_obra": n_obras, "contratacoes_vistas": stats.get("vistas"),
                    "ufs": n_uf, "municipios": n_muni, "orgaos": n_org, "setores": n_set},
           "ufs": ufs}
    jpath = os.path.join(OUTDIR, "obras_engenharia.json")
    json.dump(doc, open(jpath, "w", encoding="utf-8"), ensure_ascii=False)
    cpath = os.path.join(OUTDIR, "obras_engenharia.csv")
    with open(cpath, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["uf", "municipio", "codigo_ibge", "cnpj", "razao_social", "poder", "esfera",
                    "n_obras", "n_setores_obras", "valor_estimado_obras", "modalidades_obras",
                    "primeira_obra", "ultima_obra", "email", "telefone", "situacao_cadastral",
                    "natureza_juridica", "site", "exemplos_objeto"])
        for uf, U in sorted(ufs.items()):
            for ibge, M in U["municipios"].items():
                for cnpj, o in M["orgaos"].items():
                    r = o.get("rfb") or {}
                    w.writerow([uf, M["nome"], ibge, cnpj, o["razaoSocial"], o["poder"], o["esfera"],
                                o["nObras"], len(o["setores"]), o["valorObras"],
                                "; ".join(o["modalidades"]), o["primeiraObra"], o["ultimaObra"],
                                r.get("email"), r.get("telefone"), r.get("situacao"),
                                r.get("naturezaJuridica"), o["site"], " | ".join(o["exemplos"])])
    log(f"OK — {n_uf} UF · {n_muni} municípios · {n_org} órgãos-de-obra · {n_set} setores · "
        f"{n_obras} contratações de obra")
    log(f"  -> {jpath}")
    log(f"  -> {cpath}")
    return doc["meta"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", required=True, help="yyyyMMdd")
    ap.add_argument("--fim", required=True, help="yyyyMMdd")
    ap.add_argument("--modalidades", default="1,2,4,5,6,7,8,9,12",
                    help="csv de códigos (default cobre obras: concorrência/diálogo/dispensa/etc.)")
    ap.add_argument("--uf", default=None, help="filtrar por UF (ex.: MG p/ Fase 1)")
    ap.add_argument("--max-paginas", type=int, default=0, help="cap de páginas/modalidade (0=todas)")
    ap.add_argument("--limit-orgaos", type=int, default=0, help="cap de órgãos a enriquecer (0=todos)")
    ap.add_argument("--sem-rfb", action="store_true", help="não enriquecer na RFB")
    ap.add_argument("--resume", action="store_true", help="retomar de checkpoint (.sweep_obras_state.json)")
    args = ap.parse_args()
    mods = [int(x) for x in args.modalidades.split(",") if x.strip()]
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    log(f"varrendo PNCP {args.inicio}..{args.fim} modalidades={mods} uf={args.uf or 'todas'} (recorte: OBRAS)")
    try:
        orgs, stats = sweep(args.inicio, args.fim, mods, args.uf, args.max_paginas, args.resume)
    except NetErr as e:
        log(f"QUEDA DE REDE — checkpoint salvo; rode de novo com --resume. ({e})")
        sys.exit(1)
    log(f"órgãos-de-obra distintos (CNPJ): {len(orgs)}")
    ufs = build(orgs, args, cache)
    _save_cache(cache)
    write_outputs(ufs, stats)


if __name__ == "__main__":
    main()
