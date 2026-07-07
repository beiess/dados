#!/usr/bin/env python3
"""Une os estados por-modalidade (gerados em paralelo no CI) numa única cascata nacional.

Cada job do GitHub Actions varre UMA modalidade e sobe seu `.sweep_state.json` como
artefato. Aqui juntamos todos (união por CNPJ) e reaproveitamos build()/write_outputs()
de pncp_cadastro_nacional.py para gerar cadastro_nacional.json/.csv finais.

Uso: python tools/merge_cadastro_nacional.py 'states/state-*.json'
"""
import os, sys, json, glob
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pncp_cadastro_nacional as P


def load_orgs(path):
    d = json.load(open(path, encoding="utf-8"))
    return d.get("orgs", d)   # arquivo de estado = {cursor, orgs}; aceita orgs cru também


def union(paths):
    orgs = {}
    for p in paths:
        src = load_orgs(p)
        for cnpj, o in src.items():
            a = orgs.get(cnpj)
            if a is None:
                o.setdefault("unidades", {})
                o.setdefault("modalidades", [])
                orgs[cnpj] = o
                continue
            a["unidades"].update(o.get("unidades") or {})
            for m in o.get("modalidades", []):
                if m not in a["modalidades"]:
                    a["modalidades"].append(m)
            pp, up = o.get("primeiraPub"), o.get("ultimaPub")
            if pp and (not a.get("primeiraPub") or pp < a["primeiraPub"]):
                a["primeiraPub"] = pp
            if up and up > (a.get("ultimaPub") or ""):
                a["ultimaPub"] = up
            for k in ("razaoSocial", "poderId", "esferaId", "ufSigla", "ufNome",
                      "municipioNome", "codigoIbge"):
                if not a.get(k) and o.get(k):
                    a[k] = o[k]
    return orgs


def main():
    paths = []
    for a in sys.argv[1:]:
        paths += sorted(glob.glob(a)) if any(c in a for c in "*?[") else [a]
    paths = [p for p in paths if os.path.exists(p)]
    if not paths:
        sys.exit("uso: merge_cadastro_nacional.py <state1.json|glob> [...]")
    P.log(f"unindo {len(paths)} estados por-modalidade…")
    orgs = union(paths)
    P.log(f"órgãos distintos após merge: {len(orgs)}")
    args = SimpleNamespace(sem_rfb=True, sem_setores=True, limit_orgaos=0)
    ufs = P.build(orgs, args, {})
    P.write_outputs(ufs)


if __name__ == "__main__":
    main()
