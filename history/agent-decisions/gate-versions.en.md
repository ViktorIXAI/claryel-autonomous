# Contour versions: what was measured and decided

English translation of the agent's decision log
(`gate-versions.log`, Russian original preserved verbatim in the release
asset `ru-source-records-2026-11-01.tar.zst`, indexed in `logs/INDEX.md`).
A/B runs on Mac Studio: same tasks, same seeds.

v1.2 (comparison baseline): B2003 strict 73% / mean 89%, format 91%,
1230 tok/task; Mac 69% / 82%, format 94%, 1473 tok.
v1.3 (format priority + KEY: field gate): format 100% on both boxes,
H 52% -> 100%, mean 92-95%; price rose: 1926 tok/task (B2003), 2094 (Mac).
Format repairs and the retry ladder cost ~35-37% extra tokens.

v1.4 (cheap repair: format fix without the source document, previous answer
only): REJECTED.
  A/B subset B-ea-00-0, J-ea-00-0, K-ea-00-0 x 19 reps, Mac Studio:
    v1.3: correct 19/19, input 1088 tok/task, output 6119 total, 103.6 s, 29 repairs
    v1.4: correct  3/19, input  450 tok/task, output 3181 total,  59.1 s, 16 repairs
  Verdict: input tokens -59% and time -43% at the cost of 16 lost correct
  answers out of 19.
  CAUSE (refined after v1.5): v1.4 bundled two changes at once — (1) format
  repair without the source document and (2) limiting repair attempts to one.
  The cheap repair never even ran in that code: msgs0 in the contour does not
  contain the model answer, so the "without document" branch never fired.
  What actually broke was the attempt cap: repairs dropped 29 -> 16, and
  unfinished format gave missing_7 and wrong numbers. Lesson: format-repair
  attempts must not be capped at one; save money some other way.

v1.5 (cheap repair under a guard): decision to compare against v1.3. Guard:
before accepting a cheap repair, the answer skeleton (number of data rows and
key set) is compared; if rows or keys decreased, the cheap variant is
rejected (event gate:cheap_repair_rejected) and the call repeats with full
context. Format-repair attempt count returned to 2.
  Result on A/B: IDENTICAL to v1.3 (1089 tok/task, 19/19 correct, 0 guard
  firings). Reason: the cheap branch never executed — msgs0 does not contain
  the previous model answer. So v1.5 = v1.3 in effect; the guard was never
  battle-tested.

v1.6: the previous answer is passed into ask_repair as an explicit argument
prev=r["text"] in all three repairs (json_gate, format_gate, fields_gate).
Only now does the cheap repair become reachable code and the guard start
rejecting something. A/B v1.3 vs v1.6 — next measurement (subset B-ea-00-0,
J-ea-00-0, K-ea-00-0).
  A/B subset, Mac Studio:
    v1.3: correct 19/19, mean 100%, input 1088 tok/task, output 6119, 103.2 s, 29 repairs
    v1.6: correct 16/19, mean  96%, input  595 tok/task, output 6561, 104.6 s, 16 repairs
  Verdict: input tokens -45%, but 3 correct answers lost out of 19; the guard
  rejected no repair (the skeleton stayed intact, the VALUES broke). Not
  accepted for financial tasks.

v1.7 (code fixes form; the model is not called): gates first try to restore
formatting themselves (cut text around JSON/CSV, drop trailing commas,
True/False, quote keys, extract KEY: fields from prose). Data is never
invented: if rows or keys are missing — refuse and take the normal path.
Offline fixer test: 12 cases including refusals.
  ADOPTED as the working version. A/B on Mac, same task set, 19 records per
  arm:
    v1.3: correct 19/19, mean 100%, input 1088 tok/task, output 6119, 103.4 s, 29 repairs
    v1.7: correct 19/19, mean 100%, input  746 tok/task, output 4637,  83.8 s, 16 repairs
  Savings: input -31%, generation -24%, time -19%, model calls spent on
  form -45%. Quality did not drop on a single task.
  Important side finding: arm ab17 (v1.7 plus the cheap MODEL repair) gave
  16/19. So what is harmful is the cheap model-based repair without the input
  document, not code repair. Therefore PARB_CHEAP now defaults to 0 (off),
  enabled only for experiments.

v1.7 in-flight snapshot 2026-10-31 12:05 (ledger field 'content' = score):
  B2003 n=120 avg=0.96 exact=81% format_ok=100% in=1620 out=391 tok/task 7.2 s/task code_fixes=31 blocks=0
  mac-studio n=247 avg=0.92 exact=72% format_ok=97% in=1222 out=223 tok/task 3.9 s/task code_fixes=50 blocks=0
  finance B+C: B2003 60/61 exact (98%), mac 69/69 (100%); cost per correct answer B2003 1729 in + 606 out, 8.7 s; mac 1518 in + 471 out, 6.7 s
  weak spots: F 0.67-0.83, G 0.83, D 0.70 (mac), H 0.70 (mac)

(2026-10-31 third browser benchmark — voxel pagoda, B2003: already recorded
in English in the original log: framing beats prohibitions for this quant;
5/5 with deliverable-first framing; validation by CDN-snapshot sha256; page
code never edited. See the archived original for the full block, mirrored in
`history/timeline.md`.)

v1.7 FINAL (2026-10-31):
B2003: n=787 (reps 0-206), score 0.897, perfect 77%, format_ok 93%
Mac  : n=1321 (reps 0-256), score 0.887, perfect 69%, format_ok 93%
paired 717: both-perfect 536 (75%), disagree 58 (avg delta 0.50)
weak cats: D=0.53-0.63, F~0.68, H/B2003=0.65, K/Mac=0.83
top failure notes: too_few_safe_steps, q5_contradiction_missed,
no_final_answer, format, cause_not_named, bad_negation_kept

