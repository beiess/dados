#!/usr/bin/env python3
"""Povoa a cascata do CRM (crm_entidades › crm_setores › crm_servidores) a partir do painel.

Fontes (Supabase, mesmas do painel): obras_engenharia_orgaos (órgãos que contratam obra,
com contatos e emails_setoriais) e pessoas_obras (servidores com setor/email/cpf).
Classificações derivadas (esfera/poder/tipo_orgao/tema) são heurísticas sobre dado público.

PRÉ-REQUISITO: db/schema_crm.sql (v2) rodado. Roda UMA vez (usa --force p/ recarregar).
Env: SUPABASE_URL, SUPABASE_KEY (service_role).  Uso: python3 tools/load_crm_entidades.py [--force] [--dry]
"""
import os, sys, re, json, unicodedata, urllib.request, urllib.parse

U = os.environ.get("SUPABASE_URL", "").rstrip("/")
K = os.environ.get("SUPABASE_KEY", "")
DRY = "--dry" in sys.argv
FORCE = "--force" in sys.argv


def sb(path, data=None, method="GET", prefer=None):
    h = {"apikey": K, "Authorization": f"Bearer {K}", "Content-Type": "application/json"}
    if prefer: h["Prefer"] = prefer
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(f"{U}/rest/v1/{path}", data=body, method=method, headers=h)
    with urllib.request.urlopen(r, timeout=120) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else None


def getall(table, select, extra=""):
    out, off = [], 0
    while True:
        rows = sb(f"{table}?select={select}{extra}&limit=1000&offset={off}") or []
        out += rows
        if len(rows) < 1000: return out
        off += 1000


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().upper()


ESFERA = {"M": "Municipal", "E": "Estadual", "F": "Federal", "D": "Estadual"}
PODER = {"E": "Executivo", "L": "Legislativo", "J": "Judiciário", "N": "—"}


def tipo_orgao(nome):
    n = norm(nome)
    if "TRIBUNAL DE CONTAS" in n: return "Tribunal de Contas", "Controle Externo"
    if "CAMARA" in n: return "Câmara Municipal", "Legislativo"
    if "FUNDO" in n and "SAUDE" in n: return "Fundo de Saúde", "Saúde"
    if n.startswith("FUNDO"): return "Fundo", None
    if "PREVID" in n: return "Instituto de Previdência", "Administração"
    if n.startswith("INSTITUTO"): return "Instituto", None
    if "CONSORCIO" in n: return "Consórcio", None
    if re.search(r"\b(DER|DEER|DAE|SAAE|DEPARTAMENTO|AUTARQUIA)\b", n): return "Autarquia / Departamento", "Obras"
    if re.search(r"\b(UNIVERSIDADE|FACULDADE|IF\b|EDUCACAO)\b", n): return "Instituto / Educação", "Educação"
    if re.search(r"\b(COMPANHIA|EMPRESA|CIA)\b", n): return "Empresa Pública", None
    if "MUNICIPIO" in n or "PREFEITURA" in n: return "Prefeitura", "Obras"
    return "Órgão", None


def tema_setor(nome):
    n = norm(nome)
    if re.search(r"OBRA|INFRA|VIACAO|URBANIS|ENGENHAR|TRANSPORTE", n): return "Obras"
    if "SAUDE" in n: return "Saúde"
    if re.search(r"EDUCA|ENSINO|ESCOLA", n): return "Educação"
    if re.search(r"ADMINISTRA|FAZENDA|COMPRAS|LICITA|GESTAO|PLANEJAMENTO|GABINETE", n): return "Administração"
    if "LEGISLATIV" in n: return "Legislativo"
    return None


