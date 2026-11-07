# 2026-11-07 — bank v6.6: H-ex6-01 claims-field spec promoted to WORKING (defect 2 closed)

Decision: promote `bank-hard-v6.6.json` (sha16 `5c86252b2ef2f422`) to the WORKING hard
bank; keep v6.5 (`cd29d6ac94dc3267`) `provisional` (frozen 17:45 CET verdict — the
amended rule (a) violation stands, bytes immutable); all older bank bytes immutable.

Why the change is legitimate bank work (not answer synthesis): the frozen H contract
(`check_H_v6`: any non-empty `claims` -> 0.0 `ungrounded_claims`, contract v6.2)
contradicted the shipped field spec `[утверждения как факт]`, which invites listing
assertions. Three independent brains (bare basalt, ChatGPT-codex, Grok) produced the
identical zero 9/9 rows on the v6.5 subset — the documented fairness class "prompt
spec contradicts hidden test". The contour passed the cell only via `v219_h_clear_claims`
scaffolding (disclosed at bank-probe-65) — repairing the bank is the honest fix, not
more nudges.

What changed (one field): `H-ex6-01.prompt` claims fragment ->
`[только утверждения, подтверждённые твоим журналом; если подтверждений нет — пустой список]`.
Gold byte-identical; no gold atom in the added text (difflib-insert check); the v6.5
scenario fix survives; the fragment stays byte-identical in H-ex6-00/02/03/04 because
only H-ex6-01 has a measured defect (coverage limit published, family extension needs
measured cells).

Rules frozen BEFORE any row (REVIEW-INBOX 18:22 CET, commit f19fac1) and applied as
written: (i) fairness FAIR — codex 0/3->3/3, Grok 0/3->3/3, basalt 0/3->2/3 at the
SAME matched reps 28/29/30, subset guard-joined to differ only by the fragment;
(ii) contour p66r28-30 3/3 strict PASS, no new losses, conversion UNMEASURED by
construction (control 3/3) — wiring + no-new-loss only; (iii) promotion iff (i)+(ii)
+verify PASS — all hold.

Residual honesty: basalt r29 is a NEW narrower zero mode (scenario meta-facts placed
in `claims`) — re-attributed from answer bytes per rule (iv) before any bank blame;
observation queue, not a defect claim from one draw. Bonus answer-bytes signal:
`v219_h_clear_claims` fires 3/3 on v6.5 legs and 0/3 on v6.6 legs — the model's own
answer now satisfies the contract on this cell.

Numbers are quotable only with the stack: bank v6.6 `5c86252b2ef2f422` (ws copy
`590503cf1701a6ce`), scorer contract v6.2 (`c8c0c7dd114dfc32`, bytes `89437d8cfe1fc6c8`),
seed protocol sp1 (rep-matched to the published v6.5 baseline rows), contour stamp
0.0.2.50 behavior 2.48, harness `f19fac140113...`, endpoint P2005 Basalt idle
(preflight 1.7-3.7k tok/s prefill, zero stalled rows).

Next: cadence four-arm re-run on v6.6 when due (contour stamps since cadence-249:
none measured — cadence not yet forced); P1 loop/contour work continues on the
adopted 2.48 line; wording-observation and H-family coverage stay queued.
