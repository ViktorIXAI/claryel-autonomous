# bank-probe-66 — contour no-new-loss legs p66r28/29/30 (rule ii): clean; scaffolding no longer needed

Workspace `~/parb-b66-contour` (built at `f19fac1` on bank v6.6, ws bank copy
`590503cf1701a6ce`, pins `WS-GENERATED.v66full.sha256`), stamp `0.0.2.50`
(behavior 2.48 — identical tooling to the published p64/p65 legs; contour claims
nothing), `PARB_SUBSET=H-ex6-01`, serial, idle endpoint (preflight prefill
1.7-3.7k tok/s, no empty completions; auth 200 via the exact launched key file).
Matched seeds: identical `plan_reps` rep rows 28/29/30 used by the published
p64r*/p65r* legs (seed table in the queue echoes inside each leg log).

Per frozen rule (ii) the pair CANNOT claim conversion: the v6.5 control legs
strict-pass 3/3 (zero live target — UNMEASURED-as-effect doctrine, pair-233/238/242/245
pattern). What this leg set certifies:

| leg | content | format_ok | strict | ptok | ctok | sec |
|---|---|---|---|---|---|---|
| p66r28 | 1.0 | True | PASS | 348 | 247 | 4.3 |
| p66r29 | 1.0 | True | PASS | 350 | 246 | 2.5 |
| p66r30 | 1.0 | True | PASS | 345 | 289 | 2.9 |

- No new strict losses vs p65r28/29/30 (3/3 PASS vs 3/3 PASS) and vs p64r28/29/30 (3/3).
- Run-record wiring PROVEN: `stack.contour_stamp=2.50`, `contour_behavior=2.48`,
  `bank_version=v6.6`, `bank_version_source=marker`, `bank_sha16=590503cf1701a6ce`,
  `harness_git_sha=f19fac140113...` — the v6.6 bank identity flows through the marker
  into every row without env help.
- Answer-bytes signature of the bank fix: `contour:v219_h_clear_claims` (the claims
  scaffolding disclosed in bank-probe-65) fired on **3/3 p65 legs** — the raw model
  filled `claims` and the contour cleared it — and on **0/3 p66 legs**, where the
  model's own answer already carries `claims: []`. On v6.6 the contour passes this
  cell WITHOUT the repair; the scaffolding stays in the harness (other H prompts still
  carry the inviting fragment — coverage limit published in the changelog).

Verdict: rule (ii) holds (no new losses, wiring live). Combined with fair-rows.md
rule (i) FAIR and verify PASS, rule (iii) promotes v6.6 to WORKING.
