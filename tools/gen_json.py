#!/usr/bin/env python3
"""Gera JSON por municipio (formato compacto {c:[cols],r:[[...]]}) para o app estatico.
Painel 1 (servidores) e Painel 2 (cadastro) + municipios.json com contagens.

Uso: python3 tools/gen_json.py
"""
import csv, os, json
from collections import defaultdict

csv.field_size_limit(1 << 24)
B = ".."
P1 = os.path.join(B, "exports", "painel_MG_enriquecido.csv")
P2 = os.path.join(B, "exports", "cadastro_institucional_MG.csv")
OUT1 = "data/p1"; OUT2 = "data/p2"
os.makedirs(OUT1, exist_ok=True); os.makedirs(OUT2, exist_ok=True)

P1J = ["orgao", "setor", "cargo_funcao", "nome", "cpf", "matricula", "responsabilidade",
       "consta_site", "email_entidade", "telefone_entidade", "site_entidade", "origem"]
P2J = ["orgao", "esfera", "cnpj", "endereco", "contato", "email", "site_oficial",
       "portal_transparencia", "gestores", "atores_validados", "observacoes"]

# --- Painel 1: agrupa por cod_ibge
g1 = defaultdict(list)
with open(P1, encoding="utf-8") as f:
    rd = csv.DictReader(f, delimiter=";")
    for r in rd:
        ib = r.get("cod_ibge")
        if ib:
            g1[ib].append([r.get(c) or "" for c in P1J])
for ib, rows in g1.items():
    json.dump({"c": P1J, "r": rows}, open(f"{OUT1}/{ib}.json", "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
print(f"P1: {len(g1)} municipios, {sum(len(v) for v in g1.values())} pessoas", flush=True)

# --- Painel 2: agrupa por ibge
g2 = defaultdict(list)
nomes = {}
with open(P2, encoding="utf-8") as f:
    rd = csv.DictReader(f, delimiter=";")
    for r in rd:
        ib = r.get("ibge")
        if ib:
            g2[ib].append([r.get(c) or "" for c in P2J])
            nomes.setdefault(ib, r.get("cidade") or ib)
for ib, rows in g2.items():
    json.dump({"c": P2J, "r": rows}, open(f"{OUT2}/{ib}.json", "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
print(f"P2: {len(g2)} municipios, {sum(len(v) for v in g2.values())} orgaos", flush=True)

# --- municipios.json (todos os ibge do P1) com contagens
muni = []
for ib in sorted(set(g1) | set(g2)):
    muni.append({"ibge": ib, "nome": nomes.get(ib, ib),
                 "n1": len(g1.get(ib, [])), "n2": len(g2.get(ib, []))})
json.dump(muni, open("municipios.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"municipios.json: {len(muni)} municipios", flush=True)
tot = sum(os.path.getsize(os.path.join(d, f)) for d in (OUT1, OUT2) for f in os.listdir(d))
print(f"tamanho data/: {tot/2**20:.0f} MB", flush=True)
