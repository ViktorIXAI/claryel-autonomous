#!/bin/bash
# bank v6.5 paired probe (rule frozen in REVIEW-INBOX 2026-11-07 17:35 CET, commit 13c6fc3,
# BEFORE any p64r28+/p65r28+ row): contour legs p64r28/29/30 (bank v6.4 control) vs
# p65r28/29/30 (bank v6.5) at PARB_SUBSET=H-ex6-01, both stamp 0.0.2.50 (behavior 2.48,
# identical tooling; contour claims nothing), matched plan_reps seeds, serial, idle endpoint.
set -u
API="http://<LAN_IP>:8080/v1/chat/completions"
QLOG=<LOCAL_PATH>/parb-probe65-queue.log
for rep in 28 29 30; do
  for side in 64 65; do
    case $side in
      64) WS=<LOCAL_PATH>/parb-v64-contour; BANKNOTES="bank v6.4 (published 85a0cd0dd6fa1fab; ws copy 7788cc288922b9a4) CONTROL" ;;
      65) WS=<LOCAL_PATH>/parb-b65-contour; BANKNOTES="bank v6.5 (published cd29d6ac94dc3267; ws copy 919517b75a614d52; H-ex6-01 scenario names the artifact, gold identical)" ;;
    esac
    cd "$WS" || { echo "ws missing" >> $QLOG; exit 1; }
    python3 ~/sah-main/scripts/plan_reps.py bank.json $rep > plan-rep$rep.json 2>>$QLOG || exit 1
    cp -f plan-rep$rep.json plan.json
    rid="p${side}r${rep}"
    date +%s > "${rid}-start.epoch"
    PARB_ROOT=. PARB_API="$API" \
      PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=p2005-profile.json \
      PARB_GATE_VERSION=0.0.2.50 PARB_SUBSET=H-ex6-01 \
      PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
      PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
      PARB_RUN_NOTES="bank v6.5 paired probe: ${BANKNOTES}; contour 0.0.2.50 behavior 2.48 on H-ex6-01 only, matched seed rep $rep; rule REVIEW-INBOX 17:35 CET" \
      python3 -u gate_run.py > "${rid}.log" 2>&1
    echo "$rid: exit=$? rows=$(wc -l < results-${rid}.jsonl 2>/dev/null)" >> $QLOG
    date +%s > "${rid}-end.epoch"
  done
done
echo "probe65 done" >> $QLOG
