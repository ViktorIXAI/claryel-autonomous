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

## Tick 202 — 2026-11-16 10:30 CET: the footprint ceiling's binding number was produced by a process this endpoint no longer runs — census v11 re-derives the other nine gate rules from the stored columns and attributes every pooled footprint figure to the engine generation that sampled it

The day's first gate-GO is the 10:07 reading, and it is also the first reading of a
new engine process. Read out of the stored file: `engine_state=S`,
`swap_used_mib=65`, `swap_free_mib=65470`, `swap_total_peak_mib_per_s=0.0`,
`engine_vmswap_mib=0`, `health_code=200`, `health_loaded=true`,
`engine_serve_procs=1`, `gpu_util_mean_pct=5.0` / `gpu_power_w=27.98`,
`blk_read_mib_per_s=0.1` at `blk_scope=whole-disk`, `engine_pcpu=10.3`, and the
producer comment `# engine pid=438502`. The eleven earlier readings of the day all
carry pid 175316. The printed day cells: `readings of the as-of day` = 12
(3 GO / 9 NO-GO / 0 gap), `longest consecutive NO-GO run inside the day` = 5,
`readings since the day's last gate-GO` = 0 (last GO 10:07). The morning's swap
storm left with the process that held it, not with a rule change on this line.

**What the census could not see before this tick.** The producer names the pid it
sampled in a comment line and the gate's parser skips comment lines, so every
footprint, RSS and page-cache figure in the published table has always been pooled
over whatever engine processes the corpus happened to contain. That is harmless
while one process serves the window and wrong the moment the engine is restarted.
At this cut the day scope prints **2 generations over 12 readings**: pid 175316
(11 readings, 2 GO / 9 NO-GO, footprint max launchable 9499 MiB / refused
10770 MiB, last sampled `preflight-20261116-0719.txt`) and pid 438502 (1 reading,
1 GO, footprint max launchable 0 MiB, refused `no key`). The unattributable
denominator is printed next to it: 0 of 12 day, 0 of 31 in the last 24 h, 2 of 166
in the corpus — those two files predate the producer's pid comment. The overlap
state is PARTIALLY OVERLAPPING (one generation carries both launchable and refused
draws). And the row that matters for the pre-registered arming rule reads, at day
scope: launchable footprint maximum 9499 MiB (`preflight-20261116-0019.txt`)
belongs to pid 175316 while the newest reading sampled pid 438502 →
**GENERATION-STALE: a footprint ceiling drawn from this value describes a process
this cut no longer samples**. Same cut's dry-run row: a ceiling above 9499 MiB
fires on 0 of 12 launchable and 6 of 36 refused stored windows. The state word is
computed, and the harness pins STALE, CURRENT and `no denominator` separately, so
the word cannot become a caption.