v1.8 start (2026-10-31 16:53): targeted contour nudge per scorer remark
(fired/adopted counted separately); in the D-loop an answer before
read/plan is rejected (blocked_early_answer); plan: B2003 to rep506 (3153),
Mac to rep1006 (9753); run from rep0 — direct paired v1.7/v1.8 comparison on
the same tasks. Smoke: nudges fire (calls=2); on easy tasks adoption=0 —
price is 1 extra call; waiting for hard categories. In parallel the visual
contour contour1 launched: prompts frozen, fixers (importmap/addons/prose)
+ retries, B2003 endpoint.

(Visual contour contour1/contour2 blocks were written in English in the
original; key lines: balls 4/5, pel 5/5, pgp 2/5 under contour1 and 5/5
under contour2 — the jump from single-shot 1/5 to contour2 5/5.)

2026-11-01 v1.9 D-order normalization: smoke P2005 fixed D-ea-00-0 from 0.33
CHRONIC to 1.00 x3 via contour:v19_d_order_to_steps. Full paired runs
launched: B2003 results-v19.jsonl (plan trimmed to 3117 v1.8 keys) and Mac
results-v19m.jsonl (trimmed to 2513 v1.8 keys), limit 21600.

v1.9 PROBE (P2005, 22 weak tasks x3 reps 9001-9003, 2026-11-01 03:05):
D-ea-00-0 FIXED: v18p 0.33x3 -> v19p 1.00x3, contour fired 3/3.
CHRONIC: F-ha-01-0 (0.67 all 6 reps, too_few_safe_notes persistent).
LOTTERY (spread carried from v18p): G-me-04, H-ha-04-0, J-me-00-0, K-ha-04-0
— v19 reps stable-high. REGRESSED: none. F-ha-02: cause_not_named persists
on all reps both versions (0.611->0.722). Main boxes partial: B2003 n=108
running, Mac n=121 running, no D yet; paired v18->v19 delta -0.006/+0.000.
Next: v2.0 leave D alone; best-of-N targets the LOTTERY four; F-ha-01 needs
a structural check (step deficit, not keyword-only).
v1.9 calc probe: raw no-contour baseline was 4/200 strict (2%), avg 7.5%,
format 2%, 84 truncated. Fresh P2005 calc probe v1.9: 16 A tasks x3 reps =
48 records, 48/48 strict, format 100%, avg 4.07 s/task, model_calls 1.67.
Current paired v1.9 A: B2003 295/295 strict; Mac 347/347 strict. The 2% raw
calculation line is raised to 100% by money+code contour, not prompt change.

v1.9 MORNING (2026-11-01 07:30): B2003 running (1922/3117 pairs). Mac
stopped ~06:17 (box rebooted) at 2416/2513 pairs, no completion marker, no
traceback — not restarted per operator instruction.
Verdict: v1.9 BETTER on both boxes. B2003 avg 0.880->0.934 (paired +0.047,
210up/74down), Mac 0.875->0.926 (+0.050, 183up/0down). D category
0.42/0.44 -> 1.00 both. D-ea-00-0 FIXED: 121/121 + 162/162 perfect,
contour:v19_d_order_to_steps fired 142/183, order_ok 1:1.
Nudge economy: v1.8 nudges B2003 fired 480 adopted 116 (24%), Mac fired 668
adopted 18 (2.7%); v1.9 fix is mechanical, zero extra calls.
P2005 probe: FIXED D-ea-00-0; CHRONIC F-ha-01-0 (0.67 x6), F-ha-02-0
cause_not_named persists (0.61->0.72); LOTTERY G-me-04, H-ha-04-0, J-me-00-0,
K-ha-04-0; REGRESSED none. calc A: raw 2% -> v19 48/48 100%.
Visual: contour2 production pgp 5/5, balls 4/5 (seed3 fail x3), pel 5/5.

2026-11-01 07:58 v2.0 build:
- one contour change: POST_NORMALIZE for G/H only. G: if q5 already names two
  values but lacks an explicit contradiction word, mechanically label it
  "Contradiction:". H: if the answer is semantically accepted but >600 chars,
  deterministic short summary preserving uncertainty and numeric values; also
  applied after v1.8 nudge replacement.
- local tests: gate_fixers 12/12; gate_v19 D 4/4; gate_v20 post 11/11.
- P2005 targeted v1.9 vs v2.0 (6 tasks x3 reps): avg 0.787 -> 0.815 (+0.028),
  perfect 5 -> 13, format 17 -> 16; better=9 worse=3 same=6. G avg
  0.852 -> 0.907 (+0.055). H avg unchanged; H-ha-04-0 5-rep reprobe after
  nudge-post-normalize fix gave content 5/5 and format 5/5.
- Mac full v2.0 launched on the same trimmed subset (2513 keys),
  state-v20m/results-v20m/gate-ledger-v20m. B2003 v2.0 deployed but NOT
  launched while v1.9 still runs, to avoid same-endpoint contamination.
- speed cost B2003 raw vs v1.9: raw decode median 69.7 tok/s, v1.9 raw decode
  median 48.4 (-30%); generated tokens per wall-second 47.4 -> 11.4 effective
  (-76%); consumed throughput 124.3 -> 78.2 tok/s (-37%). Per-task cost
  varies: A faster (8.3 s -> 5.8 s), D/E/J/I/K faster, B/F/H slower and more
  expensive.
