#!/usr/bin/env python3
"""LOCAL-ONLY: gera JSON com dados COMPLETOS (CPF cheio + matrícula) em data_full/.
NUNCA versionar (gitignored). Uso exclusivo do app local (index_local.html), na máquina.
A anonimização é feita no app (botão); aqui os dados ficam íntegros.

Uso: python3 tools/gen_json_full.py
"""
import csv, os, json
from collections import defaultdict

csv.field_size_limit(1 << 24)
B = ".."
P1 = os.path.join(B, "exports", "painel_MG_enriquecido.csv")
P2 = os.path.join(B, "exports", "cadastro_institucional_MG.csv")
OUT1, OUT2 = "data_full/p1", "data_full/p2"
os.makedirs(OUT1, exist_ok=True); os.makedirs(OUT2, exist_ok=True)

P1J = ["orgao", "setor", "cargo_funcao", "nome", "cpf", "matricula", "remuneracao",
       "responsabilidade", "consta_site", "email_entidade", "telefone_entidade",
       "site_entidade", "endereco_entidade", "origem"]
P2J = ["orgao", "esfera", "cnpj", "endereco", "contato", "email", "emails_setoriais",
       "site_oficial", "portal_transparencia", "ouvidoria", "gestores",
       "atores_validados", "observacoes"]

g1 = defaultdict(list)
with open(P1, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter=";"):
        ib = r.get("cod_ibge")
        if ib:
            g1[ib].append([r.get(c) or "" for c in P1J])
for ib, rows in g1.items():
    json.dump({"c": P1J, "r": rows}, open(f"{OUT1}/{ib}.json", "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
print(f"P1 FULL: {len(g1)} mun, {sum(len(v) for v in g1.values())} pessoas (CPF+matrícula COMPLETOS)")

g2 = defaultdict(list)
with open(P2, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter=";"):
        ib = r.get("ibge")
        if ib:
            g2[ib].append([r.get(c) or "" for c in P2J])
for ib, rows in g2.items():
    json.dump({"c": P2J, "r": rows}, open(f"{OUT2}/{ib}.json", "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
print(f"P2 FULL: {len(g2)} mun, {sum(len(v) for v in g2.values())} órgãos")
print("data_full/ gerado (LOCAL, gitignored).")
