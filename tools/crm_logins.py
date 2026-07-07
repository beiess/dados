#!/usr/bin/env python3
"""Provisiona logins do CRM no Supabase Auth (service_role).

Login por CPF+senha = usuário Auth com email alias cpf<digitos>@crm.plenumbrasil.com.br
(o app converte CPF digitado -> alias). Fontes, em ordem:
  1) --link EMAIL          vincula um usuário Auth JÁ existente ao funcionário com esse email
                           (ex.: --link israel@licitapublica.com.br  -> acesso irrestrito)
  2) --cpf 00000000000 --senha X --nome "Fulano"   provisiona um login avulso
  3) (padrão) varre logins_pendentes (preenchidos pelo admin no app), cria os usuários
     no Auth, vincula funcionarios.auth_user_id e APAGA a linha pendente.

Env: SUPABASE_URL, SUPABASE_KEY (service_role).
"""
import os, sys, json, urllib.request, urllib.error, urllib.parse

U = os.environ.get("SUPABASE_URL", "").rstrip("/")
K = os.environ.get("SUPABASE_KEY", "")
DOM = "crm.plenumbrasil.com.br"


def req(path, data=None, method="GET", base="rest/v1", prefer=None):
    h = {"apikey": K, "Authorization": f"Bearer {K}", "Content-Type": "application/json"}
    if prefer: h["Prefer"] = prefer
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(f"{U}/{base}/{path}", data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} em {path}: {e.read().decode()[:300]}")


def alias(cpf): return f"cpf{''.join(ch for ch in cpf if ch.isdigit())}@{DOM}"


def criar_auth(email, senha):
    u = req("admin/users", {"email": email, "password": senha, "email_confirm": True},
            method="POST", base="auth/v1")
    return u["id"]


def achar_auth(email):
    page = 1
    while page < 50:
        r = req(f"admin/users?page={page}&per_page=100", base="auth/v1") or {}
        users = r.get("users", r if isinstance(r, list) else [])
        for u in users:
            if (u.get("email") or "").lower() == email.lower(): return u["id"]
        if len(users) < 100: return None
        page += 1


def vincular(func_id, auth_id):
    req(f"funcionarios?id=eq.{func_id}", {"auth_user_id": auth_id}, method="PATCH",
        prefer="return=minimal")


def main():
    if not U or not K: sys.exit("defina SUPABASE_URL e SUPABASE_KEY (service_role)")
    a = sys.argv[1:]

    if "--link" in a:                                        # vincular usuário Auth existente
        email = a[a.index("--link") + 1]
        f = req(f"funcionarios?select=id,nome&email=eq.{email}")
        if not f: sys.exit(f"funcionário com email {email} não encontrado")
        uid = achar_auth(email)
        if not uid:
            senha = a[a.index("--senha") + 1] if "--senha" in a else None
            if not senha: sys.exit(f"usuário Auth {email} não existe — passe --senha para criá-lo")
            uid = criar_auth(email, senha)
        vincular(f[0]["id"], uid)
        print(f"OK — {f[0]['nome']} vinculado ao Auth ({email})")
        return

    if "--cpf" in a:                                         # login avulso por CPF
        cpf = a[a.index("--cpf") + 1]; senha = a[a.index("--senha") + 1]
        nome = a[a.index("--nome") + 1] if "--nome" in a else None
        q = f"funcionarios?select=id,nome&cpf=eq.{''.join(ch for ch in cpf if ch.isdigit())}"
        f = req(q) or (req(f"funcionarios?select=id,nome&nome=ilike.*{urllib.parse.quote(nome)}*") if nome else [])
        if not f: sys.exit("funcionário não encontrado (cadastre no app com o CPF primeiro)")
        uid = criar_auth(alias(cpf), senha)
        req(f"funcionarios?id=eq.{f[0]['id']}", {"auth_user_id": uid, "cpf": ''.join(ch for ch in cpf if ch.isdigit())},
            method="PATCH", prefer="return=minimal")
        print(f"OK — login CPF criado p/ {f[0]['nome']} ({alias(cpf)})")
        return

    pend = req("logins_pendentes?select=funcionario_id,cpf,senha") or []
    if not pend:
        print("nenhum login pendente (o admin preenche CPF+senha no app).")
        return
    for p in pend:
        uid = criar_auth(alias(p["cpf"]), p["senha"])
        vincular(p["funcionario_id"], uid)
        req(f"logins_pendentes?funcionario_id=eq.{p['funcionario_id']}", method="DELETE")
        print(f"provisionado: funcionario {p['funcionario_id']} ({alias(p['cpf'])})")
    print(f"OK — {len(pend)} logins criados e pendências apagadas.")


if __name__ == "__main__":
    main()
