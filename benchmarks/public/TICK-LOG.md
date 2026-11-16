# Public-line tick log

Working log of the CLARYEL public-benchmark line (`benchmarks/public/`), one dated
block per autonomous tick. Append-only: a superseded sentence stays visible and the
correction goes beneath it with the grep or command that settles it, the same rule
`LEG-INCIDENTS.md` follows. Blocks written before 2026-11-16 07:19 lived in working
notes outside git and are not reconstructed here — that gap is recorded in the tick
201 block, along with a figure that only existed in those notes.

Two rules this file is held to: every number is read out of a printed cell or a
stored file (grep before writing, not after), and every key name comes from the
producer's emitted key set — the gate has twelve rules and no other vocabulary, so a
sentence that names a key the sampler never emits is a fabrication even when the
verdict it describes is real.

## Tick 201 — 2026-11-16 07:19 CET: the state rule was never re-derived either — a refusal attributed to `engine_state=D` had only the gate's word, and 6 of 9 windowed state-D refusals turn out to sit on a quiet device

The 07:19 line is the day's eleventh reading and its latest refusal, and the gate
stays NO-GO. Read back out of the stored file: swap in 161.3 MiB/s = 8.07x the 20.0
mean ceiling (sampled window peak 275.2), `engine_state=D`, GPU mean util 1.3% at
26.84 W, `blk_read=0.1 MiB/s` at whole-disk scope, swap_free 48,696 of 65,535 MiB,
MemAvailable 19,297 of 61,953 MiB, load1 7.67, zero foreign legs, `/health` 200. The
day escalated while this line was between ticks: 05:41 6.91x, 06:43 10.69x (the
day's highest refusal draw), 07:19 8.07x, and the last gate-GO is
`preflight-20261116-0349.txt`, 210 minutes before this cut. Nothing runs; no arm was
launched or stopped this tick.

Correction, recorded because this line's whole discipline is that prose may only
quote a printed or stored cell: the first draft of the paragraph above said "swap
15.6 MiB/s = 0.78x, `engine_mem_limit_halt=1`, GPU mean 14.3% with 47.99 W,
`blk_read=28.5 MiB/s`", carried from tick memory. None of it is in the corpus.
`engine_mem_limit_halt` is not a preflight field at all: 0 of the 165 stored readings
carry that key, the untracked producer emits 23 keys and it is not one of them, and
the gate has no rule that could print it — so a KEY NAME, not merely a value, had
been invented. Nothing published ever quoted it (`git grep engine_mem_limit_halt HEAD`
returns empty and no tracked file mentions `halt=1`); the defect lived only in this
untracked working log, which is itself the finding: a working log outside git carries
no diff, no review and no replay, so its numbers can drift from the corpus silently.
Rule adopted with this tick: a tick sentence may name a key only if it is in the
producer's emitted set, and may quote a number only if a stored file carries it
(grep the corpus before writing, not after).

The published v9 table (rewritten this morning) attributes every refusal to a rule
out of the gate's reason text, but of the twelve rules it re-derives ONE from the
readings, the swap band. Every other attribution in that table, including the 13
corpus refusals it credits to `engine-state-D`, is still the gate's own claim. The
state rule is the cheapest rule to re-derive and the most interesting: it has no
ceiling to disagree about, because the gate fires when `engine_state` contains `D` —
a substring test, so `Dl` fires too.

A survey of the corpus said the state test is safer to mirror than to re-implement.
The gate parses every `key=value` token anywhere in a line and keeps the LAST value
of a repeated key (`([A-Za-z_][A-Za-z0-9_]*)=\s*(\S+)`, comment lines skipped), while
the census's own row parser was line-anchored. Today the difference is invisible for
163 of the 165 files, and the two exceptions are the corpus's own archaeology:
`preflight-20261111-0948.txt` emits `engine_state=` with an empty value and
`preflight-20261111-1144.txt` emits `  engine_state       S` with no `=` at all, and
the gate's pattern sees neither — which is exactly why those two readings are input
gaps and never healthy rows. The new cross-check runs the gate's regex itself
(byte-identical pattern in the census, `GATE_KV`), while the old line-anchored parse
stays for the published swap-band cells so no published number moves.

The three new rows, at the committed 07:19 cut (census stamp moves to
`pub-preflight-census-v10`, gate sha16 `dd2f0e4fa0255fa5` unchanged):

```
| state-rule cross-check: reading's own engine_state contains D vs the gate's engine-state-D reason
|   day 20261116: AGREES (2 = 2) / last 24 h: AGREES (5 = 5) / whole corpus: AGREES (13 = 13)
| readings with no engine_state key: day 0 of 11 / 24 h 0 of 32 / corpus 2 of 165
| state-D refusals on a device the device rule calls quiet (50.0 whole-disk / 100.0 unscoped):
|   day 1 of 2 (2 with a window) / 24 h 2 of 5 (5) / corpus 6 of 9 (13 named by the gate)
```

Three things follow. (1) The state attribution holds under an independent
derivation at every scope — the set of readings whose own `engine_state` token
contains `D` is exactly the set whose gate reason line names the rule, 13 = 13.
That is the first refusal class in this line verified from the columns rather
than from the reason text. (2) The denominator row is not decoration: 2 of the 165
corpus readings have no state the gate can read (one emits `engine_state=` with an
empty value, one omits the `=`), so for them the check is blind and the gate itself
calls them an input gap, never healthy. (3) The device-quiet complement splits the
class physically, and the split is the interesting number: of the 9 state-D
refusals that carry a device window, 6 sat on a device the device rule calls quiet.
Today's two state-D refusals are the two halves side by side —
`preflight-20261116-0214.txt` is state D with `blk_read=77.6 MiB/s` whole-disk (top
reader `basalt`, GPU mean 96%): the device really is saturated, which is the class
the reason text calls "thrashing"; `preflight-20261116-0719.txt` is state D with
`blk_read=0.1 MiB/s` and GPU mean 1.3% while swap-in runs 8.07x: the wait is page-in
traffic, not a saturated disk. A state-D verdict read without that complement reads
as one failure mode when the corpus holds two. Four state-D refusals (13 minus 9)
predate the device key, which arrived on 2026-11-14, and belong to neither class;
the row prints that count rather than quietly joining a smaller band.

Non-retroactivity proved by replay, not asserted: the v9 tool and the v10 tool
were run at the same `--as-of 2026-11-16 07:19 --no-transition` and their tables
diffed. The diff is 1 changed stamp line, 6 prose lines replaced by 13, and 3
added rows — 24 changed lines total, zero numeric cells of the v9 table moved, and
the printed gate sha16 identical in both (`dd2f0e4fa0255fa5`), which is expected
because the gate file is untouched this tick. The v9 table at the 06:43 cut stays
published in git history as its own shape (HEAD: window `as-of 2026-11-16 06:43`,
164 readings, DAY 10 bandable / 7 swap-rule refusals 1.27-10.69x / median 5.630x);
this tick rewrites the working copy at the 07:19 cut, so the day cells move because
the day slice grew by one reading (11 bandable, 8 refusals, median 6.223x — the new
point is 07:19 at 8.07x), not because any rule changed.

Contract deltas: `harness/pub_preflight_census_test.py` 212 -> 219 checks green.
The new checks pin (a) the AGREES cell with both set sizes named at all three
scopes, (b) the missing-key denominator (0 of 13 in the fixture corpus), (c) the
device-quiet cell with its denominator, (d) a state-D refusal taken WITHOUT a
device window prints 'no denominator' instead of shrinking the band, and (e) a
`Dl` state fires the rule and agrees in both derivations, because an equality test
here would call a real gate refusal unexplained. Non-vacuity in both directions,
with the refusal-site count kept intact so the red comes from the set comparison
and not from the rule-table guard: `if "D" in vals["engine_state"]:` ->
`... or "S" in vals["engine_state"]:` (the rule fires on a reading whose key says
S) prints DISAGREES, names the file and exits 4; `... -> if "Z" in ...` (the rule
can never fire) with a D-carrying reading still refused by the swap rule prints
DISAGREES derived-only and exits 4. `harness/pub_preflight_test.py` stays
117/117 green with an unchanged gate sha16.

Standing checks, each re-run at this tick rather than inherited:
`scripts/push_ready.sh` rc=0 — manifest VERIFY PASS, links 155 checked across 341
markdown files, DOCS POLICY PASS (push), gitleaks clean, infra scanner 0 findings,
and 6 pub gate rows green (arms index drift 0; 42 derived percents recomputed from
shipped bytes; grok cell rule 9 documents / 0 findings; superseded-cell rule 9 / 0;
digest row rule 49 rows / 0; three-arm parity 49 rows / 9 sets / 0 findings at
contour stamp 0.0.2.56 with Grok not an arm).
`scripts/pub_three_arm_parity_check.py` on its own: same 49 rows / 9 sets / 0
findings. `scripts/pub_grok_resume_check.py --as-of 2026-11-16` exits 3 BY DESIGN
while the cancel stands — 22 checks, exactly one finding (`owner_window`: the 182
unasked ids in the pin are a record, not a queue), the pin intact (ifeval 359 stored
rows / 359 ok, sha16 `01c1ee0b6e7f6d5d`, resume set 182 ids marked VOID,
gpqa-diamond / humaneval / mmlu-pro resume sets empty), and the machine-readable
marker on disk is 121 bytes with mtime 2026-11-12 06:54:20. That marker is the only
thing making `scripts/pub_bench_cloud.py` refuse a Grok arm, so it stays and nothing
here re-arms it.

Next tick's question: the state rule agrees with the readings, so the remaining
unverified attributions are the rules with a CEILING — device-read, footprint,
idle-spin — whose derived sets can disagree with the gate for a numeric reason. A
ceiling rule is also the only kind where a scale fix can move the boundary (the
whole-disk double-count found on 2026-11-14 is why the producer emits `blk_scope`
and why unmarked files are judged by the old ceiling), so a derived set is what
would make a future scale fix auditable instead of a re-typing exercise. Second
open item, closed the same tick: this log lived outside git. Its numbers were the
only figures in the line with no diff, no replay and no scanner, and this tick
proved they can drift into values no stored file carries. It is now a tracked file
(first commit at this tick), so every future tick sentence is a diff, runs through
the link checker and the secret scanner, and can be replayed against the corpus.
