#!/usr/bin/env python3
"""Carrega os CSVs no Supabase via API REST, em lotes (streaming, baixa RAM/disco).
Resumível por offset (grava .progress). Não cria arquivos grandes locais.

Env: SUPABASE_URL, SUPABASE_KEY (service_role).
Uso: python3 tools/load_supabase.py painel1 <painel_MG_enriquecido.csv>
     python3 tools/load_supabase.py cadastro <cadastro_institucional_MG.csv>
"""
import sys, os, csv, json, time, urllib.request, urllib.error

csv.field_size_limit(1 << 24)
URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_KEY", "")
LOTE = 1000

# colunas destino por tabela (subconjunto útil do CSV)
COLS = {
    "painel1_servidores": ["ibge", "entidade", "orgao", "esfera", "setor", "cargo_funcao",
        "matricula", "regime", "nome", "cpf", "remuneracao", "responsabilidade",
        "cnpj_entidade", "email_entidade", "telefone_entidade", "site_entidade",
        "endereco_entidade", "portal_transparencia_entidade", "redes_entidade",
        "consta_site", "origem", "grau_confianca", "motivo_ausencia"],
    "cadastro_institucional": ["entidade_id", "ibge", "uf", "cod_orgao", "cidade", "entidade",
        "orgao", "esfera", "cnpj", "endereco", "latitude", "longitude", "geo_precisao",
        "contato", "email", "emails_setoriais", "redes_sociais", "site_oficial",
        "portal_transparencia", "ouvidoria", "links_relevantes", "gestores",
        "atores_relevantes", "atores_confirmados", "atores_validados", "observacoes"],
}
TAB = {"painel1": "painel1_servidores", "cadastro": "cadastro_institucional"}
# coluna destino -> coluna de origem no CSV (quando diferem)
RENAME = {"ibge": "cod_ibge"}


def post(table, rows):
    data = json.dumps(rows).encode("utf-8")
    req = urllib.request.Request(f"{URL}/rest/v1/{table}", data=data, method="POST",
        headers={"apikey": KEY, "Authorization": f"Bearer {KEY}",
                 "Content-Type": "application/json", "Prefer": "return=minimal"})
    for tent in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if tent == 3:
                raise RuntimeError(f"HTTP {e.code}: {e.read()[:300]}")
            time.sleep(2 * (tent + 1))
        except Exception:
            if tent == 3:
                raise
            time.sleep(2 * (tent + 1))


def main():
    if not URL or not KEY:
        sys.exit("defina SUPABASE_URL e SUPABASE_KEY no ambiente")
    alvo, src = sys.argv[1], sys.argv[2]
    table = TAB[alvo]; cols = COLS[table]
    prog = src + f".{table}.progress"
    feito = int(open(prog).read().strip()) if os.path.exists(prog) else 0
    print(f"carregando {table} de {src} (a partir da linha {feito})", flush=True)
    buf = []; n = 0; enviados = feito
    with open(src, encoding="utf-8") as f:
        rd = csv.DictReader(f, delimiter=";")
        for r in rd:
            n += 1
            if n <= feito:
                continue
            buf.append({c: (r.get(RENAME.get(c, c)) or None) for c in cols})
            if len(buf) >= LOTE:
                post(table, buf); enviados += len(buf); buf = []
                open(prog, "w").write(str(enviados))
                if enviados % 20000 == 0:
                    print(f"  {enviados} linhas", flush=True)
    if buf:
        post(table, buf); enviados += len(buf); open(prog, "w").write(str(enviados))
    print(f"OK | {table}: {enviados} linhas carregadas", flush=True)


if __name__ == "__main__":
    main()
