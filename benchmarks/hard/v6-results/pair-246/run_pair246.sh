#!/bin/bash
# Paired contour arms on bank v6.2 (ws bank copy d1e8d11df5840dcc): 0.0.2.46 (ADOPTED control
# line, contour behavior 2.44, pair-245) vs 0.0.2.47 (C best-of-2 SECOND TRIGGER on the
# `set_mismatch` note family: the frozen v6.2 C scorer never emits missed_options for C, so the
# adopted 2.13 trigger has a live coverage gap; one extra draw at seed+17491 - distinct from C
# 5309 and D 4096/8117/12289 - adopted only if strictly better; monotone, it can only fire on
# rows the C scorer already failed; missed_options keeps precedence; exactly one C retry/task;
# call site cat==C only).
# Target class (published): cadence-246 line map - C-ex6-02 strict-fails 3/3 on the adopted line
# with set_mismatch (content 0.0, format_ok true, model's own verdicts omit B). PRE-LAUNCH
# DRY-RUN on published cadence bytes: 24 contour C rows, 5 carry set_mismatch, ALL strict-fail,
# ZERO v34 fires on them - gap live before any s* row.
# PRE-REGISTERED RULE (REVIEW-INBOX 2026-11-07 10:04 CET - the verdict is decided ONLY by this text):
#  (a) LIVE TARGET: MEASURED iff >=1 control (s46) C row carries a set_mismatch note AND
#      strict-fails. Zero live target = UNMEASURED, never a pass.
#  (b) CELL ATTRIBUTION: a conversion counts only if the candidate strict-PASSES where the
#      control strict-failed on the same (task,rep) and the row carries fix:v47_c_best2_set_win
#      plus contour:v47_c_best2_set_fired, and the set_mismatch note is ABSENT from the winner.
#  (c) GUARDS: ZERO candidate C strict-fails where the control passed (monotonicity broken in
#      CODE - close the stamp); zero v47 events outside cat==C or in the control arms; zero
#      frozen-band events (2.30-32/34/36/38/41/42/44 fires absent); adopted-line parity (v34
#      missed_options family, v243 banned-only draws, 2.39/2.40 J fires, 2.35 B repair identical
#      across arms); stall protocol: engine_stalled rows excluded, abort >25% of last 20.
#  (d) RESOLUTION: per-cell flips + exact sign test over 231 C-pool-adjacent cells published; an
#      arm-mean delta under ~2 cells at three seeds is UNRESOLVABLE and never quoted as the
#      reason; candidate not >2 cells below control on the 77-cell pool. ADOPT 0.0.2.47 iff
#      (a) holds, >=1 evented conversion, all guards clean. Otherwise freeze C_BEST2_SET to
#      CONTOUR_REVISION == (2,47) and publish the negative with the same detail as a win.
set -u
cd ~/parb-v62-contour || exit 1
for rep in 19 20 21; do
  plan=plan-rep${rep}.json
  for v in 46 47; do
    rid="s${v}r${rep}"
    date +%s > "${rid}-start.epoch"
    cp -f "$plan" plan.json
    PARB_ROOT=. PARB_API=http://<LAN_IP>:<PORT>/v1/chat/completions \
      PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=p2005-profile.json \
      PARB_GATE_VERSION=0.0.2.$v PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
      PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
      PARB_RUN_NOTES="paired contour 0.0.2.${v} seed ${rep} on bank v6.2 (2.47 = C best-of-2 second trigger on set_mismatch, one retry at seed+17491, strict-better only; control 0.0.2.46 = adopted behavior 2.44 line; 2.30-2.34/2.36/2.38/2.41/2.42 frozen) " \
      python3 -u gate_run.py > "${rid}.log" 2>&1
    rc=$?
    date +%s > "${rid}-end.epoch"
    echo "$rid: exit=$rc rows=$(wc -l < "results-${rid}.jsonl" 2>/dev/null)" >> queue.log
  done
done
cp -f plan-rep21.json plan.json
echo "pair246 done" >> queue.log
