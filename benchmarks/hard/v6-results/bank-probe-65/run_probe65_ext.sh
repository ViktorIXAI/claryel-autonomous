#!/bin/bash
set -u
export PATH="$HOME/.local/bin:$PATH"
{ command -v codex >/dev/null && command -v hermes >/dev/null; } || { echo "codex/hermes missing" >> <LOCAL_PATH>/parb-probe65-queue.log; exit 1; }
API="http://<LAN_IP>:8080/v1/chat/completions"
QLOG=<LOCAL_PATH>/parb-probe65-queue.log
for rep in 31 32 33; do
  for side in 64 65; do
    case $side in
      64) WS=<LOCAL_PATH>/parb-v64-contour; BANKNOTES="v6.4 CONTROL" ;;
      65) WS=<LOCAL_PATH>/parb-b65-contour; BANKNOTES="v6.5 CANDIDATE" ;;
    esac
    cd "$WS" || exit 1
    python3 ~/sah-main/scripts/plan_reps.py bank.json $rep > plan-rep$rep.json 2>>$QLOG || exit 1
    cp -f plan-rep$rep.json plan.json
    rid="p${side}r${rep}"
    date +%s > "${rid}-start.epoch"
    PARB_ROOT=. PARB_API="$API" PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 \
      PARB_KEY_FILE=p2005-profile.json PARB_GATE_VERSION=0.0.2.50 PARB_SUBSET=H-ex6-01 \
      PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
      PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
      PARB_RUN_NOTES="v6.5 probe extension (amended rule 17:44 CET): ${BANKNOTES}, stamp 0.0.2.50 behavior 2.48, H-ex6-01, seed rep $rep" \
      python3 -u gate_run.py > "${rid}.log" 2>&1
    echo "$rid: exit=$? rows=$(wc -l < results-${rid}.jsonl 2>/dev/null)" >> $QLOG
    date +%s > "${rid}-end.epoch"
  done
done
RAW=<LOCAL_PATH>/parb-b65-raw-fair
cd $RAW || exit 1
export PARB_RAW_WS=$RAW PARB_BASALT_CHAT_URL="$API"
date +%s > fair-start.epoch
python3 ~/sah-main/scripts/raw_v6.py basalt 28,29,30 > fair-basalt.log 2>&1; rcb=$?
python3 ~/sah-main/scripts/raw_v6.py codex 28,29,30 > fair-codex.log 2>&1; rcc=$?
python3 ~/sah-main/scripts/raw_v6.py grok 28,29,30 > fair-grok.log 2>&1; rcg=$?
date +%s > fair-end.epoch
echo "fair: basalt rc=$rcb rows=$(wc -l < answers-basalt.jsonl 2>/dev/null); codex rc=$rcc rows=$(wc -l < answers-codex.jsonl 2>/dev/null); grok rc=$rcg rows=$(wc -l < answers-grok.jsonl 2>/dev/null)" >> $QLOG
echo "probe65-ext done" >> $QLOG