def main():
    if not U or not K: sys.exit("defina SUPABASE_URL e SUPABASE_KEY (service_role)")
    try:
        ja = sb("crm_entidades?select=id&limit=1")
    except Exception:
        sys.exit("tabela crm_entidades não existe — rode db/schema_crm.sql no SQL Editor primeiro")
    if ja and not FORCE and not DRY:
        sys.exit("crm_entidades já tem dados — use --force para recarregar (apaga o que veio do painel)")
    org = sb("empresas?select=id&cnpj=eq.21650715000160")[0]["id"]

    orgaos = getall("obras_engenharia_orgaos",
                    "cnpj,cod_ibge,razao_social,uf,municipio,poder,esfera,email,telefone,site,"
                    "emails_setoriais,n_obras,valor_estimado_obras")
    pessoas = getall("pessoas_obras", "nome,cpf,setor,email,orgao,municipio,cod_ibge")
    print(f"painel: {len(orgaos)} órgãos · {len(pessoas)} pessoas{' (DRY)' if DRY else ''}")

    if FORCE and not DRY:
        # capturas ativas travam a exclusão via FK — proteção intencional
        sb("crm_servidores?origem=eq.painel_estrategico", method="DELETE")
        sb("crm_entidades?fonte=eq.painel_estrategico", method="DELETE")

    # ---- entidades ----
    ents, bykey = [], {}
    for o in orgaos:
        if not o.get("cnpj"): continue
        tp, tema = tipo_orgao(o.get("razao_social"))
        poder = PODER.get(str(o.get("poder") or "")[:1].upper(), o.get("poder") or "—")
        area = "Legislativo" if poder == "Legislativo" else "Gestão Pública"
        ents.append({"org_id": org, "cnpj": o["cnpj"], "cod_ibge": o.get("cod_ibge"),
                     "nome": o.get("razao_social"), "uf": o.get("uf"), "municipio": o.get("municipio"),
                     "esfera": ESFERA.get(str(o.get("esfera") or "M")[:1].upper(), "Municipal"),
                     "poder": poder, "tipo_orgao": tp, "area": area, "tema": tema or "Obras",
                     "email": o.get("email"), "telefone": o.get("telefone"), "site": o.get("site"),
                     "n_obras": o.get("n_obras"), "valor_obras": o.get("valor_estimado_obras"),
                     "fonte": "painel_estrategico"})
    if not DRY:
        for i in range(0, len(ents), 500):
            sb("crm_entidades", data=ents[i:i+500], method="POST", prefer="return=minimal")
        fonte = getall("crm_entidades", "id,cnpj,cod_ibge,nome,tipo_orgao")
    else:
        fonte = [dict(e, id=e["cnpj"]) for e in ents]        # ids fictícios p/ contagem no dry-run
    for e in fonte:
        bykey[e["cnpj"]] = e["id"]
        bykey.setdefault(("ibge", e["cod_ibge"], norm(e["nome"])), e["id"])
    print(f"entidades: {len(ents)}")

    # ---- setores (1º nível) ----
    # a) dos emails_setoriais ("SETOR: a@x, OUTRO: b@y"); b) dos setores de pessoas_obras
    setores = {}   # (ent_id, nome_norm) -> {payload}
    for o in orgaos:
        eid = bykey.get(o.get("cnpj"))
        if not eid: continue
        for m in re.finditer(r"([^:,]{3,80}):\s*([\w.\-+]+@[\w.\-]+)", o.get("emails_setoriais") or ""):
            nome = m.group(1).strip().title()
            setores.setdefault((eid, norm(nome)), {"entidade_id": eid, "nivel": 1, "nome": nome,
                                                    "tema": tema_setor(nome), "email": m.group(2).lower()})
    # match pessoa->entidade: exato > nome canônico ("PREFEITURA DE X"≡"MUNICIPIO DE X") >
    # câmara do município (se legislativo) > prefeitura do município
    def canon(n):
        return re.sub(r"^(PREFEITURA (MUNICIPAL )?D[EA] |MUNICIPIO D[EA] |CAMARA MUNICIPAL D[EA] )", "", norm(n))
    por_ibge = {}
    for e in fonte:
        d = por_ibge.setdefault(e["cod_ibge"], {"canon": {}, "pref": [], "cam": []})
        d["canon"].setdefault(canon(e["nome"]), []).append(e["id"])
        tp = e.get("tipo_orgao") or ""
        if tp == "Prefeitura": d["pref"].append(e["id"])
        if "mara" in tp: d["cam"].append(e["id"])
    ent_by_pessoa = {}
    for p in pessoas:
        eid = bykey.get(("ibge", p.get("cod_ibge"), norm(p.get("orgao"))))
        if not eid:
            d = por_ibge.get(p.get("cod_ibge"))
            if d:
                hit = d["canon"].get(canon(p.get("orgao") or ""))
                if hit and len(hit) == 1: eid = hit[0]
                elif "CAMARA" in norm(p.get("orgao")) and len(d["cam"]) == 1: eid = d["cam"][0]
                elif len(d["pref"]) == 1: eid = d["pref"][0]
        if not eid: continue
        ent_by_pessoa[id(p)] = eid
        nome = (p.get("setor") or "Geral").strip()[:120]
        setores.setdefault((eid, norm(nome)), {"entidade_id": eid, "nivel": 1, "nome": nome,
                                               "tema": tema_setor(nome), "email": None})
    setlist = list(setores.values())
    if not DRY:
        for i in range(0, len(setlist), 500):
            sb("crm_setores", data=setlist[i:i+500], method="POST", prefer="return=minimal")
        setid = {(s["entidade_id"], norm(s["nome"])): s["id"]
                 for s in getall("crm_setores", "id,entidade_id,nome")}
    print(f"setores (1º nível): {len(setlist)}")

    # ---- servidores (folha) ----
    srvs, skip = [], 0
    for p in pessoas:
        eid = ent_by_pessoa.get(id(p))
        if not eid: skip += 1; continue
        sid = None if DRY else setid.get((eid, norm((p.get("setor") or "Geral").strip()[:120])))
        srvs.append({"entidade_id": eid, "setor_id": sid, "nome": p.get("nome"),
                     "cargo": None, "email": p.get("email"), "cpf": p.get("cpf"),
                     "origem": "painel_estrategico"})
    if not DRY:
        for i in range(0, len(srvs), 500):
            sb("crm_servidores", data=srvs[i:i+500], method="POST", prefer="return=minimal")
    print(f"servidores: {len(srvs)} (sem match de entidade: {skip})")
    print("OK — cascata carregada." if not DRY else "DRY ok — nada gravado.")


if __name__ == "__main__":
    main()
