-- Camada consolidada de LEADS de obras (views sobre os painéis).
-- Junta órgão que contrata obra + contatos + nº de pessoas, num objeto único consultável
-- (app, Metabase, API e export lêem o mesmo lugar). Rodar no SQL Editor do Supabase.
-- security_invoker=on => a view respeita a RLS das tabelas base (leitura só autenticada).

-- 1) v_leads_obras — 1 linha por ÓRGÃO de obra, com contatos e agregado de pessoas do município.
create or replace view v_leads_obras with (security_invoker = on) as
select
  o.uf, o.municipio, o.cod_ibge, o.cnpj, o.razao_social, o.poder, o.esfera,
  o.n_obras, o.valor_estimado_obras, o.modalidades_obras, o.primeira_obra, o.ultima_obra,
  o.n_setores_obras, o.setores_obras,
  o.email, o.emails_setoriais, o.telefone, o.site, o.situacao_cadastral,
  coalesce(p.n_pessoas, 0)       as n_pessoas_municipio,
  coalesce(p.n_pessoas_email, 0) as n_pessoas_com_email
from obras_engenharia_orgaos o
left join (
  select cod_ibge, count(*) as n_pessoas, count(email) as n_pessoas_email
  from pessoas_obras
  group by cod_ibge
) p on p.cod_ibge = o.cod_ibge;

-- 2) v_leads_prospeccao — enxuta e ordenada por valor, pronta p/ CRM/campanha (só quem tem contato).
create or replace view v_leads_prospeccao with (security_invoker = on) as
select
  uf, municipio, razao_social as orgao, cnpj,
  setores_obras as secretarias,
  email, emails_setoriais, telefone, site,
  n_obras, valor_estimado_obras, ultima_obra
from obras_engenharia_orgaos
where email is not null or emails_setoriais is not null or telefone is not null
order by valor_estimado_obras desc nulls last;

-- 3) v_pessoas_obras_lead — cada pessoa + o peso de obra do seu município (para priorizar contato).
--    (CPF continua na base; mascare na exposição fora do ambiente autenticado.)
create or replace view v_pessoas_obras_lead with (security_invoker = on) as
select
  pe.nome, pe.cpf, pe.setor, pe.email, pe.origem, pe.orgao, pe.municipio, pe.cod_ibge,
  m.n_obras_municipio, m.valor_obras_municipio
from pessoas_obras pe
left join (
  select cod_ibge, sum(n_obras) as n_obras_municipio, sum(valor_estimado_obras) as valor_obras_municipio
  from obras_engenharia_orgaos
  group by cod_ibge
) m on m.cod_ibge = pe.cod_ibge;

-- Observação: views com security_invoker herdam a RLS das tabelas base; não precisam de policy própria.
-- Consumo via API:  GET /rest/v1/v_leads_prospeccao?uf=eq.MG&order=valor_estimado_obras.desc
