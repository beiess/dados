#!/bin/bash
# Lote FINAL: espera RFB/recoletas terminarem → carga (upsert) → contatos por UG → Painel 2 → marca conclusão.
cd "$(dirname "$0")"; PY=~/.claude/jobs/email-central/venv/bin/python
export P1_DB_URL="$(sed -n '8p' ~/.claude/jobs/tse-nasc-mg/tse_nasc_mg.py | grep -o "postgres[^\"']*" | head -1)"
log(){ echo "[$(date '+%d/%m %H:%M:%S')] $*"; }
log "final.sh: aguardando RFB/recoletas…"
while pgrep -f "rfb_orgaos.py --conc" >/dev/null || pgrep -f "coleta_orgaos.py --de" >/dev/null; do sleep 120; done
log "LOTE FINAL: carga"; $PY carga_pncp.py 2>&1 | grep -v Warning | tail -3
log "LOTE FINAL: rfb (residual)"; $PY rfb_orgaos.py --conc 5 2>&1 | grep -v Warning | tail -2
log "LOTE FINAL: contatos"; $PY contatos_ug.py 2>&1 | grep -v Warning | tail -7
log "LOTE FINAL: painel 2"; $PY enriquece_painel2.py 2>&1 | grep -v Warning | tail -3
log "PIPELINE CONCLUÍDO"
