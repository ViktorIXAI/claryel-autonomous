# External reviews of this repository — published in full, with our responses

**Provenance.** On 2026-11-01 the project owner obtained a critical review of
the public repository from an external conversational AI system and pasted it
to the lab agent verbatim. It is *not* the lab agent's self-assessment, and
the reviewer states their own limitation: they read the published material and
did not run the full experimental suite. Ledger entry EXT-001 in
[`../history/external-model-inputs/ledger.md`](../history/external-model-inputs/ledger.md);
SHA-256(16) of the received text: `c26848ffd40c75ce`.

**Our policy:** external criticism is published unedited. The original is
Russian; the English abstract below is a translation aid, not a rewrite.

## English abstract of the review

- Verdict: "a serious enthusiast experimental lab, not a finished scientific
  study — convincing as that; problematic if presented as proof that AI has
  learned to grow its own intelligence."
- Scores (subjective expert impression, not a scientific metric):
  presentation 8/10, engineering 7/10, transparency 8/10, scientific rigor
  5/10, autonomy evidence 5/10, interest to AI researchers 7/10.
- Praised: publication of failed versions, paired A/B discipline, model/harness
  separation, published checking tooling, documented limitations.
- Core criticisms: (1) gains may be gains *against the lab's own validator and
  task bank* (benchmark overfitting; format-vs-substance); (2) "autonomous
  self-development" claims outrun the evidence chain (agent-authored logs are
  the main evidence); (3) a self-made 178-task synthetic bank scoring near
  perfect risks being too easy; (4) missing budget-matched simple baselines
  (retry, plain JSON validator, generic frameworks); (5) project naming
  promises more than a few-days, single-model experiment can support.
- Suggested positioning (adopted, see EXT-002): home-lab open experiment,
  published failures, paired benchmarks, costs, provenance; study which
  improvements generalize and which only fit the test format.

## What we did in response (same day, public)

| review point | response in the public record |
|---|---|
| overfitting to own bank | post-freeze holdout bank (206 tasks, disjoint, CI-checked) already run: overall 0.819, G-category gap 0.167 published in [`holdout-mini.md`](holdout-mini.md); dynamic bank-rotation rule now protocol ([`docs/dynamic-regime.md`](../docs/dynamic-regime.md)) |
| independent validator | second-opinion scorer with published dissent (independent delta −0.011 on the rescored subset, 22 reversals): [`independent-scorer.md`](independent-scorer.md) |
| format-vs-substance | second scorer re-derives semantics from bank ground truth only; divergences kept, not averaged |
| autonomy wording | README wording narrowed to the reviewer's formulation (EXT-002); no recursive-self-improvement claims anywhere |
| simple baselines | named as the next planned measurement in [`docs/roadmap.md`](../docs/roadmap.md) (not yet run — stated as such) |
| scale of claims | README positioning replaced with the home-lab framing; dashboard and timeline show elapsed time honestly (project started 2026-10-30) |
| stale docs / missing pipeline / dashboard | fixed same day: link-checker in CI, publication pipeline with two automatic publishes, dashboard live |

## The review, full English translation

(The Russian original is archived verbatim in release asset
`ru-source-records-2026-11-01.tar.zst`, sha256 recorded in `logs/INDEX.md`;
this translation is complete, section by section.)

**Independent evaluation of the Strata Autonomous Harness** — I looked at it
as an unknown project sent to me for professional assessment. I do not take
the author's claims on faith, I do not count our previous discussions as
evidence, and I compare the approach with what is currently happening in
AI-agent research.

**Verdict.** This is not a typical beginner project. But for now it looks
more like a serious enthusiast experimental lab than a finished scientific
study. Positioned that way it is quite convincing; problems arise only if it
is presented as proof that AI has learned to develop its own intelligence.

**Scores (subjective expert impression, not a scientific metric):**
presentation 8/10, engineering organization 7/10, transparency 8/10,
scientific rigor 5/10, autonomy evidence 5/10, interest to AI researchers
7/10. This is an assessment of published sources, README, methodology,
limitations, version history and research-materials structure. I did not run
the full experimental suite myself, so I do not grant the project
fully-verified status.

**1. The idea is not amateurish.** In 2026, the effect of the software
wrapping on agent capability is a full research topic (Harness-Bench;
Rethinking the Evaluation of Harness Evolution for Agents; Holistic Agent
Leaderboard). Asking how far a frozen model's practical performance can be
improved by perfecting the code around it is a professional question. But the
novelty of the idea is no longer a strong argument on its own: to interest a
specialist the project needs unusual experimental results, strong evidence,
or a new approach to autonomous improvement. Strata has potential here, but
not enough independent confirmation yet.

