#!/usr/bin/env python3
"""Carrega empresas + funcionários do CRM a partir da planilha do RH (COLABORADORES 2026.xls).

Mapeia a planilha real p/ o schema_crm.sql:
  CNPJ->empresas.cnpj | Nome Unidade->empresas.nome | Nome Setor->funcionarios.setor |
  Nome Cargo->cargo (+ nivel romano) | Nome Funcionário->nome |
  "Area de Atuação Setor Comercial"->area_atuacao (normaliza "Legilslativo"->"Legislativo") |
  Salário/Dt.Admissão/Sexo/OBS(localização) -> campos de RH | funcao (papel no app) derivada do cargo.

PRÉ-REQUISITO: rodar db/schema_crm.sql no Supabase antes. O login (auth_user_id) NÃO é criado aqui —
é feito via convite/signup no Supabase Auth e depois vinculado por email.
Env: SUPABASE_URL, SUPABASE_KEY (service_role). Opcional: CRM_XLS (caminho da planilha).
Uso: SUPABASE_URL=... SUPABASE_KEY=... python3 tools/load_crm_colaboradores.py [--dry]
"""
import os, sys, re, json, urllib.request, urllib.error
import pandas as pd

U = os.environ.get("SUPABASE_URL", "").rstrip("/")
K = os.environ.get("SUPABASE_KEY", "")
XLS = os.environ.get("CRM_XLS", "/Users/israelsantiago/Library/CloudStorage/GoogleDrive-israel.taptos@gmail.com/"
                      "Outros computadores/Meu laptop/D:/Plenum/Administrativo Plenum/"
                      "Recursos Humanos/Interno/COLABORADORES 2026.xls")
DRY = "--dry" in sys.argv
AREA = {"legilslativo": "Legislativo", "legislativo": "Legislativo", "gestão pública": "Gestão Pública",
        "gestao publica": "Gestão Pública"}
ROMAN = re.compile(r"\b(I{1,3}|IV|V|VI{0,3}|IX|X)\b")


def only_digits(s): return re.sub(r"\D", "", str(s or ""))


def sb(path, data=None, method="GET", prefer=None):
    h = {"apikey": K, "Authorization": f"Bearer {K}", "Content-Type": "application/json"}
    if prefer: h["Prefer"] = prefer
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(f"{U}/rest/v1/{path}", data=body, method=method, headers=h)
    with urllib.request.urlopen(r, timeout=60) as resp:
        raw = resp.read()
        return json.loads(raw) if raw and method == "GET" else None


def papel(cargo):
    c = (cargo or "").lower()
    if "diretor" in c: return "gerente"
    if "gerente" in c: return "gerente"
    if "vendedor" in c: return "vendedor"
    return "vendedor"                       # demais (admin/limpeza/financeiro) entram como vendedor; ajustar depois


def nivel(cargo):
    m = ROMAN.search((cargo or "").upper())
    return m.group(1) if m else None


def main():
    if not U or not K: sys.exit("defina SUPABASE_URL e SUPABASE_KEY (service_role)")
    df = pd.read_excel(XLS, sheet_name="ModeloI", header=1).dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]
    col_area = next(c for c in df.columns if c.lower().startswith("area de atua"))

    # empresas por cnpj (a 1ª unidade que aparece nomeia; matriz = a marcada na últ. coluna)
    emp = {}
    for _, r in df.iterrows():
        cnpj = only_digits(r["CNPJ"])
        if not cnpj: continue
        tipo = "matriz" if "matriz" in str(r.get("Unnamed: 12", "")).lower() else "filial"
        emp.setdefault(cnpj, {"cnpj": cnpj, "nome": str(r["Nome Unidade"]).strip(), "tipo": tipo})
    print(f"empresas: {len(emp)} | funcionários: {len(df)}{' (DRY)' if DRY else ''}")

    if not DRY:
        for e in emp.values():
            sb("empresas?on_conflict=cnpj", data=[e], method="POST",
               prefer="return=minimal,resolution=merge-duplicates")
    idmap = {only_digits(x["cnpj"]): x["id"] for x in sb("empresas?select=id,cnpj")} if not DRY else {}

    funcs = []
    for _, r in df.iterrows():
        cnpj = only_digits(r["CNPJ"])
        cargo = str(r["Nome Cargo"]).strip()
        area_raw = str(r.get(col_area, "")).strip().lower()
        obs = str(r.get("OBS", "") or "")
        loc = "BH" if "bh" in obs.lower() else ("DF" if "df" in obs.lower() else None)
        dt = r.get("Dt.Admissão")
        funcs.append({
            "nome": str(r["Nome Funcionário"]).strip(),
            "empresa_cnpj": cnpj,
            "empresa_id": idmap.get(cnpj),
            "funcao": papel(cargo),
            "setor": str(r["Nome Setor"]).strip(),
            "cargo": cargo, "nivel": nivel(cargo),
            "area_atuacao": AREA.get(area_raw),
            "salario": float(r["Salário"]) if pd.notna(r.get("Salário")) else None,
            "dt_admissao": str(pd.to_datetime(dt).date()) if pd.notna(dt) else None,
            "sexo": str(r.get("Sexo", "") or "").strip() or None,
            "localizacao": loc,
            "situacao": str(r.get("Situação", "ativo") or "ativo").strip().lower(),
        })
    if DRY:
        for f in funcs:
            print(f"  {f['nome'][:26]:26} | {f['cargo']:24} | {f['setor']:14} | {f['area_atuacao'] or '-':14} | {f['funcao']}")
        return
    payload = [{k: v for k, v in f.items() if k != "empresa_cnpj"} for f in funcs if f["empresa_id"]]
    sb("funcionarios", data=payload, method="POST", prefer="return=minimal")
    print(f"OK — {len(emp)} empresas e {len(payload)} funcionários carregados. "
          f"Vincule os logins depois (Supabase Auth -> auth_user_id por email).")


if __name__ == "__main__":
    main()
