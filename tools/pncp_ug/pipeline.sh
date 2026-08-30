#!/bin/bash
# Lotes automáticos enquanto a varredura roda: a cada 2h carga (upsert) + RFB dos novos; ao fim: carga + RFB + contatos + painel 2.
cd "$(dirname "$0")"; PY=~/.claude/jobs/email-central/venv/bin/python
export P1_DB_URL="$(sed -n '8p' ~/.claude/jobs/tse-nasc-mg/tse_nasc_mg.py | grep -o "postgres[^\"']*" | head -1)"
log(){ echo "[$(date '+%d/%m %H:%M:%S')] $*"; }
lote(){ log "LOTE: carga"; $PY carga_pncp.py 2>&1 | grep -v Warning | tail -3; log "LOTE: rfb"; $PY rfb_orgaos.py --conc 5 2>&1 | grep -v Warning | tail -2; }
while pgrep -f coleta_orgaos.py >/dev/null; do lote; log "varredura: $(tail -1 coleta.log)"; sleep 7200; done
log "varredura terminou → lote final"; lote
log "contatos"; $PY contatos_ug.py 2>&1 | grep -v Warning | tail -6
log "painel 2"; $PY enriquece_painel2.py 2>&1 | grep -v Warning | tail -3
log "PIPELINE CONCLUÍDO"
