#!/usr/bin/env python3
"""Carrega o Cadastro Institucional Nacional (cascata PNCP) no Supabase.

Lê data_full/cadastro_nacional.json (gerado por pncp_cadastro_nacional.py), achata em
dois grãos e grava nas tabelas do db/schema_p2n.sql:
  - cadastro_institucional_br           (1 linha por ÓRGÃO/cnpj)
  - cadastro_institucional_br_unidades  (1 linha por SETOR)

Modos:
  --truncate  (default) esvazia e recarrega tudo (rpc truncate_cadastro_institucional_br).
  --upsert    faz UPSERT por cnpj / (cnpj,codigo_unidade) — para a retroalimentação semanal.

PRÉ-REQUISITO: rodar db/schema_p2n.sql no SQL Editor do Supabase antes da 1ª carga.
Env: SUPABASE_URL, SUPABASE_KEY (service_role). Opcional: P2N_JSON (caminho do json).
Uso: SUPABASE_URL=... SUPABASE_KEY=... python3 tools/load_cadastro_nacional.py [--upsert] [--dry]
"""
import os, sys, json, time, urllib.request, urllib.error

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_KEY", "")
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
JSONF = os.environ.get("P2N_JSON", os.path.join(BASE, "data_full", "cadastro_nacional.json"))
T_ORG = "cadastro_institucional_br"
T_UNI = "cadastro_institucional_br_unidades"
UPSERT = "--upsert" in sys.argv
DRY = "--dry" in sys.argv
BATCH = 1000


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def sb(path, data=None, method="POST", prefer=None, timeout=120):
    h = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
         "User-Agent": UA}
    if prefer:
        h["Prefer"] = prefer
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(f"{URL}/rest/v1/{path}", data=body, method=method, headers=h)
    for t in range(4):
        try:
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if t == 3:
                raise RuntimeError(f"HTTP {e.code} em {path}: {e.read()[:300]}")
            time.sleep(2 * (t + 1))


def flatten(doc):
    """Cascata -> (linhas de órgão, linhas de unidade)."""
    coleta = doc.get("meta", {}).get("geradoEm", "")[:10]
    orgs, unis = [], []
    for uf, U in doc.get("ufs", {}).items():
        uf_nome = U.get("nome")
        for ibge, M in U.get("municipios", {}).items():
            muni = M.get("nome")
            for cnpj, O in M.get("orgaos", {}).items():
                r = O.get("rfb") or {}
                f = O.get("fontePNCP") or {}
                setores = O.get("unidades") or {}
                orgs.append({
                    "cnpj": cnpj, "razao_social": O.get("razaoSocial"),
                    "nome_fantasia": O.get("nomeFantasia"),
                    "poder": O.get("poder"), "esfera": O.get("esfera"),
                    "cod_natureza_juridica": O.get("codNaturezaJuridica"),
                    "natureza_juridica": r.get("naturezaJuridica"),
                    "uf": uf, "uf_nome": uf_nome, "municipio": muni, "cod_ibge": ibge,
                    "n_setores": len(setores), "status_ativo": O.get("statusAtivo"),
                    "email": r.get("email"), "telefone": r.get("telefone"),
                    "situacao_cadastral": r.get("situacao"),
                    "logradouro": r.get("logradouro"), "bairro": r.get("bairro"), "cep": r.get("cep"),
                    "site": O.get("site"), "info_complementar": O.get("infoComplementar"),
                    "publicou_pncp": bool(f.get("publicou", True)),
                    "primeira_publicacao": f.get("primeiraPublicacao"),
                    "ultima_publicacao": f.get("ultimaPublicacao"),
                    "n_modalidades": f.get("nModalidades"),
                    "data_coleta": coleta, "grau_confianca": "A",
                })
                for cu, nome in setores.items():
                    unis.append({"cnpj": cnpj, "codigo_unidade": str(cu), "nome_unidade": nome,
                                 "uf": uf, "municipio": muni, "cod_ibge": ibge})
    return orgs, unis


def push(table, rows, conflict):
    if not rows:
        return 0
    path = f"{table}?on_conflict={conflict}" if UPSERT else table
    prefer = "return=minimal,resolution=merge-duplicates" if UPSERT else "return=minimal"
    n = 0
    for i in range(0, len(rows), BATCH):
        chunk = rows[i:i + BATCH]
        if not DRY:
            sb(path, data=chunk, prefer=prefer)
        n += len(chunk)
        if n % 10000 == 0:
            log(f"  {table}: {n}/{len(rows)}")
    return n


def main():
    if not URL or not KEY:
        sys.exit("defina SUPABASE_URL e SUPABASE_KEY (service_role)")
    if not os.path.exists(JSONF):
        sys.exit(f"json não encontrado: {JSONF} (rode pncp_cadastro_nacional.py antes)")
    doc = json.load(open(JSONF, encoding="utf-8"))
    orgs, unis = flatten(doc)
    log(f"achatado: {len(orgs)} órgãos · {len(unis)} setores · modo={'UPSERT' if UPSERT else 'TRUNCATE'}{' (DRY)' if DRY else ''}")
    if not UPSERT and not DRY:
        log("truncate das tabelas…")
        sb("rpc/truncate_cadastro_institucional_br", data={}, prefer="return=minimal")
    push(T_ORG, orgs, "cnpj")            # órgãos primeiro (FK das unidades)
    push(T_UNI, unis, "cnpj,codigo_unidade")
    log(f"OK — {len(orgs)} órgãos e {len(unis)} setores {'simulados' if DRY else 'carregados'}.")


if __name__ == "__main__":
    main()