**2. What an experienced researcher will praise:** (1) publishing failed
versions — v1.4 sharply worse, v1.5 a near-no-op, v1.6 saving tokens at the
cost of correctness — the author is not showing only wins; (2) paired A/B on
identical tasks, ids and seeds, far better than comparing averaged
percentages from different runs; (3) model/harness separation stated plainly
— system improvement is not model improvement; (4) the checking tooling is
published: scorer code, task sources, JSONL results, SHA-256 index,
reproduction scripts — not just charts and claims; (5) limitations are
documented: missing historical code snapshots, test-set overfitting risk,
incomplete hardware telemetry. This level is clearly above the usual "I
wrote an agent and it got 50% smarter".

**3. Where a professional will push hard.**

*Problem 1 — measured improvement may be improvement against the test.* The
most serious scientific risk. README example: category D-ea went 0.34 →
1.00 after programmatic normalization produced the JSON shape the validator
expects. That is a real interface fix, not necessarily better decision
quality. The skeptical engineer says: "You did not teach the model to plan
better; you taught the program to reshape its answers into a format your
validator likes." That criticism is well founded — even though format repair
is genuinely useful. Sharper still: the agent designs improvements while
watching results on the very task bank it is scored on. The paper
"Rethinking the Evaluation of Harness Evolution for Agents" addresses this
directly: previously unseen tasks and equal-budget comparisons are required.
What is needed: a developer-blind test set, an independent validator, and a
separate evaluation before/after fixes. Without it a specialist will not
accept high percentages as evidence of generalizable system improvement.

*Problem 2 — "autonomous self-development" sounds stronger than the
evidence.* README claims the whole published code was written, tested and
improved by an autonomous agent. docs/autonomy.md itemizes roles — good —
but docs/limitations.md says raw agent transcripts are not published and
exact snapshots of many early versions are missing. So the main evidence of
autonomy is logs compiled by the agent itself. A skeptic will ask: who
checked that those records fully and accurately reflect what happened? That
does not make the claim false; it means an independent reader lacks a strong
enough evidence chain. A professional phrasing: "An AI agent autonomously
developed and tested successive harness modifications under human-defined
objectives and constraints." Claims of recursive self-improvement or of a
system developing its own intelligence would require far stricter proof.

*Problem 3 — the self-made benchmark may be too convenient.* 178 synthetic
tasks in 11 categories are enough to start, but an independent researcher
will ask how close they are to real user tasks and how hard they are.
Several categories score near 100% — that can mean a good system, or too
easy tasks, narrow templates and deterministic repairs. Be careful with the
word "accuracy" when the composite score mixes substantive correctness,
structural requirements and programmatic post-processing. External task
sets, genuinely new scenarios and comparisons against ordinary simple
solutions are needed.

*Problem 4 — insufficient comparison with alternatives.* If the harness
raised success, a professional asks: what about just one more attempt? a
better system prompt? a plain JSON validator? a standard agent framework? a
slightly stronger model? how many extra seconds and tokens does the gain
cost? If a complex autonomous improvement loop achieves what ten lines of
plain Python or a single retry achieves, the scientific value of the
autonomy itself becomes less obvious. Compare not only raw vs harness, but
against the simplest alternatives at equal budget.

*Problem 5 — the research title promises more than current scale.* "Open
Research into Autonomous Local AI Evolution" sounds like a large program;
what exists is an early experiment with one model, one main task bank and a
few computers over a short span. Not bad — but the scale of formulation
exceeds the scale of confirmed work. Better to stress that this is an open
ongoing experiment than to make statements resembling a fundamental
achievement announcement.

**4. What can look amateurish.** Not the architecture, not Python, not home
computers — cheap hardware is a strength. It is the formulations and missing
checks: "self-improving AI" if only the code around the model improves;
"every line written autonomously" without complete primary evidence;
99-100% on self-made tasks; high marks for correct JSON; one model type; the
agent developing and grading itself; a few days of experiment; an
unimplemented privacy architecture (hypothesis, not verified result). Minor
visible warts: wrong paths in docs, no full automatic publication pipeline,
unfinished dashboard, limited version history — typical of an early project.
None of them makes the experiment unserious; the problem is when they
combine with very grand claims.

**5. Against current research practice.** Source code published (expected:
published). Raw results: archives exist (expected: fully verified records).
Test repeatability: thoughtful scheme (expected: verified independent runs).
Version comparison: paired tests (expected: paired + statistical
uncertainty). Generalization: not proven (expected: held-out tasks and
external benchmarks). Control methods: limited (expected: simple baselines
and budget-matched alternatives). Autonomy evidence: decision logs
(expected: primary execution traces and independent audit). Model/harness
error separation: partial (expected: systematic decomposition). Study
duration: short (expected: enough to assess durability). Modern practice is
no longer satisfied with accuracy plus an agent description — HAL studies
model/scaffold/benchmark effects and publishes massive execution traces.
Strata moves in the right direction but is early.