**All nine remaining gate rules are now re-derived, not quoted.** v9 derived the
swap band, v10 the engine-state rule; this tick adds health-loaded, health-code,
engine-process-absent, swap-free, mem-available, device-read, idle-spin, GPU-busy
and foreign-legs, each compared with the set of readings whose gate reason line
names that rule. The coverage row prints 11 of 11 computed rules at all three
scopes, and every cell agrees: `device-read` 1 = 1 (day) / 3 = 3 (24 h) / 8 = 8
(corpus), `gpu-busy` 1 = 1 / 3 = 3 / 6 = 6, `swap-free-low` 15 = 15 in the corpus,
`idle-spin` 17 = 17, `health-loaded-false` 1 = 1, and four rules never fired in the
corpus. The blind counts are printed inside each cell rather than hidden: 35 of the
82 corpus refusals carry no parseable device key, 38 no GPU key, 30 neither
`health_loaded` nor `engine_serve_procs` (both keys joined the producer after the
corpus's first week), 1 lacks the idle-spin pair. An AGREES over a shrunken
denominator is not published as an agreement without that number beside it.

**The guard that keeps the vocabulary honest.** Every rule anchor in the census rule
table must still exist in the gate source, the gate's refusal-site count must equal
the table's total, and every rule id in the table must have a derivation. Dropping
one derivation reddens the run (exit 4), and so does a gate refusal site the table
does not know — both directions are exercised by fixture in the harness, not
asserted in prose.

**Non-retroactivity, proved by replay.** v10 bytes and v11 bytes run at the same
`--as-of 2026-11-16 03:05 --no-transition` differ by exactly one removed line (the
stamp sentence) and 27 added lines (stamp sentence, the prose block, 9 rule rows,
1 coverage row, 4 generation rows). Every published numeric cell is byte-identical,
the printed gate sha16 is unchanged (`dd2f0e4fa0255fa5`, the gate was not touched),
and `--check` against the regenerated table exits 0.

**What the census cannot say, said plainly.** It sees only the pid. The endpoint's
supervisor log carries no restart entry for 10:07 — its last entry is 2026-11-13 —
and the process now serving, read from the box's own process table at 10:24, is the
brain line's v0.4.0 launcher (`--vram-reserve-mib 500 --resident-budget-gib 46
--resident-cpu-experts --vision --grammar on`, expert profile `placement-040.prof`).
So this restart belongs to the brain line, not to this one, and no stored verdict
moved: the gate never reads comments.

**Readiness repair, no arm, one bounded probe.** The pinned local-arm profile
`~/parb/p2005-profile.json` still named the Strata-era alias. Probed at 10:3x
against the endpoint in force: old alias with the file's own key → `HTTP 404` with
body `{"error": {"message": "The model '<alias>' does not exist", "code":
"model_not_found"}}`; the served alias (read from the endpoint's own `/health`
`model` field) with that same key → 200, `finish=stop`, usage 60 prompt / 32
completion / 92 total, 55 prompt tokens cached. The key did not move: the profile's
key and the endpoint's own key file hash identically (sha16 `faae108fefea011b`
both sides). The untracked file was re-pointed to the served alias with its Strata
bytes kept beside it (`p2005-profile.json.strata-era.bak-20261116`). This is the
documented trap in its quiet form: an alias the endpoint no longer serves produces
rows at ~0.0 s, an exit code of 0 and a full record count.

**Trap re-measured while doing it, and it cost two false 401s.** An authorization
scheme word assembled inline in a tool-call source comes back replaced by the
redaction placeholder, and the placeholder is what actually executes — so the
failure presents as *wrong API key* while the key is fine and the source is broken.
Checked by printing the assembled shape and asserting the placeholder is absent
from the value in memory, never by reading the echo. Nothing was rewritten on the
endpoint on the strength of those two 401s.

**Suites.** `harness/pub_preflight_census_test.py` 219 → 254 checks green.
`harness/pub_preflight_test.py` stays 117/117 with unchanged gate bytes. Three-arm
parity 49 rows / 9 sets / 0 findings at contour stamp 0.0.2.56 with Grok not an arm;
digest-row gate 49 rows / 0 findings; superseded-cell rule 9 / 0; grok cell rule 9 /
0; grok resume check exits 3 BY DESIGN with the pin intact. No leg ran this tick, so
`LEG-INCIDENTS.md` is untouched and no published percent moved.

Next tick's question: three rules (`health-code-not-200`, `mem-available-low`,
`foreign-legs`) agree only against a zero set — the corpus has never exercised them,
so their derivations are pinned by fixtures, not by real bytes. And the footprint
dry-run ceiling must be re-drawn from generation 438502's readings before any arming
decision: pre-registering from 9499 MiB would be pre-registering a retired process.

### 10:55 follow-up inside the same tick: the endpoint's engine moved twice while the census was being written

The 10:07 gate-GO and a second gate-GO at 10:35 both belong to engine process `438502`, which
started 09:59 and runs a **newer Basalt build from a different directory** than the one process
`175316` served with (that process started 14 Nov 16:31 and was last sampled at 07:19). The day
scope therefore prints 2 generations over 13 readings, and the row carrying the footprint ceiling's
binding number still reads GENERATION-STALE at every cut: the launchable footprint maximum
9499 MiB comes from `preflight-20261116-0019.txt` of pid 175316, while the newest reading of the
scope sampled pid 438502. One honest limit of the new attribution: a reading names a **process**,
not a build — the producer stores only the pid, so which engine binary that pid ran is a box-side
fact this table cannot see. That is the second reason a footprint ceiling may not be carried across
an engine swap, and it is why the census refuses to pool across generations instead of pretending
the pid is enough.

Two consequences, closed mechanically in this tick:
- The local runner's fetched key/profile file still carried the **pre-swap model alias**. Launched as
  it stood, every row would have finished in ~0.0 s with `HTTP Error 404` while the runner still
  reported a full record count — the known broken-endpoint signature, not a model result. The alias
  in that untracked profile now names the served model; the key bytes were verified unchanged by
  hash only and never printed; live auth was confirmed with ONE bounded chat-completions call naming
  that alias. On this engine `GET /v1/models` answers 401 even with a valid key, so it is not an
  auth test — the probe has to be a completion.
- The published local bare rows sit on the **pre-swap build**: the 2026-11-08..11 arms carry no
  serving-engine stamp at all (recorded in the runner's own header). A bare row taken on the new
  build describes a different endpoint state, so a contour-parity pair must be drawn inside one
  engine window. The tooling already supports proving that: each leg writes a leg-level engine note
  and every row carries `engine_sha256_16` from the `/health` body, so a mid-leg swap stays visible
  per row and two rows can be shown to share one engine or not.

No leg was launched at this cut, and that is a decision, not a stall. The three-arm parity census
reports 0 findings across the 9 in-force sets (the ladder holds no open item), the footprint rule's
arming counter stands at 13 of 30 launchable windows carrying the field (the swap-peak rule at
22 of 30), and the endpoint box is inside a Basalt-version campaign of its own: the serve log was
renamed at 10:00, probe and A/B scripts were written 09:53-10:01, and the GPU read 99 % utilisation
at 157 W at 10:35 while the producer's 6 s window averaged 4.7 %. A percent row taken inside
somebody else's version campaign is not attributable to a named engine build, so the next tick
launches only after a fresh reading taken at launch time, and the footprint ceiling stays
GENERATION-STALE until windows of the live generation carry it.

## Tick 203 — 2026-11-16 11:14 CET: the new engine generation's first launchable windows all read a zero swap footprint — the census moves its counters, the ceiling still binds to a retired process

No leg launched, and the empty queue is the mechanical answer, not a reading: three-arm parity
49 rows / 9 sets / 0 findings (contour stamp 0.0.2.56, Grok not an arm), and the grok resume pin
exits 3 by design with the pin intact — its 182-id resume set prints VOID under the 2026-11-12
owner cancellation. Nothing in force needs a row.

**The endpoint went quiet and the gate took it.** The foreign Basalt-version campaign that held
the box at GPU 99 % / 157 W at 10:35 is over. A fresh reading at 11:14
(`preflight-20261116-1114.txt`, wrapper bare, gate rc captured unshielded) returns **GO**: engine
pid 438502 (up since 09:59) state R, sampled pcpu 4.6 %, RSS 54 158 MiB, **VmSwap 0 MiB**, GPU
mean 0.0 % peak 0 % at 26.47 W, whole-disk read 0.1 MiB/s (top reader `basalt`), swap free
65 470 of 65 535 MiB with SwapCached 9 MiB, `foreign_legs=0`, `/health` 200 +
`health_loaded=true` + one serve process.

**Census re-run to the 11:14 cut** (same v11 shape, gate sha16 `dd2f0e4fa0255fa5`, gate bytes
unmoved; `--check` drift → 0 after `--markdown`). The committed-vs-recomputed diff is a re-count,
every cell attributed: readings in window 166→168, corpus GO 78→80, day scope 12→14 readings
(3 GO → 5 GO; the day refusal band unchanged 1.27-10.69x, median 6.223x — both new GO draws sit
at 0.0x), swap-peak arming 21→23 of 30, footprint arming 12→14 of 30, and one file
(`preflight-20261115-1053.txt`, a GO) aged out of the sliding 24 h window — the launchable-24h
count stays at 8 with nothing reclassified.

**Tick 202's re-draw question answered in a sharper form than it was asked.** Generation 438502
now holds three launchable windows — 10:07, 10:35, 11:14 — and all three carry
`engine_vmswap_mib=0`. The 10:35 draw was taken *inside* that generation's own GPU-99 %/157 W
campaign, and even then the engine held zero bytes of swap. The retired generation 175316, by
contrast, held 6 970-10 770 MiB across 15-16 Nov (the swap total was 65 535 MiB in every file of
that range — the size change predates this corpus and is not a box event today). Consequences, as
published by the table: the pooled dry-run ceiling (binding value > 9499 MiB, fires 0 of 14
launchable / 6 of 36 refused windows) stays GENERATION-STALE at all three scopes — its binding
number belongs to pid 175316, last sampled 07:19 — while a ceiling drawn only from the live
generation's windows could be pre-registered as "> 0 MiB" and nothing more: arming from zeros
arms a rule whose failure mode the live process has not demonstrated once. Decision stays open;
the counter counts coverage, not information, and that distinction becomes a real question if the
live generation keeps reading zeros as the counter approaches 30.

**Tick 202's other question, re-checked:** the three rules `health-code-not-200`,
`mem-available-low`, `foreign-legs` still fire 0 / 0 / 0 at all three scopes at this cut — their
v11 derivations remain AGREES (0 = 0) against a corpus that has never exercised them. That is an
honest zero, not evidence; only a real occurrence on the box would move it.

**Repo hygiene.** `origin/main` moved under this tick with one foreign commit,
`69390e6` (CHG-002 MACSTUDIO hardware drift, `hardware/` paths only) — fetched and
fast-forwarded; the two workstreams share no path. The GitHub docs-freshness job
(`ef7ea47ff99b`) failed its 03:00 run today with "repo is dirty; refusing daily docs refresh"
(its stdout names `scripts/pub_preflight_census.py` modified — the previous tick's work in
flight at 03:00, exactly the standing machine-note class); failure_streak 1, self-clears when
03:00 catches a clean tree, and in-flight work is deliberately not committed to paper over it.
The frozen-line watchers (`P2005 paired full 2.1→2.2 watch`, `Mac v2.2 full`) still fire on
schedule and stay inert — owner decision, untouched.

**Suites.** `harness/pub_preflight_census_test.py` 254/254 green, `harness/pub_preflight_test.py`
117/117 with unchanged gate bytes; digest-row gate 49 rows / 0 findings, superseded-cell rule
9/0, grok cell rule 9/0, arms index drift 0, derived percents 42 recomputed / 0 findings.
No leg ran, so `LEG-INCIDENTS.md` is untouched, zero model calls, zero cloud calls, and no
published percent moved.

## Tick 204 — 2026-11-16 11:50 CET: the footprint arming counter was buying coverage, not information — census v12 prints the non-zero/zero split and names a generation that has never swapped

No leg launched: three-arm parity **49 rows / 9 sets / 0 findings** (contour stamp 0.0.2.56, Grok not
an arm), the standing pre-push gate `scripts/push_ready.sh` rc=0 with all six pub-gate rows green, and
the grok resume pin exits 3 by design — **182 ids VOID** under the 2026-11-12 owner cancellation,
`ifeval` stored 359 rows / 359 ok (sha256-16 `01c1ee0b6e7f6d5d`), pin intact. The queue is empty, so
this tick spent its budget on the measurement stack instead of manufacturing a leg.

**One new reading, and it is a GO.** `preflight-20261116-1149.txt` (wrapper run bare, gate rc captured
unshielded): engine pid 438502 state S, sampled pcpu 1.0 %, RSS 54 244 MiB, **VmSwap 0 MiB**, GPU mean
0.0 % / peak 0 % at 26.84 W, whole-disk read 0.1 MiB/s (top reader `basalt`), swap 65 of 65 535 MiB in
use with SwapCached 9 MiB, `foreign_legs=0`, `/health` 200 with `health_loaded=true` and one serve
process → `PREFLIGHT GO`, gate rc 0. Nothing was launched: a GO is available capacity, not a reason to
spend it, and no in-force set is missing a cell.

**Census to the 11:50 cut** (gate sha16 `dd2f0e4fa0255fa5`, gate bytes unmoved,
`harness/pub_preflight_test.py` 117/117). Readings in window 168→169; corpus 81 GO / 82 NO-GO / 6 input
gap; day scope 14→15 readings (5 GO → 6 GO), the day's last GO aged 1 minute and the trailing 24 h
refusal run is 0. Swap-peak arming 23→24 of 30, footprint arming 14→15 of 30. Day cells recomputed at
this cut: launchable band 0.00-0.05 x the 20.0 mean ceiling, refusals 1.27-10.69 x (median 6.223 x),
the rule's own boundary accepted ≤ 0.94 x and refused ≥ 1.27 x, `EMPTY BY CONSTRUCTION`.

**The change (census v12: coverage is not information).** Tick 203 left the sentence "the counter counts
coverage, not information, and that distinction becomes a real question if the live generation keeps
reading zeros as the counter approaches 30". It is now a printed cell rather than a warning beside the
number. The pre-registered arming rule counts launchable windows that CARRY `engine_vmswap_mib`, and a
window reading 0 MiB carries it — so a ceiling drawn over an all-zero launchable group is `> 0 MiB`, a
rule armed against a failure mode nobody has observed on that process. Three rows join the footprint
block (launchable split non-zero / exactly 0, the same split on the refused side, and a computed
informative-coverage state `INFORMATIVE` / `ZERO-DRAW-DOMINATED` / `ALL-ZERO`), and the generation block
gains per-generation `non-zero footprint draws N of M launchable / K of L refused` plus a row that asks
whether the NEWEST sampled generation has ever recorded a footprint above 0 MiB. The zero draws stay in
the coverage count — they are measurements — they only stop being able to pose as a ceiling.

**What those cells read on live bytes.** Corpus at this cut: 15 launchable footprint draws = 11 non-zero
/ 4 zero (`INFORMATIVE`), refused side 36 non-zero / 0 zero. The coverage went 14→15 while the
informative count stayed at 11: the new draw is another zero. Per generation, the retired 175316 is
informative in every window it produced (day 2 of 2 launchable / 9 of 9 refused; last 24 h 5 of 5 /
22 of 22) while the live 438502 prints `0 of 4 launchable / 0 of 0 refused` — its four windows (10:07,
10:35, 11:14, 11:49) all read 0 MiB, including the one taken inside its own GPU-99 %/157 W campaign —
so the new row states `ZERO-FOOTPRINT GENERATION: the only ceiling this coverage admits is > 0 MiB, so
arming on it arms a rule whose failure mode this very process has never demonstrated once`, at all three
scopes. The pooled dry-run ceiling (> 9499 MiB, firing on 0 of 15 launchable and 6 of 36 refused
windows) stays `GENERATION-STALE` at all three scopes.

**Non-retroactivity, proved rather than asserted.** The v11 bytes were restored inside `scripts/` (the
tool resolves its gate relative to its own directory) and re-run at the committed cut: its output is
**byte-identical to the committed table**, which is what licenses the second half — the v12 tool at the
same `as-of 2026-11-16 11:14` cut differs from those committed bytes by exactly the stamp sentence
(gate sha16 unchanged), **4 added labels, 0 removed**, and **1 label whose cell gained counters** (the
generation detail row, appended counters only: every reading count, first/last file name and footprint
maximum byte-identical). Across the 36 verdict / band / ceiling / arming / counter cells, **0 moved**.
The restore was sha-verified and the replay file deleted; `git status` names only the four paths of
this tick.

**Decision.** The arming threshold is untouched (30 launchable windows carrying the key, as
pre-registered) and no footprint rule is armed or proposed — at 15 of 30 the question is not live. What
changed is that when the counter does reach 30, the table will already have printed whether those 30
windows carry a ceiling at all, so arming off a zero-footprint generation can no longer be justified by
the counter alone. If the live generation keeps reading 0, the decision is `no ceiling from this
generation`: the count of unexercised windows says nothing about swapping.

**Suites and hygiene.** `harness/pub_preflight_census_test.py` **271/271** green (254 at tick 203; +17
for the split rows, the three state words over ALL-ZERO / ZERO-DRAW-DOMINATED / INFORMATIVE fixtures,
and the source-level v12 keys) and its stamp check no longer pins `CENSUS_STAMP = 11` exactly — it
asserts the floor plus the v12 structure, because an exact-stamp pin goes red on every legitimate shape
change (tick 197's class). `--check` green against the committed v12 table. `origin/main` unmoved since
tick 203 (ahead 0 / behind 0), no foreign paths in the tree. No leg ran, so `LEG-INCIDENTS.md` is
untouched: zero model calls, zero cloud calls, no published percent moved.

## Tick 205 — 2026-11-16 12:49 CET: the table banded only RATES while the failure mode of this box moved to a STATE — census v13 publishes the memory-headroom trajectory per engine generation, and the 10:06 restart shows the two free columns moving in OPPOSITE directions

No leg launched: three-arm parity **49 rows / 9 sets / 0 findings** (contour stamp 0.0.2.56, Grok not
an arm), so the queue is empty as arithmetic, not as scheduling, and this tick again spent its budget
on the measurement stack. `scripts/pub_grok_resume_check.py --as-of 2026-11-16` read unshielded with
the code captured on the next line: **22 checks green, exit 3, `RESUME GATE: NO-GO - do not spend
quota`**, one FINDING which is the owner cancellation itself ("the Grok line is CANCELLED by owner
decision 2026-11-12 … the 182 unasked ids in the pin are a record, not a queue"), `ifeval` stored
**359 rows / 359 ok** sha256-16 `01c1ee0b6e7f6d5d`. That exit 3 is the guard answering correctly on
the owner decision, not an incident. `~/pub-bench/GROK-CANCELLED` untouched, no window guard re-armed.

**A belief I carried into this tick and had to discard by checking, not by reasoning.** The compacted
notes of the previous run described a `gpqa-diamond` codex leg "still pending after two transport
timeouts, relaunch once with a longer timeout". There is no such pending leg: `git status` shows no
running `parb-pub-*` unit and no `pub_bench_cloud.py` process, and the stored log
`~/pub-bench/cloud-gpqa-codex.log` ends `codex done: ok=198 bad=0 wall 3553 s -> …/gpqa-diamond/pub-codex.jsonl`
and `cloud gpqa codex exit=0`. The arm is complete at **198/198 stored rows**, published at
**174/198 = 87.9 %**; a relaunch would have been a duplicate leg burning a subscription window on a
set that already has its cell. Rule followed: read the artifact before honouring the note.

**One new reading, and it is a GO.** `preflight-20261116-1249.txt` (wrapper run bare, rc captured
unshielded): engine pid 438502 state S, sampled pcpu 1.0 %, RSS **54 483** MiB, `engine_vmswap_mib`
**0**, GPU mean 0.0 % / peak 0 % at 27.17 W, whole-disk read 0.1 MiB/s (top reader `basalt`,
`blk_scope=whole-disk`), swap in use **65** of 65 535 MiB with SwapCached 9 MiB, `foreign_legs=0`,
`/health` 200 with `health_loaded=true`, one serve process, producer window measured **6.14 s** →
`PREFLIGHT GO`, gate rc 0. Window transition as the tool derives it (previous bound = previous stored
reading): prev window as-of 12:40 held 31 readings / 10 launchable, this window as-of 12:49 holds 32
readings / **11 launchable**, aged out **0**, newly inside **1**, launchable delta **+1**. Corpus at
run time: **171 files, 83 GO / 82 NO-GO / 6 input gap**.

**The substantive change: the census had never quoted a distance to the only threshold in force that
is a STATE.** Every rule this table bands is a rate over one 6 s window. The gate has always had a
memory rule too — `mem-available-low`, floor `MEM_AVAILABLE_MIN_MIB = 2048`, read out of the gate
source at run time like every other ceiling — and the producer has always printed `mem_available_mib`
and `engine_rss_mib`, yet in 204 ticks no published cell ever carried a headroom band, a distance to
that floor, or an RSS difference, because every tick wrote headroom into a prose sentence next to a
verdict and moved on. That prose hid a regime change which the rate rules are structurally blind to:

| engine generation (day scope, printed by the tool) | MemAvailable | swap in use | engine RSS |
| --- | --- | --- | --- |
| pid 175316, 11 draws, last at 07:19 | 18 647 → 19 297 MiB | **16 062 → 16 839 MiB** | 57 048 → 56 654 MiB |
| pid 438502, 6 draws, last at 12:49 | **6 618 → 4 855 MiB** | **65 → 65 MiB** | 52 711 → **54 483** MiB |

The row the block exists for: `pid 175316 (preflight-20261116-0719.txt) → pid 438502
(preflight-20261116-1007.txt): REGIME FLIP — swap in use fell 16 774 MiB (16 839 → 65) while
MemAvailable fell 12 679 MiB (19 297 → 6 618) across the restart`. The two free columns moved in
**opposite** directions: the new process re-admitted into RAM what the old one held in swap and spent
almost 13 GiB of headroom doing it. That is also, mechanically, why the page-in storms this line
spent ticks 196/199/200 on (6.82×, 6.91×, **10.69×** of the 20.0 MiB/s swap ceiling) simply stopped —
there was nothing left swapped to page in. The box's risk moved from swap throughput to distance to
the gate's own memory floor, and a table of rates could not see the transition at all: the 05:41 and
06:43 refusals belong to the old generation, and every window the new generation has sampled prints a
swap peak of **0.0 MiB/s** with 65 MiB of swap in use — the two halves of the day are not the same
machine state, and the rate bands pool them as if they were.

What v13 prints (10 new rows at three scopes, all computed): headroom coverage; the MemAvailable band
with the file that set the minimum (**min 4 855 MiB (`preflight-20261116-1249.txt`), median 18 647,
max 21 441 over 17 readings** at day scope, median 19 188 over 32 at 24 h, median 19 041 over 170 at
corpus); the newest draw against the floor (**4 855 MiB = 2 807 MiB above 2 048, 2.37× the floor,
verdict GO**); the closest approach with a state word (**THE MINIMUM IS THE NEWEST DRAW — headroom is
falling, not resting**); the per-generation MemAvailable / swap-in-use / RSS trajectory with the
trailing monotone run; an attribution row (**RSS grew 1 772 MiB against a headroom fall of 1 763 MiB,
the sampled engine accounts for 101 % of it, residual 9 MiB — `ATTRIBUTED TO THE SAMPLED ENGINE`**,
and the same cell prints `UNATTRIBUTED` when the engine's RSS did not grow, i.e. it refuses to charge
the sampled process for memory it did not take); the trend row (**6 consecutive decreasing draws lost
1 763 MiB over 162 min = −653.0 MiB/h, mean cadence 32.4 min; `PROJECTION (not a promise, one
generation, n=6)`: at that constant slope the gate's own 2 048 MiB floor arrives ≈258 min after
`preflight-20261116-1249.txt`, about 7 further readings** — the row carries the word projection inside
the cell, and it needs ≥3 monotone draws to say anything, two points being a line and not a trend);
the restart flip row; the pid-less-reading count; and an impossible-field row.

**Two honesty notes on that projection, both published rather than smoothed.** (a) The cadence inside
the run is not a uniform cron cadence: 12:40 and 12:49 are two manual draws 9 minutes apart, so
"about 7 further readings" is cadence-dependent and the minute figure (≈258 min) is the one to read.
(b) A headroom fall ending in a floor breach is a *refusal*, not a crash, and the rule that fires is
already wired — so nothing was armed here and no ceiling was registered. The block prints the evidence
a decision needs, not the decision.

**A published field caught being physically impossible.** The impossible-field row reports
`preflight-20261111-0336.txt` carrying `engine_rss_mib=58 929 928` against `mem_total_mib=61 953` —
an RSS 951× the machine's whole memory, in a corpus where the same process reads 57 470 MiB two
windows later, i.e. a KiB value inside a MiB column. It is now named in the table and **excluded from
every delta**, because that is exactly the scale bug that would have made an attribution ratio read
~1000 % instead of 101 %. No published percent, band or sign test consumes an RSS delta, so nothing
published needs correcting; the guard exists so the next such reading cannot enter arithmetic quietly.
Coverage at this cut: 170 of 171 corpus readings carry a parseable `mem_available_mib`.

**Non-retroactivity, proved by replay, not asserted.** Old bytes (HEAD blob `9343efd5…`, verified
against `git rev-parse HEAD:scripts/pub_preflight_census.py`, `CENSUS_STAMP = 12`) and new bytes
(`CENSUS_STAMP = 13`) run side by side over every stored reading at the same
`--as-of 20261116-1255 --no-transition`, each in its own directory of symlinks so neither sees the
other. Diffed as parsed **(label → value) pairs, not lines** (tick 204's lesson: a long cell that grew
is invisible to a line count): **old 100 rows, new 110 rows, cells moved 0, rows removed 0, rows added
10** — every added row is a headroom row. Gate sha16 `dd2f0e4fa0255fa5` printed identical in both runs
(the gate was not touched), only the stamp sentence moved, and the preserved-shape sentence regenerated
itself to "v1 … v12 tables are left published exactly as written; a file stamped any of them is not the
same table shape as this v13 one".

**Gates on this head.** `harness/pub_preflight_census_test.py` **297/297 green** (was 278: 19 new
checks, each with its non-vacuity twin — a rising series must NOT project, one engine generation must
print `no denominator` rather than "no flip", a headroom fall with a flat RSS must print `UNATTRIBUTED`,
two decreasing draws must refuse, an RSS above `mem_total_mib` must be named and must cost the
attribution row its denominator). `pub_preflight_census.py --check` **0** against the committed v13
table at the 12:49 window. Five pub publication gates unshielded: `pub_arms_index --check`,
`pub_derived_percent_check`, `pub_grok_cell_check`, `pub_superseded_cell_check`, `pub_digest_row_check`
all **rc 0**. `scripts/qa/static_checks.py` and `verify_manifest.py --v6` re-run on the tree below.
`scripts/security/secret_scan.py --dir . --strict` re-run after the commit, unshielded.

**LEG-INCIDENTS.md got one entry, written retrospectively.** The engine restart that moved the
endpoint from pid 175316 to pid 438502 (between the 07:19 refusal and the 10:07 GO, which is also a
Basalt restart — the alias/serve pair came up 2 h 49 min before the 12:49 draw) had never been
recorded, because no leg was in flight when it happened. Zero arm bytes touched, zero verdict moved;
what it did change is which process owns every pooled footprint and headroom figure in the corpus,
which is the event census v11 and v13 now print. Recorded late rather than never, and labelled as
late.

Next: the trend row is now recomputed at every cut, so the headroom question stops being a prose
question. If a future draw prints `BELOW the floor`, that is the gate's own `mem-available-low` rule
refusing, attributed by the v9 rule table in the same run. No new rule was armed and no ceiling
registered this tick.

## Tick 206 — 2026-11-16 13:37 CET: the headroom projection labelled itself a projection but its second number rested on an unstated uniform-cadence assumption — census v14 puts the sampling interval in the cell

**No leg launched: the queue is empty as arithmetic.** `scripts/pub_three_arm_parity_check.py`
**49 rows / 9 sets / 0 findings** (contour stamp 0.0.2.56, Grok not an arm), so there is no set whose
bare row is waiting for a matched contour row. `scripts/pub_grok_resume_check.py --as-of 2026-11-16`
read unshielded, code captured on the next line: **22 checks, exit 3, `RESUME GATE: NO-GO — do not
spend quota`**; `ifeval` stored **359 rows / 359 ok** sha256-16 `01c1ee0b6e7f6d5d`, **182 ids never
asked** and printed as VOID (the owner cancellation, not a queue). `~/pub-bench/GROK-CANCELLED`
untouched, no window guard re-armed, zero model calls this tick.

**Two stored readings, both gated fresh with the return code captured on the line after the call**
(the tick-173 rc trap): `preflight-20261116-1305.txt` **rc 0 GO** — `mem_available_mib=4789`,
`engine_rss_mib=54542`, `engine_state=S`, `swap_used_mib=65`, `engine_pcpu=1.1`,
`gpu_util_mean_pct=0.0`; `preflight-20261116-1337.txt` **rc 0 GO** — **4729 / 54597 / S / 65 / 1.0 /
0.0**. The producer wrapper was re-read rather than trusted and still ends `exit "$GATE_RC"`, so its
return code is the gate's. Window transition 13:05 → 13:37 (stdout evidence only): both windows hold
**32 readings**, launchable **12 → 13**, one NO-GO aged out (`preflight-20261115-1337.txt`) and one
GO entered (the 13:37 draw). Corpus **173 readings**.

**A number this line quoted is not in the corpus, and the correction goes in the log rather than
silently.** A reading time of `13:11` with `MemAvailable 3 717 MiB` was carried forward from the
compacted notes of the previous run and repeated in chat. There is no `preflight-20261116-1311.txt`,
and `grep -l mem_available_mib=3717` over all 173 stored readings returns **nothing** — the value
never existed in any file. The two real readings are the 13:05 and 13:37 draws above. Same class as
tick 205's phantom `gpqa-diamond` codex leg: a figure that survives context compaction stops being
re-derived, and this line's own rule (every statistic is COMPUTED by the reporter at every run, prose
may only quote the printed cell) applies to numbers quoted from notes as much as to numbers in a
table.

**The census finding of this tick: the projection's second number had an undeclared denominator.**
The headroom trend row v13 prints at this cut is correct in its first half and unsound in its second:
the newest engine generation (pid 438502) fell **1 889 MiB over 210 min = −539.7 MiB/h** across 8
consecutive decreasing draws (`preflight-20261116-1007.txt` → `preflight-20261116-1337.txt`), and the
gate's own `mem-available-low` floor of **2 048 MiB** sits **≈298 min** past the newest draw at that
slope. v13 then divided 298 by the run's **mean cadence 30.0 min** and printed **`about 9 further
readings`**. The mean is not the run: the seven intervals behind it are **28, 39, 35, 51, 9, 16 and
32 min** — a **5.7x** spread containing a 9-minute gap, because these draws are taken by ticks and
reports, not by a scheduler. The same 298 minutes is **5 readings** at this run's slowest interval and
**33 at its fastest**, so `9` was not a conservative bound, it was an assumption about how often the
producer runs. That is the producer rule already written on this line — *divide by a MEASURED window,
never a nominal count* (the 6 s loop that measured 6.17 s, tick 14.11) — arriving one level further
down, inside a cell that had the honesty to label itself a projection.

**Census v14.** The minutes stay the primary quantity; the reading count is printed as the band the
run's own intervals support, with its denominator in the cell: `in READINGS 5-33 further draws,
because the run's own intervals span 9-51 min (7 interval(s), 9-51 min, mean 30.0), a 5.7x spread:
v13 divided the minutes by that mean alone and printed the single number 9, which this run's interval
range refutes by 5.7x`. It collapses to one count only when the intervals are uniform within
`MEM_INTERVAL_FLAT_RATIO = 1.5` (then `≈9 further draws, a single count being admissible at this
cadence (7 interval(s), 30-30 min, mean 30.0)`), and prints **no count at all** when no positive
interval exists — two draws sharing a timestamp must never reach a denominator. The cell also names
the old number instead of replacing it, so the published history stays citable. **Nothing armed, no
threshold touched, no ceiling registered**: the floor is the gate's own `MEM_AVAILABLE_MIN_MIB =
2048`, the 13:37 draw sits at 4 729 MiB = 2.31x above it, and the row is still a projection, not a
forecast — one generation, n=8.

**Reporter-only proof by replay, at the SAME cut, parsed as (label → value) pairs and not as lines.**
Old bytes (`git show HEAD:scripts/pub_preflight_census.py`, `CENSUS_STAMP = 13`) and new bytes
(`CENSUS_STAMP = 14`) run side by side over all 173 readings at `--as-of 20261116-1337
--no-transition`: **110 table rows in both, 0 rows removed, 0 rows added, exactly 1 cell moved** — the
headroom trend row — plus the stamp sentence and one new prose block. Gate sha16 `dd2f0e4fa0255fa5`
printed identical in both runs (the gate was not touched). The committed table is now the v14 tool's
own output at the 13:37 window and `pub_preflight_census.py --check` re-derives it with **0 diff
lines, rc 0**.

**Gates on this head.** `harness/pub_preflight_census_test.py` **308/308 green** (was 297: 7 new
checks, the band pair being non-vacuity twins — the same eight values at a uniform 30 min cadence
must collapse to `≈9` and must NOT print a band, so the band is provably arithmetic over the cadence
and not a template; plus the printed denominator, the named old number, a direct pin of
`_positive_intervals` dropping zero and negative gaps so the fail-closed branch is not decorative, and
two structural pins that v13's mean-only phrasing cannot come back). `harness/pub_preflight_test.py`
**117/117**. Five pub publication gates unshielded: `pub_arms_index --check` (index drift 0),
`pub_derived_percent_check` (42 recomputed from shipped bytes, 0 findings), `pub_grok_cell_check` (9
documents, 0 findings), `pub_superseded_cell_check` (9 documents, 0 findings), `pub_digest_row_check`
(49 rows, 0 findings) — all **rc 0**. `scripts/qa/static_checks.py` **rc 0** (the local CI-parity loop
runs the census test by glob) and `harness/verify_manifest.py --v6` **VERIFY PASS**.
`scripts/security/secret_scan.py --dir . --strict` re-run after the commit, unshielded.

**Cron state read from the job table, not assumed:** `PUB benchmark loop 30m` last **ok** 13:06,
`sah-publication-watchdog` last **ok** 11:13, `GitHub docs freshness daily` last **error** at 03:00:40
— the standing daily failure because the working tree is dirty during its run, reported not fixed, no
in-flight work committed to make it green.

**LEG-INCIDENTS.md: nothing to add.** No leg started, no engine restart, no partial file discarded, no
duplicate launch; the two gate runs above re-judged stored readings and touched no byte.

Next: the reading-count band is recomputed at every cut, so the only forward-looking number on this
line now carries the sampling cadence it was divided by. If a future draw prints `BELOW the floor`,
that is the gate's own `mem-available-low` rule refusing, attributed by the v9 rule table in the same
run. The queue stays empty until a new ladder item is pre-registered.
