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
