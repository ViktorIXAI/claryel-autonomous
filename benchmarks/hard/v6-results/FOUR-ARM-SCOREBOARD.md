COMMON SET (single-shot): 71 tasks
arm        strict  content
contour     43/71     48/71 
basalt      49/71     49/71 
codex       49/71     49/71 
grok        59/71     59/71 

CONTOUR-ONLY loop tasks (6): strict 1/6 mean 0.625

McNemar exact (strict, paired on common set):
  contour  vs basalt  : +6/-12  p=0.2379  (n=71)
  grok     vs codex   : +11/-1  p=0.0063  (n=71)
  grok     vs contour : +17/-1  p=0.0001  (n=71)
  codex    vs basalt  : +2/-2  p=1.0000  (n=71)
  grok     vs basalt  : +11/-1  p=0.0063  (n=71)
  contour  vs codex   : +5/-11  p=0.2101  (n=71)

Per-category strict on common set:
cat   contour   basalt    codex     grok
A        5/9       7/9       7/9       6/9  
B        2/7       7/7       6/7       7/7  
C        6/8       5/8       5/8       6/8  
D        3/3       3/3       3/3       3/3  
E       10/10      9/10     10/10     10/10 
F        2/6       1/6       0/6       5/6  
G        5/6       5/6       5/6       5/6  
H        3/5       0/5       1/5       3/5  
I        5/6       6/6       6/6       6/6  
J        1/7       5/7       5/7       6/7  
K        1/4       1/4       1/4       2/4  

---

## contour 0.0.2.17 re-draw (2026-11-05 20:49-21:04 CET), hard bank v6

The `contour` row above is the published **0.0.2.14** arm. Since then two contour fixes
landed, both measurement-validity bugs in the contour's own driver, each with a paired
same-seed measurement:

| change | paired arms (identical seeds, one rep) | effect |
|---|---|---|
| 0.0.2.16 loop-v2 drive (re-ask instead of abort, in-place `gate_rejected`, salvage the model's own answer) | loop-only 2.15 vs 2.16 | loop-D strict **1/6 -> 5/6** (4W/0L/2T, exact sign p=0.125, directional) |
| 0.0.2.17 format repair unbundled from `CHECKER_INJECT` | full bank 2.16 vs 2.17 | plain strict **39/71 -> 41/71**; B **2->5**, J **0->3**; 6/6 targeted format-only cells recovered, 0 broken by the repair |

Latest contour full-bank arm (0.0.2.17, rep0): plain **41/71**, loop **4/6**. Per-category
strict incl. loop: A 4/9, B 5/7, C 5/8, D 4/9, E 10/10, F 2/6, G 5/6, H 1/5, I 5/6, J 3/7,
K 1/4. Artifacts: `full-217/` (results, ledgers, log, `PAIR-217.md`, `pair-216-217.txt`),
loop artifacts in `loopd-216/`.

Cross-arm comparability note: the 43/71 (0.0.2.14) and 41/71 (0.0.2.17) contour rows are
different arms on the same seeds; the local serve is seeded but not bit-reproducible, so a
+-4 cell spread on 71 tasks is within resample noise. A fresh four-arm comparison at 2.17
(neighbours unchanged) is needed before restating the contour-vs-raw verdict.
Evidence, not verdict: the two fixes above are deterministic driver fixes with mechanism-level
proof (contour events in ledgers, 6/6 targeted flips), not a claim that the contour now
beats the raw arms.


## 2026-11-05 corrected rescore (same answer bytes, frozen checker)

`scripts/rescore_v6_cells.py` re-scored every published contour arm on its stored answer
bytes. Contour stamps before 0.0.2.21 scored the three plain-D tasks (`D-ex6-p0/p1/p2`)
through the loop trajectory scorer: all three were scored 0 in every one of those arms, all
three pass under `check_D_plain_v6`. Corrected plain totals:

| stamp | 0.0.2.16 | 0.0.2.17 | 0.0.2.18 | 0.0.2.19 | 0.0.2.20 | 0.0.2.21 | 0.0.2.22 | 0.0.2.23 |
|---|---|---|---|---|---|---|---|---|
| as-run | 39 | 41 | 45 | 47 | 47 | 50 | 54 | 52 |
| corrected | 42 | 44 | 48 | 50 | 50 | 50 | 54 | 52 |

Consequences, stated carefully:
- The as-run +3 at 0.0.2.21 was scoring validity, not a model gain (corrected delta 0).
- The corrected independent check agrees: corrected 0.0.2.17 = 44/71 matches the external
  rescore in `CROSSCHECK-217.md` (their scorer, our published bytes).
- On this bank at rep1 the contour line's best corrected draw is **54/71** (0.0.2.22) against
  raw arms grok 59, codex 49, basalt 49. Single rep each, contention documented in each
  writeup: contour is above the two basalt-class raw arms and below grok, and a fresh
  four-arm comparison at the current stamp is still owed before that becomes a verdict.
