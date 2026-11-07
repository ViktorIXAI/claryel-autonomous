#!/bin/bash
# Paired contour arms on the WORKING bank v6.6 (ws bank copy 590503cf1701a6ce):
# 0.0.2.52 (ADOPTED control line after pair-249, contour behavior 2.52) vs
# 0.0.2.53 (C PYTHON-LITERAL OPTIONS grounding, gate_c_ground shape C).
# TARGET (REVIEW-INBOX 22:56 CET before any v52r4x/v53r4x row): C-ex6-02 strict-fails 6/6 in the
# first v6.6 draws and 27/27 across ALL published contour rows (cadence-246 + pair-246/247/248/249
# replay), single note set_mismatch got=[A,C,D] want=[A,B,C,D]. Resampling route published-spent
# (pair-246: 2.47 fired 3/3, won 0/3) - this stamp does NOT resample; it re-derives the letter set
# by EXECUTING the prompt's own printed snippets over a closed AST allow-list (derived set ==
# gold {A,B,C,D} == the executed truth table the v6.2 changelog shipped). Coverage census pins the
# grammar to EXACTLY {C-ex6-02} over all 77 v6.6 + all 77 v6.2 prompts (gate_v67, 108 checks).
# PRE-REGISTERED RULE (REVIEW-INBOX 2026-11-07 22:56 CET - the verdict is decided ONLY by that text):
#  (a) LIVE TARGET: MEASURED iff >=1 control (v52) row strict-fails C-ex6-02. Zero live target =
#      UNMEASURED, never a pass.
#  (b) CELL ATTRIBUTION: a conversion counts only if the candidate strict-PASSES where the control
#      strict-failed on the same (task,rep) AND the row carries contour:v53_c_py_from_prompt at
#      identical ptok/calls (post-hoc code; any added model call on a converted row closes the stamp).
#  (c) GUARDS: zero v53 events in any control arm; ZERO v53 events outside C-ex6-02 (grammar
#      regression otherwise - close the stamp); ZERO candidate C-ex6-02 strict-fails where the
#      control passed; frozen-band parity (zero 2.30-32/34-config/36/38/41/42/44 fires - the frozen
#      2.41 C_RULE_GROUND must stay silent at 2.53); adopted-family parity within seed noise (v47
#      C-set trigger, v52 A chain, v51 B echo, v48 K enum, v243 loop draws, 2.39/2.40 J); stall
#      protocol (engine_stalled rows excluded, abort above 25% of last 20).
#  (d) RESOLUTION: 1 task x 3 seeds = 3 cells, cell-level by construction. The 77-cell mean with
#      the exact pooled sign test is context only; deltas under ~2 cells UNRESOLVABLE, never the
#      reason. ADOPT 0.0.2.53 iff (a) holds, >=1 evented conversion, and all guards clean. Otherwise
#      freeze C_PY_GROUND to STAMP_REVISION == (2, 53) and publish the negative with win-level detail.
# Energy per arm from gpu-power-p250.csv windows (per-arm -start.epoch/-end.epoch); the mechanism
# is zero-token by construction, extra Wh attributed only beyond run-to-run noise.
set -u
cd ~/parb-b66-contour || exit 1
for rep in 41 42 43; do
  plan=plan-rep${rep}.json
  for v in 52 53; do
    rid="v${v}r${rep}"
    date +%s > "${rid}-start.epoch"
    cp -f "$plan" plan.json
    PARB_ROOT=. PARB_API=http://<LAN_IP>:8080/v1/chat/completions \
      PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=p2005-profile.json \
      PARB_GATE_VERSION=0.0.2.$v PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
      PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
      PARB_RUN_NOTES="paired contour 0.0.2.${v} seed ${rep} on bank v6.6 (2.53 = C python-literal options: the prompt's own printed snippets executed by code over a closed AST allow-list, letter set re-derived, only the OTVET line touched, zero model tokens, control 0.0.2.52 = adopted line after pair-249; 2.30-2.34/2.36/2.38/2.41/2.42/2.44 frozen) " \
      python3 -u gate_run.py > "${rid}.log" 2>&1
    rc=$?
    date +%s > "${rid}-end.epoch"
    echo "$rid: exit=$rc rows=$(wc -l < "results-${rid}.jsonl" 2>/dev/null)" >> queue.log
  done
done
cp -f plan-rep43.json plan.json
echo "pair250 done" >> queue.log
