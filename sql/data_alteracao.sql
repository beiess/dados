-- data_alteracao (timestamptz) + trigger de manutenção em todas as tabelas dos painéis (aplicado 30/08/2026)
-- Semântica: INSERT sem valor → now(); UPDATE que não tocou a coluna → now() (loaders podem setar explicitamente).
-- Backfill inicial (feito ANTES da trigger) com a data de coleta/entrada existente; painel1_servidores e
-- servidores_brasil_2026 (8,4M/7,9M) ficam NULL — histórico começa nas próximas inclusões/alterações.
-- Filtro do app (cabeçalho): data_alteracao=gte.<ini>T00:00:00 & data_alteracao=lte.<fim>T23:59:59.999
-- Reaplicar: tools/data_alteracao.py (idempotente). Views v_email_central e v_pncp_ug expõem data_alteracao
-- (P16 = greatest(unidade, órgão) para não “piscar” tudo a cada rebuild de contatos).
create or replace function trg_set_data_alteracao() returns trigger language plpgsql as $$
begin
  if TG_OP='INSERT' then if NEW.data_alteracao is null then NEW.data_alteracao := now(); end if;
  else if NEW.data_alteracao is not distinct from OLD.data_alteracao then NEW.data_alteracao := now(); end if; end if;
  return NEW;
end $$;
-- por tabela: alter table <t> add column if not exists data_alteracao timestamptz;
--             create trigger trg_data_alteracao before insert or update on <t> for each row execute function trg_set_data_alteracao();
--             create index ix_<t>_dtalt on <t>(data_alteracao);
