#!/bin/bash
# Paired contour arms on bank v6.2 (ws bank copy d1e8d11df5840dcc): 0.0.2.47 (ADOPTED control line
# after pair-246, contour behavior 2.47) vs 0.0.2.48 (K FIELDS-GATE KEY SET FROM THE TASK'S OWN
# ENUMERATION). The bug is published in our own artifacts: `want_fields` scans the prompt for
# UPPERCASE tokens followed by a colon, and in a K prompt the only such tokens are the instruction's
# own example (`вида FIELD: значение`) plus a parenthetical value form - so K-ex6-03's required set
# was [FIELD, FREE_SHIPPING], the contour hint told the model to use the literal placeholder `FIELD`
# as a key, and the published line strict-fails that task 9/9 with code `missing` (content 0.25)
# while the prompt prints every value the gold needs. 2.48 replaces the required set with the
# fields the prompt enumerates on its `Поля:` line, ONLY when the old detection is
# placeholder-tainted. Reference never read; want_format (which decides whether the gate runs) is
# untouched, so the surface is closed: over all 77 bank-v6.2 prompts exactly one task reaches
# fields_gate.
# LIVE TARGET (published, before any t* row): 9/9 contour arms on v6.2 strict-fail K-ex6-03
# (cadence-246 q45r16/17/18 + pair-246 s46/s47 r19/20/21). SAME-SEED SMOKE (rep0, sp1 gseed, 11:32
# CET, outside the pair seeds): control 0.0.2.47 -> answer "FIELD: 200 кресел 'Oslo'\nFREE_SHIPPING:
# yes", gate:fields_ok, c=0.25 f=False; candidate 0.0.2.48 -> "ITEM: Oslo / QTY: 200 / LEAD_WEEKS:
# 14 / FREE_SHIPPING: yes", contour:v48_fields_enum_from_prompt:4 + gate:fields_ok, c=1.00 f=True,
# one model call on both sides. Wiring proof on identical bytes, NOT the verdict.
# PRE-REGISTERED RULE (REVIEW-INBOX 2026-11-07 11:33 CET - the verdict is decided ONLY by that text):
#  (a) LIVE TARGET: MEASURED iff >=1 control (t47) K-ex6-03 row strict-fails carrying a `missing`
#      code. Zero live target = UNMEASURED, never a pass.
#  (b) CELL ATTRIBUTION: a conversion counts only if the candidate strict-PASSES where the control
#      strict-failed on the same (task,rep) AND the row carries contour:v48_fields_enum_from_prompt:4.
#  (c) GUARDS: zero v48 events in a control arm; zero v48 events outside the four enumerating K
#      tasks (K-ex6-00..03) and never on a task whose required set did not change; ZERO candidate
#      K strict-fails where the control passed (the required set is the only changed path - such a
#      cell closes the stamp); frozen-band parity (zero 2.30-32/34/36/38/41/42/44 fires in either
#      arm); adopted-line parity (v34 C families, v47 set trigger, v243 loop draws, 2.39/2.40 J,
#      2.35 B event census identical within seed noise); stall protocol (engine_stalled rows
#      excluded, abort above 25% of the last 20).
#  (d) RESOLUTION: the target pool is 1 task x 3 seeds = 3 cells, so the verdict is CELL-LEVEL by
#      construction. The 77-cell arm mean is published with the exact pooled sign test as context
#      only; a delta under ~2 cells at three seeds is UNRESOLVABLE and never quoted as the reason.
#      ADOPT 0.0.2.48 iff (a) holds, >=1 evented conversion, and all guards clean. Otherwise freeze
#      K_FIELDS_ENUM to CONTOUR_REVISION == (2, 48) and publish the negative with win-level detail.
# Energy per arm from gpu-power-p247.csv windows (per-arm -start.epoch/-end.epoch), reported side
# by side; the mechanism costs at most the already-existing fields re-ask, so extra Wh is attributed
# only if on-target retries dominate the delta.
set -u
cd ~/parb-v62-contour || exit 1
for rep in 22 23 24; do
  plan=plan-rep${rep}.json
  for v in 47 48; do
    rid="t${v}r${rep}"
    date +%s > "${rid}-start.epoch"
    cp -f "$plan" plan.json
    PARB_ROOT=. PARB_API=http://<LAN_IP>:8080/v1/chat/completions \
      PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=p2005-profile.json \
      PARB_GATE_VERSION=0.0.2.$v PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
      PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
      PARB_RUN_NOTES="paired contour 0.0.2.${v} seed ${rep} on bank v6.2 (2.48 = K fields-gate key set from the task's own Поля enumeration, replacing the placeholder-tainted FIELD set, one re-ask max; control 0.0.2.47 = adopted line after pair-246; 2.30-2.34/2.36/2.38/2.41/2.42/2.44 frozen) " \
      python3 -u gate_run.py > "${rid}.log" 2>&1
    rc=$?
    date +%s > "${rid}-end.epoch"
    echo "$rid: exit=$rc rows=$(wc -l < "results-${rid}.jsonl" 2>/dev/null)" >> queue.log
  done
done
cp -f plan-rep24.json plan.json
echo "pair247 done" >> queue.log
