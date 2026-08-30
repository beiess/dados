# Curadoria de diretórios oficiais por UF — contrato de saída (agentes web-reach)

Objetivo: para cada órgão/entidade estadual (ou federal, no lote União) publicar CONTATOS oficiais e CATALOGAR
as APIs/portais de dados abertos que o órgão oferece. Só leitura de páginas públicas. Nada de adivinhar e-mail:
só o que está publicado (mailto:, texto na página, PDF oficial). Registrar SEMPRE a URL de origem.

Arquivos (JSON Lines, UTF-8, 1 objeto por linha; APPEND incremental, nunca reescrever):
- `<UF>/orgaos.jsonl`  — 1 linha por órgão/entidade encontrado no diretório oficial:
  {"uf":"MG","esfera":"estadual","nome":"Secretaria de Estado de Saúde","sigla":"SES-MG","tipo":"secretaria|autarquia|fundacao|empresa|fundo|tribunal|mp|legislativo|tce|outro",
   "site":"https://…","emails":["ouvidoria@…"],"telefones":["(31) 3915-…"],"endereco":"…","ouvidoria_url":"…","fale_conosco_url":"…",
   "orgao_pai":"Estado de Minas Gerais","fonte_url":"https://…(página onde o dado está)","coletado_em":"2026-08-30"}
- `<UF>/apis.jsonl` — 1 linha por API/portal de dados do órgão (ou do estado, com "orgao":"(estado)"):
  {"uf":"MG","orgao":"…","nome":"Portal de Dados Abertos de MG (CKAN)","url":"https://dados.mg.gov.br/api/3/action/package_search","docs_url":"…",
   "tipo":"CKAN|DKAN|REST|OpenAPI|GraphQL|CSV/ZIP|portal-html|outro","auth":"nenhuma|chave|token|login","formato":"json|csv|xml|html",
   "dominio":"orcamento|compras|servidores|saude|educacao|obras|transparencia|geo|normas|outro","status":"200 ok|bloqueado|erro|nao_testado",
   "obs":"…","fonte_url":"https://…","testado_em":"2026-08-30"}
- `<UF>/relatorio.md` — o que foi coberto, fontes usadas (URLs dos diretórios), o que não foi encontrado, rendimento.

Regras: MG primeiro. Testar cada API com 1 requisição real (GET) e anotar o status HTTP. Páginas que bloqueiam
curl: usar `curl -s "https://r.jina.ai/<URL>"`. Não gravar nada no Google Drive; trabalhar só em ~/.claude/jobs/diretorios-uf/.
Listas-alvo (para saber o que casar): `alvos_<UF>.csv` (órgãos do PNCP com unidades) e `alvos_<UF>_unidades.csv`
(unidades compradoras — em MG quase tudo é unidade do CNPJ "ESTADO DE MINAS GERAIS": secretarias, polícias, DER…).
