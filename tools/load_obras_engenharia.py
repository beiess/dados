#!/usr/bin/env python3
"""Carrega o Painel 7 — Obras e Serviços de Engenharia no Supabase.

Lê data_full/obras_engenharia.json (gerado por pncp_obras_engenharia.py), achata em
dois grãos e grava nas tabelas do db/schema_p7.sql:
  - obras_engenharia_orgaos     (1 linha por ÓRGÃO/cnpj que contrata obra)
  - obras_engenharia_unidades   (1 linha por SETOR que publicou obra)

Modos:
  --truncate  (default) esvazia e recarrega tudo (rpc truncate_obras_engenharia).
  --upsert    faz UPSERT por cnpj / (cnpj,codigo_unidade) — para a retroalimentação semanal.

PRÉ-REQUISITO: rodar db/schema_p7.sql no SQL Editor do Supabase antes da 1ª carga.
Env: SUPABASE_URL, SUPABASE_KEY (service_role). Opcional: P7_JSON (caminho do json).
Uso: SUPABASE_URL=... SUPABASE_KEY=... python3 tools/load_obras_engenharia.py [--upsert] [--dry]
"""
import os, sys, json, time, urllib.request, urllib.error

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_KEY", "")
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
JSONF = os.environ.get("P7_JSON", os.path.join(BASE, "data_full", "obras_engenharia.json"))
T_ORG = "obras_engenharia_orgaos"
T_UNI = "obras_engenharia_unidades"
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
    """Cascata -> (linhas de órgão, linhas de setor)."""
    coleta = doc.get("meta", {}).get("geradoEm", "")[:10]
    orgs, unis = [], []
    for uf, U in doc.get("ufs", {}).items():
        uf_nome = U.get("nome")
        for ibge, M in U.get("municipios", {}).items():
            muni = M.get("nome")
            for cnpj, O in M.get("orgaos", {}).items():
                r = O.get("rfb") or {}
                setores = O.get("setores") or {}
                nomes_set = [s.get("nomeUnidade") for s in setores.values() if s.get("nomeUnidade")]
                orgs.append({
                    "cnpj": cnpj, "razao_social": O.get("razaoSocial"),
                    "nome_fantasia": O.get("nomeFantasia"),
                    "poder": O.get("poder"), "esfera": O.get("esfera"),
                    "natureza_juridica": r.get("naturezaJuridica"),
                    "uf": uf, "uf_nome": uf_nome, "municipio": muni, "cod_ibge": ibge,
                    "n_obras": O.get("nObras") or 0,
                    "n_setores_obras": len(setores),
                    "valor_estimado_obras": O.get("valorObras"),
                    "modalidades_obras": "; ".join(O.get("modalidades") or []) or None,
                    "primeira_obra": O.get("primeiraObra"),
                    "ultima_obra": O.get("ultimaObra"),
                    "exemplos_objeto": " | ".join(O.get("exemplos") or []) or None,
                    "setores_obras": "; ".join(nomes_set) or None,
                    "email": r.get("email"), "telefone": r.get("telefone"),
                    "situacao_cadastral": r.get("situacao"),
                    "logradouro": r.get("logradouro"), "bairro": r.get("bairro"), "cep": r.get("cep"),
                    "site": O.get("site"),
                    "data_coleta": coleta, "grau_confianca": "B",
                })
                for cu, s in setores.items():
                    unis.append({"cnpj": cnpj, "codigo_unidade": str(cu),
                                 "nome_unidade": s.get("nomeUnidade"),
                                 "uf": uf, "municipio": s.get("municipioNome") or muni,
                                 "cod_ibge": s.get("codigoIbge") or ibge,
                                 "n_obras": s.get("nObras") or 0,
                                 "valor_estimado_obras": round(s.get("valorObras") or 0, 2) or None,
                                 "ultima_obra": s.get("ultimaObra")})
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
        sys.exit(f"json não encontrado: {JSONF} (rode pncp_obras_engenharia.py antes)")
    doc = json.load(open(JSONF, encoding="utf-8"))
    orgs, unis = flatten(doc)
    log(f"achatado: {len(orgs)} órgãos-de-obra · {len(unis)} setores · "
        f"modo={'UPSERT' if UPSERT else 'TRUNCATE'}{' (DRY)' if DRY else ''}")
    if not UPSERT and not DRY:
        log("truncate das tabelas…")
        sb("rpc/truncate_obras_engenharia", data={}, prefer="return=minimal")
    push(T_ORG, orgs, "cnpj")            # órgãos primeiro (FK dos setores)
    push(T_UNI, unis, "cnpj,codigo_unidade")
    log(f"OK — {len(orgs)} órgãos e {len(unis)} setores {'simulados' if DRY else 'carregados'}.")


if __name__ == "__main__":
    main()
