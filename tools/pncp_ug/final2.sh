#!/bin/bash
# Após a 2ª passada de RFB: sede/situação (contatos_ug) + Painel 2 → marca conclusão 2.
cd "$(dirname "$0")"; PY=~/.claude/jobs/email-central/venv/bin/python
export P1_DB_URL="$(sed -n '8p' ~/.claude/jobs/tse-nasc-mg/tse_nasc_mg.py | grep -o "postgres[^\"']*" | head -1)"
log(){ echo "[$(date '+%d/%m %H:%M:%S')] $*"; }
log "final2: aguardando RFB (2ª passada)…"; while pgrep -f "[r]fb_orgaos.py --conc" >/dev/null; do sleep 120; done
log "final2: rfb residual"; $PY rfb_orgaos.py --conc 5 2>&1 | grep -v Warning | tail -2
log "final2: contatos"; $PY contatos_ug.py 2>&1 | grep -v Warning | tail -6
log "final2: painel 2"; $PY enriquece_painel2.py 2>&1 | grep -v Warning | tail -3
log "PIPELINE 2 CONCLUÍDO"