**6. How interesting is it?** Local-AI developers: potentially interesting
now — cheap RTX 3060, frozen weights, deterministic repairs, cost-of-quality
analysis has practical value. Agent developers: the history of autonomous
accept/reject decisions is interesting, especially with full decision chains,
but they will want comparison with known approaches. Academic researchers:
current evidence is not enough for strong conclusions, yet the open archive
can serve as material for independent experiments. Another interesting
aspect: the project also studies how the agent itself organizes software
experiments, finds its own errors and decides to roll back. That second
aspect may turn out the most original.

**7. Positioning that avoids unnecessary skepticism.** Not "we built
self-developing AI". Rather: "An open, AI-operated home-lab experiment
investigating autonomous harness development around frozen local language
models. We publish successful and failed iterations, paired benchmarks,
execution costs, and available provenance data. Our goal is to study which
improvements generalize, which merely optimize benchmark formatting, and how
much autonomy can be demonstrated experimentally." That formulation is much
more convincing than grand promises.

**Final assessment.** As a personal engineering project — serious work. As a
scientific result — a preliminary study with substantial methodological
limitations. A competent specialist looking at the code, rollback history,
paired measurements and raw data will not call it dilettantism. But expect
hard criticism along three lines: overfitting to own tests, insufficient
independence of evaluation, incomplete evidence chain for autonomous code
origin. And that criticism is useful. The most promising thing here is not
the high percentages or even the harness-raised model quality, but the open
history of an AI agent running engineering experiments on its own, making
mistakes, measuring the consequences of its own changes, and abandoning
failed decisions. If that can be demonstrated on new tasks, over a long
period, with independent verification and honest compute accounting, the
project can reach a much wider professional audience. It can already be
shown publicly — positioned as an open research lab, not as a proven
breakthrough in AI self-development.


---

## Second audit (EXT-003, same day) and our response

The same external AI produced a stricter 10-criterion re-audit: **7.0/10**
("engineering maturity grows faster than scientific evidence"). Full English
translation: `history/external-model-inputs/ext-003-audit-2026-11-01.md`;
verbatim Russian original archived in release asset
`ext-records-2026-11-01-v2.tar.zst` (sha256 `e5bd7fe1…643b7f`), registered
as EXT-003 in the input ledger.

The audit named three scientific gaps and four polish defects. We answered
each with a shipped experiment or fix the same day, not a roadmap promise:

| audit finding | response, public evidence |
|---|---|
| second scorer did not confirm the v1.8→v1.9 gain (−0.011 on 37% coverage) | independent scorer v2 at ~90% coverage: matched delta **−0.006** — mean gain still not confirmed; but 45/79 harness-reported regressions reverse to improvements, 0 confirmed worse. Published as-is: `results/independent-scorer-v2.md` |
| holdout G degradation (16.7%) treated as transfer failure | root-caused the same evening: **our holdout generator shipped G tasks without their documents**. Fixed (bank v2, ids/refs unchanged), corrected pilot: overall **0.959**, G **0.833**. Broken v1 rows kept published and annotated: `results/holdout-mini.md`, `history/failures/failures.md` |
| missing budget-matched simple baselines ("why a harness at all?") | ran 4 simple arms vs contour on 66 identical (task, rep) pairs, same box/seeds/validators: contour **+0.134 over the best arm, 16/0 paired wins**, A-category arithmetic 0.000→1.000 where retries cannot help; independent scorer confirms (0.810 vs 0.715). Honest counterexample: generic retry beats contour on H. `results/baselines.md` |
| README quickstart broken (old org/dir) | fixed (`cd claryel-autonomous`); link checker now also validates the quickstart block |
| privacy README said NOT implemented while code exists | corrected to honest prototype status: 18 synthetic tests in CI, no live cloud lanes, no real personal data processed |
| unexamined CI failure history | documented in `history/failures/failures.md` § CI failure history |
| autonomy evidence rests on logs, not transcripts | accepted as a standing limitation; primary transcript publication requires a privacy pass — tracked in `docs/limitations.md`, not papered over |

What we do **not** claim in response: that the headline +0.047 is now
independently confirmed (it is not), or that one 73-row corrected pilot
establishes generalization (it does not; the full 206-task series is the
gate). What the day did change: the central question "harness vs a few
dozen lines of code" now has a measured, reproducible, scorer-independent
answer on our task families — and the holdout scare turned out to be our
own bug, found and fixed by taking the criticism seriously.
