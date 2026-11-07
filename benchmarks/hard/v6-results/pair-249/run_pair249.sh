#!/bin/bash
# Paired contour arms on the WORKING bank v6.6 (ws bank copy 590503cf1701a6ce):
# 0.0.2.51 (ADOPTED control line after pair-248, contour behavior 2.51) vs
# 0.0.2.52 (A PERCENT-CHAIN arithmetic, fifth 2.27-family branch).
# TARGET (published in REVIEW-INBOX 21:57 CET before any v* row): A-ex6-03 strict-fails
# 10/15 published v6.2-era draws (2/3 in BOTH arms of pair-247 and pair-248), note
# fields_mismatch:net,tax, zero a_arith events on every row. Coverage census over all 77
# v6.6 + all 77 v6.2 prompts: the grammar matches EXACTLY {A-ex6-03}; 15/15 published losses
# re-value to gold in replay, 6/6 passes untouched, mis-derivations 0 (gate_v66 pins all of it).
# A-ex6-03 bytes byte-identical v6.2 -> v6.6, chronicity evidence transfers.
# PRE-REGISTERED RULE (REVIEW-INBOX 2026-11-07 21:57 CET - the verdict is decided ONLY by that text):
#  (a) LIVE TARGET: MEASURED iff >=1 control (v51) row strict-fails A-ex6-03. Zero live target =
#      UNMEASURED, never a pass.
#  (b) CELL ATTRIBUTION: a conversion counts only if the candidate strict-PASSES where the control
#      strict-failed on the same (task,rep) AND the row carries contour:v52_a_percent_chain at
#      identical ptok/calls (any added model call on a converted row closes the stamp).
#  (c) GUARDS: zero v52 events in any control arm; ZERO v52 events outside A-ex6-03 (grammar
#      cannot match elsewhere - a fire there = grammar regression, close the stamp); ZERO candidate
#      A-ex6-03 strict-fails where the control passed; frozen-band parity (zero 2.30-32/34-config/
#      36/38/41/42/44 fires in either arm); adopted-line parity (v34 C families, v47 set trigger,
#      v48 K enum, v51 B echo, v243 loop draws, 2.39/2.40 J event census identical within seed
#      noise); stall protocol (engine_stalled rows excluded, abort above 25% of last 20).
#  (d) RESOLUTION: the target pool is 1 task x 3 seeds = 3 cells, so the verdict is CELL-LEVEL by
#      construction. The 77-cell arm mean is published with the exact pooled sign test as context
#      only; a delta under ~2 cells at three seeds is UNRESOLVABLE and never quoted as the reason.
#      ADOPT 0.0.2.52 iff (a) holds, >=1 evented conversion, and all guards clean. Otherwise freeze
#      A_PCT_CHAIN to STAMP_REVISION == (2, 52) and publish the negative with win-level detail.
# Energy per arm from gpu-power-p249.csv windows (per-arm -start.epoch/-end.epoch), side by side;
# the mechanism is zero-token by construction, extra Wh attributed only beyond run-to-run noise.
set -u
cd ~/parb-b66-contour || exit 1
for rep in 37 38 39; do
  plan=plan-rep${rep}.json
  for v in 51 52; do
    rid="v${v}r${rep}"
    date +%s > "${rid}-start.epoch"
    cp -f "$plan" plan.json
    PARB_ROOT=. PARB_API=http://<LAN_IP>:8080/v1/chat/completions \
      PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=p2005-profile.json \
      PARB_GATE_VERSION=0.0.2.$v PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
      PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
      PARB_RUN_NOTES="paired contour 0.0.2.${v} seed ${rep} on bank v6.6 (2.52 = A percent-chain arithmetic: chain recomputed by code from the prompt's own cap/floor clauses + formula, key set never changed, zero model tokens, control 0.0.2.51 = adopted line after pair-248; 2.30-2.34/2.36/2.38/2.41/2.42/2.44 frozen) " \
      python3 -u gate_run.py > "${rid}.log" 2>&1
    rc=$?
    date +%s > "${rid}-end.epoch"
    echo "$rid: exit=$rc rows=$(wc -l < "results-${rid}.jsonl" 2>/dev/null)" >> queue.log
  done
done
cp -f plan-rep39.json plan.json
echo "pair249 done" >> queue.log
