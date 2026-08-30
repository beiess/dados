#!/usr/bin/env python3
"""Adiciona data_alteracao (timestamptz) + trigger de manutenção a todas as tabelas dos painéis.
Trigger: INSERT sem valor → now(); UPDATE que não mexeu na coluna → now() (loaders podem setar explicitamente).
Backfill (feito ANTES da trigger) usa a coluna de data existente; painel1 e servidores_brasil (gigantes) ficam NULL
(histórico começa agora; edições/inserções/cargas futuras preenchem). Recria v_email_central e v_pncp_ug com a coluna.
Re-executável. Credencial: env P1_DB_URL."""
import os, time, psycopg2
def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)
c=psycopg2.connect(os.environ['P1_DB_URL'], connect_timeout=30, keepalives=1, keepalives_idle=20); c.autocommit=True; cur=c.cursor(); cur.execute("set statement_timeout=0")
cur.execute("""create or replace function trg_set_data_alteracao() returns trigger language plpgsql as $$
begin
  if TG_OP='INSERT' then if NEW.data_alteracao is null then NEW.data_alteracao := now(); end if;
  else if NEW.data_alteracao is not distinct from OLD.data_alteracao then NEW.data_alteracao := now(); end if; end if;
  return NEW;
end $$""")
# tabela -> expressão de backfill (None = deixa NULL) ; gigantes ficam None
BF={
 'painel1_servidores':None,'servidores_brasil_2026':None,
 'cadastro_institucional':None,'cadastro_institucional_br':"data_coleta::timestamptz",
 'fornecedores_obra':None,'contratos_2026':None,'estrutura_despesa_2026':None,'painel6_responsaveis':None,
 'servidores_estado_2026':None,'obras_engenharia_orgaos':"data_coleta::timestamptz","obras_engenharia_unidades":None,
 'pessoas_obras':"data_coleta::timestamptz",'contatos_orgaos_fontes':"data_coleta::timestamptz",
 'painel14_gestores_rh':"data_carga::timestamptz",'email_registro':"greatest(entrada_em, atualizado_em)",
 'email_validacao':"verificado_em",'pncp_orgaos':"greatest(data_inclusao, data_atualizacao)",
 'pncp_unidades':"greatest(data_inclusao, data_atualizacao)",'pncp_ug_contatos':"now()"}
for t,bf in BF.items():
    try:
        cur.execute(f"alter table {t} add column if not exists data_alteracao timestamptz")
        # backfill só onde ainda nulo e há expressão (antes da trigger; se a trigger já existir, dropa)
        cur.execute(f"drop trigger if exists trg_data_alteracao on {t}")
        if bf:
            t0=time.time(); cur.execute(f"update {t} set data_alteracao={bf} where data_alteracao is null"); log(f"{t}: backfill {cur.rowcount} em {time.time()-t0:.0f}s")
        cur.execute(f"create trigger trg_data_alteracao before insert or update on {t} for each row execute function trg_set_data_alteracao()")
        cur.execute(f"create index if not exists ix_{t[:24]}_dtalt on {t} (data_alteracao)")
        log(f"{t}: coluna+trigger+índice OK")
    except Exception as e:
        log(f"{t}: ERRO {str(e)[:120]}")
# views com data_alteracao
cur.execute("""create or replace view v_email_central as
 select r.id, r.email, r.dominio, r.local_part, r.fontes, r.n_ocorrencias, r.entrada_em, r.primeira_fonte, r.status,
  v.sintaxe_ok, v.mx_ok, v.mx_provedor, v.smtp_status, v.is_catch_all, v.tipo, v.role_based, v.descartavel, v.risco,
  v.spf, v.dkim, v.dmarc, v.dmarc_politica, v.confiabilidade, v.assertividade, v.estrategia, v.tags, v.verificado_em, v.camadas,
  x.nome, x.cpf, x.orgao, x.cargo, x.setor, x.esfera, x.uf, x.municipio, x.cnpj, x.ibge, x.n_pessoas, x.ufs, x.ibges, x.esferas, x.cnpjs,
  greatest(r.data_alteracao, v.data_alteracao) as data_alteracao
 from email_registro r left join email_validacao v using (email) left join email_vinculos x using (email)""")
cur.execute("revoke all on v_email_central from anon; grant select on v_email_central to authenticated, service_role")
cur.execute("""create or replace view v_pncp_ug as
 select u.id, u.uf, u.municipio, u.cod_ibge, o.razao_social as orgao, o.cnpj, u.codigo_unidade, u.nome_unidade,
  case o.esfera when 'M' then 'municipal' when 'E' then 'estadual' when 'F' then 'federal' when 'D' then 'distrital' else null end as esfera,
  case o.poder when 'E' then 'Executivo' when 'L' then 'Legislativo' when 'J' then 'Judiciário' when 'M' then 'Ministério Público' else null end as poder,
  o.natureza_juridica, o.cod_natureza_juridica, c.email_orgao, c.telefone_orgao, c.site, c.portal_transparencia, c.ouvidoria,
  c.email_setor, c.contato_pessoa, c.n_contatos, c.fonte as fonte_contato, c.dominio_institucional, a.codigo_uasg, a.nome_uasg, a.uso_sisg, a.codigo_siorg,
  o.orgao_id, o.n_unidades, o.validado, o.publicou_pncp, o.cliente_pncp, u.status_ativo, u.data_inclusao, o.data_inclusao as orgao_data_inclusao,
  o.situacao_cadastral as situacao_rfb, ((r.logradouro||coalesce(', '||r.numero,''))||coalesce(' - '||r.bairro,''))||coalesce(' · CEP '||r.cep,'') as endereco_rfb,
  greatest(u.data_alteracao, o.data_alteracao) as data_alteracao
 from pncp_unidades u join pncp_orgaos o on o.orgao_id=u.orgao_id
 left join pncp_ug_contatos c on c.unidade_id=u.id
 left join uasg a on a.codigo_uasg=u.codigo_unidade and a.cnpj_orgao=u.cnpj
 left join pncp_orgaos_rfb r on r.cnpj=u.cnpj and r.status=200""")
cur.execute("revoke all on v_pncp_ug from anon; grant select on v_pncp_ug to authenticated, service_role")
cur.execute("select pg_notify('pgrst','reload schema')")
cur.execute("select count(*) filter (where data_alteracao is not null) from pncp_orgaos"); log(f"pncp_orgaos c/ data_alteracao: {cur.fetchone()[0]}")
log("FIM")
