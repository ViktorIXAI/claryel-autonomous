#!/bin/bash
# Paired contour arms on bank v6.2 (ws bank copy d1e8d11df5840dcc): 0.0.2.48 (ADOPTED control line
# after pair-247, contour behavior 2.48) vs 0.0.2.51 (B ECHO RESTORE re-armed). Pair-234 built this
# repair and froze it UNMEASURED at exactly (2,34): that revision's echo guard refused any answer
# adding the declared count key, so all three candidate seeds fired ZERO times. The guard was
# extended right after (drop-names + count-key tolerance) but the flag stayed frozen - no published
# arm ever ran the current echo bytes. The class is now live ON THE ADOPTED LINE ITSELF:
# B-ex6-05 strict-fails 2/3 at t48r22/23/24 (published in PAIR-247-V62.md artifacts), every zero
# the same mode - the model copies `items` but injects its own per-item `n_tags`, violating the
# prompt's «Items не меняй», scored fields_mismatch:items. The echo grammar rebuilds the answer
# from the prompt's own JSON literal (items verbatim, count recomputed, drop applied), zero model
# tokens, reference never read; refuses on every uncertainty; coverage census over all 77 v6.2
# prompts: the grammar matches EXACTLY one task (B-ex6-05). Event: contour:v51_b_echo_restore.
# LIVE TARGET (published, before any u* row): >=1 control u48 strict-fail of B-ex6-05 at reps
# 34/35/36 (measured base rate 2/3 on t48; rep0 smoke 20:29 CET showed the no-op branch clean on
# identical bytes - repair fired ZERO times where the answer was already prompt-equal, both arms).
# PRE-REGISTERED RULE (REVIEW-INBOX 2026-11-07 20:28 CET - the verdict is decided ONLY by that text):
#  (a) LIVE TARGET: MEASURED iff >=1 control (u48) row strict-fails B-ex6-05. Zero live target =
#      UNMEASURED, never a pass.
#  (b) CELL ATTRIBUTION: a conversion counts only if the candidate strict-PASSES where the control
#      strict-failed on the same (task,rep) AND the row carries contour:v51_b_echo_restore.
#  (c) GUARDS: zero v51 events in any control arm; ZERO v51 events outside B-ex6-05 (grammar cannot
#      match elsewhere - a fire there = grammar regression, close the stamp); ZERO candidate
#      B-ex6-05 strict-fails where the control passed (the repair only rewrites non-equal answers);
#      non-target flips event-less and within the published noise floor; frozen-band parity (zero
#      2.30-32/34-config/36/38/41/42/44 fires in either arm); adopted-line parity (v34 C families,
#      v47 set trigger, v48 K enum, v243 loop draws, 2.39/2.40 J, 2.35 B event census identical
#      within seed noise); stall protocol (engine_stalled rows excluded, abort above 25% of last 20).
#  (d) RESOLUTION: the target pool is 1 task x 3 seeds = 3 cells, so the verdict is CELL-LEVEL by
#      construction. The 77-cell arm mean is published with the exact pooled sign test as context
#      only; a delta under ~2 cells at three seeds is UNRESOLVABLE and never quoted as the reason.
#      ADOPT 0.0.2.51 iff (a) holds, >=1 evented conversion, and all guards clean. Otherwise freeze
#      B_ECHO_RESTORE to STAMP_REVISION == (2, 51) and publish the negative with win-level detail.
# Energy per arm from gpu-power-p248.csv windows (per-arm -start.epoch/-end.epoch), side by side;
# the mechanism is zero-token by construction, extra Wh attributed only beyond run-to-run noise.
set -u
cd ~/parb-v62-contour || exit 1
for rep in 34 35 36; do
  plan=plan-rep${rep}.json
  for v in 48 51; do
    rid="u${v}r${rep}"
    date +%s > "${rid}-start.epoch"
    cp -f "$plan" plan.json
    PARB_ROOT=. PARB_API=http://<LAN_IP>:8080/v1/chat/completions \
      PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=p2005-profile.json \
      PARB_GATE_VERSION=0.0.2.$v PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
      PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
      PARB_RUN_NOTES="paired contour 0.0.2.${v} seed ${rep} on bank v6.2 (2.51 = B echo restore re-armed: items rebuilt verbatim from the prompt's own JSON literal, count recomputed, declared drop applied, zero model tokens, control 0.0.2.48 = adopted line after pair-247; 2.30-2.34/2.36/2.38/2.41/2.42/2.44 frozen) " \
      python3 -u gate_run.py > "${rid}.log" 2>&1
    rc=$?
    date +%s > "${rid}-end.epoch"
    echo "$rid: exit=$rc rows=$(wc -l < "results-${rid}.jsonl" 2>/dev/null)" >> queue.log
  done
done
cp -f plan-rep36.json plan.json
echo "pair248 done" >> queue.log
