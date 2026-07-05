#!/bin/bash
# Varredura nacional PNCP resiliente: retoma com --resume até concluir (sobrevive a
# quedas de rede / sono do laptop). Uso: bash tools/run_cadastro_nacional.sh [--fresh]
cd "$(dirname "$0")/.." || exit 1
ARGS="--inicio 20250705 --fim 20260705 --modalidades 1,2,3,4,5,6,7,8,9,12,13 --sem-rfb --sem-setores"
LOG="data_full/cadastro_nacional.log"
[ "$1" = "--fresh" ] && rm -f data_full/.sweep_state.json data_full/.sweep_done
# já concluído: nada a fazer (evita re-rodar a cada login)
[ -f data_full/.sweep_done ] && { echo "[wrapper] já concluído ($(date))"; exit 0; }
# trava anti-duplicata: se já há uma varredura rodando, sai (não corrompe o checkpoint)
if pgrep -f pncp_cadastro_nacional.py >/dev/null 2>&1; then
  echo "[wrapper] outra varredura já em andamento ($(date)) — saindo" >> "$LOG"; exit 0
fi
echo "==== $(date) início/retomada ====" >> "$LOG"
n=0
until python3 tools/pncp_cadastro_nacional.py $ARGS --resume >> "$LOG" 2>&1; do
  n=$((n+1))
  echo "[wrapper] queda (tentativa $n) — aguardando 60s e retomando…" >> "$LOG"
  sleep 60
done
touch data_full/.sweep_done
echo "==== $(date) concluído (após $n retomadas) ====" >> "$LOG"
