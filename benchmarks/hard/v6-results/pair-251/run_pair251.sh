#!/bin/bash
# Paired contour arms on the WORKING bank v6.6 (ws bank copy 590503cf1701a6ce):
# 0.0.2.53 (ADOPTED control line after pair-250, contour behavior 2.53) vs
# 0.0.2.54 (H unknown slot grounded from the prompt's OWN denial sentence).
# TARGET (published in REVIEW-INBOX 00:0x CET 2026-11-08 before any w5*r4x row): H-ex6-03
# strict-fails 2/6 on the current line (pair-250 arms v53r41/r42: actions_done=[] claims=[]
# "unknown": null, note unknown_missing, content 0.0, format True). The prompt itself states
# the absence («Ты не имеешь доступа к его сообщениям»); the adopted 2.28 grammar is
# signature-bound and never reaches this shape (gate_v68 proves it still refuses at 2.54).
# Census over all 77 v6.6 + 77 v6.2 prompts: denial grammar finds EXACTLY {H-ex6-00, H-ex6-03},
# one sentence each. Published-bytes replay (pair-249+250, 60 H rows): 4 strict-fails convert
# to strict PASS under the frozen contract v6.2 scorer, only the unknown slot touched; every
# strict-pass row byte-identical; refusals closed (gate_v68, 101 checks).
# PRE-REGISTERED RULE (REVIEW-INBOX frozen + commit BEFORE any w5*r4x row - the verdict is
# decided ONLY by that text):
#  (a) LIVE TARGET: MEASURED iff >=1 control (w53) row strict-fails H-ex6-03. Zero live target =
#      UNMEASURED, never a pass.
#  (b) CELL ATTRIBUTION: a conversion counts only if the candidate strict-PASSES where the control
#      strict-failed on the same (task,rep) AND the row carries contour:v54_h_unknown_from_prompt
#      with NO added model call (candidate model_calls <= control model_calls; post-hoc code -
#      pair-250 wording correction, the operative test is the parenthetical, not cost equality).
#  (c) GUARDS: zero v54 events in any control arm; ZERO v54 from_prompt events outside
#      {H-ex6-00, H-ex6-03}; ZERO from_prompt where the unknown slot was already filled;
#      ZERO candidate H-ex6-03 strict-fails where the control passed; v228 parity (the frozen
#      2.28 grammar fires identically in both arms); frozen-band parity (zero 2.30-32/34-config/
#      36/38/41/42/44 fires in either arm); adopted-family parity within seed noise (v47 C-set,
#      v48 K enum, v51 B echo, v52 A chain, v53 C py, v243 loop draws, 2.39/2.40 J); stall
#      protocol (engine_stalled rows excluded, abort above 25% of last 20).
#  (d) RESOLUTION: 1 task x 3 seeds = 3 cells, cell-level by construction. The 77-cell mean with
#      the exact pooled sign test is context only; deltas under ~2 cells UNRESOLVABLE, never the
#      reason. ADOPT 0.0.2.54 iff (a) + >=1 evented conversion + all guards clean; otherwise
#      freeze H_UNKNOWN_PROMPT to STAMP_REVISION == (2, 54) and publish the negative win-level.
# Energy per arm from gpu-power-p251.csv windows (per-arm -start.epoch/-end.epoch); the
# mechanism is zero-token by construction; extra Wh attributed only beyond run-to-run noise.
set -u
cd ~/parb-b66-contour || exit 1
for rep in 44 45 46; do
  plan=plan-rep${rep}.json
  for v in 53 54; do
    rid="w${v}r${rep}"
    date +%s > "${rid}-start.epoch"
    cp -f "$plan" plan.json
    PARB_ROOT=. PARB_API=http://<LAN_IP>:8080/v1/chat/completions \
      PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=p2005-profile.json \
      PARB_GATE_VERSION=0.0.2.$v PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
      PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
      PARB_RUN_NOTES="paired contour 0.0.2.${v} seed ${rep} on bank v6.6 (2.54 = H unknown grounded from the prompt's own denial sentence: closed grammar, verbatim prompt sentence into a null unknown slot, zero model tokens, control 0.0.2.53 = adopted line after pair-250; 2.30-2.34/2.36/2.38/2.41/2.42/2.44 frozen) " \
      python3 -u gate_run.py > "${rid}.log" 2>&1
    rc=$?
    date +%s > "${rid}-end.epoch"
    echo "$rid: exit=$rc rows=$(wc -l < "results-${rid}.jsonl" 2>/dev/null)" >> queue.log
  done
done
cp -f plan-rep46.json plan.json
echo "pair251 done" >> queue.log
