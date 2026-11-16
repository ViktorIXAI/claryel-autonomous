#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PUB preflight reading census: every stored endpoint reading re-judged by the CURRENT gate.

Why (line discipline, ticks 145-153): every tick restated a "reading census" (N files,
x GO / y NO-GO / z input gaps) plus a swap-peak band and an arming counter, and the numbers
were re-derived by hand every time. Two denominators live in that one paragraph and they are
NOT the same set:

  * the VERDICT set - the gate's own exit code per file;
  * the SWAP-MEAN-RULE set - files whose sampled swap window passes SWAP_RATE_MAX_MIB_S.
    A reading can be NO-GO on the device or GPU rule with the swap mean quiet (peak 0.0), and
    a reading can be an INPUT GAP (a NaN field the gate refuses to judge) while still carrying
    a big peak. Counting either of those into the band invents a separation that does not exist.

So the census is a tool: it runs `scripts/pub_preflight.py` as a subprocess over every stored
reading (the gate's returncode, never a restatement), and derives the band and the arming
counter from the rule the band is defined on, printing both denominators side by side so the
misreading cannot recur.

A third denominator the first version of this tool got wrong (2026-11-14 18:47): the gate's own
device ceiling is SCOPE-DEPENDENT (`BLK_READ_MAX_MIB_S_WHOLE = 50.0` for readings carrying
`blk_scope=whole-disk`, `BLK_READ_MAX_MIB_S = 100.0` only for readings with no scope key, the old
diskstats sum that double-counts partitions). The first table named only 100.0 and labelled it
"whole-disk scope", so the printed table contradicted the verdicts it was reporting: the 18:47
reading (whole-disk, 56.2 MiB/s) is a gate NO-GO while the table implied its ceiling was 100.0.
The table now prints both numbers beside their scope and counts the readings per scope; the
contract test pins both ceilings by driving the REAL gate on the same device number with and
without the scope key (60.0: NO-GO scoped, GO unscoped).

A fourth cell the first two versions got wrong (2026-11-15 01:00): the header printed
"N stored readings, M inside the window", where N is the CORPUS-WIDE count of reading files
present at run time. That number moves when a reading is taken AFTER the frozen window, so a
`--check` of an untouched snapshot reported drift on correct bytes: at the committed window
`as-of 2026-11-14 23:47` the line went from "123 stored readings, 123 inside the window" to
"124 stored readings, 123 inside the window" — no verdict moved, no reading was edited. The
usage note had promised that "a committed snapshot is reproducible while the readings are
retained", and the corpus count was the one cell that broke that promise, so the table now
prints only the window-scoped count and the corpus count is reported on stdout, outside the
committed file. Census stamp `v2` -> `v3`; v1 and v2 tables stay published as written.

A fifth cell this tool did not compute, and the tick note that got it wrong (2026-11-15 07:14,
tick 172): every tick since tick 145 has hand-attributed the 24 h launchable-window count with a
sentence of the form "N -> M with zero reclassification - exactly one named file aged past the
cutoff, X, re-run at rc 0". The table never carried that attribution, so nothing checked it. At the
committed window `as-of 2026-11-15 06:37` the published tick note claimed the launchable count went
"22 -> 23 (this reading inside; nothing aged out this window)". The tool's own tables for the two
consecutive windows say **22 -> 22**, and a launchable window DID age out:
`preflight-20261114-0614.txt`, gate rc 0 (GO), between the 05:57 cutoff (2026-11-14 05:57) and the
06:37 cutoff (2026-11-14 06:37). One entering GO and one leaving GO net to zero, which is exactly
the case the hand sentence could not see. Same class as ticks 155/162/163/166 — a report that states
what it did not compute — and this time the un-computed part is now the tool's job: every census run
prints the window transition on stdout (bound = the previous stored reading unless `--prev-as-of
YYYYMMDD-HHMM` names one; `--no-transition` silences it). It names the readings that aged out and
the ones that newly entered, each with its gate returncode and a `launchable` marker, plus the
launchable delta written as its own arithmetic `A -> B = +n_new_GO - n_aged_GO`. The block is stdout
evidence only: it joins no committed table, which stays byte-identical with or without it.

A sixth set of cells this tool did not compute, and the tick prose that went stale over them
(2026-11-15 23:08, tick 192): the day's refusal band, refusal MEDIAN and the GO/refusal "dead
zone" existed only as sentences in tick notes, and each tick re-typed them. Recomputed with a
scratch parser over the same reading files, the swap-rule refusal median is **4.225x at the
24-reading cut, 3.985x at the 30th and 3.745x at the 31st**, while two consecutive ticks quoted
"4.22x" as the current day's figure — the number was never wrong for its own cut, it simply stopped
being recomputed. The band edges and the dead-zone bounds had the same exposure. The census now
prints a DAY table whose rows come from the same per-file gate returncodes as the verdict census:
GO/refusal swap-ratio bands, the recomputed median, refusals decided by a rule OTHER than swap
(named, so they cannot pollute the swap band), the dead zone with a computed EMPTY/POPULATED state
word and the count inside it, the longest consecutive-refusal run, readings since the day's last
GO, and the age of the launchable-footprint maximum plus how many trailing day windows sit above
it. Census stamp `v4` -> `v5`; v1-v4 tables stay published as written.

A seventh set of cells the DAY table cannot answer (2026-11-16 00:04, tick 193): the day table is
scoped to the calendar day, so at the first reading of a new day it prints a longest refusal run of
**1** and `n/a — no GO of this day` even when the box has been refusing readings continuously since
the previous evening. Measured live at that reading: four consecutive NO-GOs across midnight
(21:57, 22:32, 23:08 on 15 Nov, 00:04 on 16 Nov) and the last GO 162 minutes earlier at 21:22, one
of the 7 launchable windows the same table counts in the last 24 h — so the day cells were true as
labelled and misleading as a streak, the same failure class one level down from the stale median
above. The tool now also prints a window-scoped continuity block over the sliding `--window-hours`
span: the trailing NO-GO run ending at the newest reading (any-verdict non-GO run beside it), the
readings since the last gate-GO with that reading named and its age in minutes, and a computed
window-run-vs-day-run state word (`MATCHED` or `MIDNIGHT RESET` with both counts). Census stamp
`v5` -> `v6`; v1-v5 tables stay published as written.

A third scope defect in the SAME cells (2026-11-16 01:50, tick 195): the rule band existed only at
DAY scope, and a dead zone is a function of the row set it is measured over. Measured at this cut,
the same 20 MiB/s ceiling gives a day-scoped dead zone **0.00-1.27 x wide** (25.3 MiB/s, 1 GO draw)
while the whole corpus of 158 readings puts the highest launchable swap draw at **0.905 x** and the
lowest swap-rule refusal at **1.06 x**: a **0.155 x = 3.1 MiB/s** band, empty across the 25
launchable draws and 35 swap-rule refusals that carry a parseable swap window. Only 70 of those 158
files carry `swap_in_mib_per_s` / `swap_out_mib_per_s` at all (the producer added them
2026-11-14 09:26), so a corpus band is a statement about the sampler era since that hour and the
excluded files are excluded by the rule, not silently, i.e. the corpus zone is **8.2x narrower**
than the day cell a reader would quote. The day cell is
correct as labelled, but every tick sentence that said "the dead zone" (2026-11-15: "0.38-1.06 x",
then "0.74-1.06 x") was a day-scoped number presented as a property of the rule. The census now
prints the same band arithmetic at three scopes — the `as-of` calendar day, the sliding
`--window-hours` span, and the whole corpus — each labelled with its scope word, plus a computed
state word naming the widest and narrowest interval at this cut. Census stamp `v6` -> `v7`; v1-v6
tables stay published as written.

A fourth defect in the SAME column (2026-11-16 02:55, tick 196): the band's bounds mixed two
denominators while a single row quoted one claim. `go_max`/`ref_min` bound the interval on the gate
VERDICT (the GO column), and the row label plus every tick sentence read it as the swap RULE's
resolution. On the committed 2026-11-16 02:14 window the swap rule has accepted a draw the gate
never launched: `preflight-20261116-0214.txt` measures swap 0.0 in + 18.8 out = **0.94 x** of the
20.0 MiB/s ceiling and the swap rule PASSED it (the reading was refused instead by the device,
state-D and GPU-mean rules), so the rule is measured accepting at 0.94 x while the v7 corpus row
put the top of the "dead zone" at 0.905 x and counted that very accepted draw as `POPULATED (1
windows inside)` evidence that the band is unmeasured. The rule's own band is **0.940-1.060 x
(0.120 x = 2.4 MiB/s)** at corpus scope, not 0.905-1.060 x (0.155 x = 3.1 MiB/s), and the POPULATED
word vanishes at all three scopes for a structural reason: a judged draw strictly between the
accepted maximum and the refused minimum cannot exist, because such a draw is below the ceiling
(accepted, so it moves the upper bound up) or at/above it (refused, so it moves the lower bound
down). The census now prints BOTH quantities with their denominator in the label — the "swap-rule
decision boundary" and the "launchable-column gap ... VERDICT-scoped" — the boundary row states its
occupancy as EMPTY BY CONSTRUCTION and names input-gap readings inside the band separately, because
an unjudged reading carries traffic without a rule decision, and a computed rule-boundary scope
state compares widths only, since occupancy cannot differ there. Census stamp `v7` -> `v8`; v1-v7
tables stay published as written.

An eighth set of cells this tool did not compute (2026-11-16 03:47, tick 197): the table counts WHICH
VERDICT a reading got and — for the swap rule only — whether the sampled window passed its ceiling. It
never counted WHICH GATE RULE refused. Every tick attributed refusals in prose ("the night's first
out-heavy swap window", "02:14 died on the device, state-D and GPU-mean rules"), and no such sentence
was ever computed. The census now reads the gate's own refusal text (the strings the gate appends to
its NO-GO block, not a restatement) and counts every rule at the three published scopes, each rule row
labelled with the gate's own reason prefix so a rename cannot hide behind a friendly id. Two fail-closed
paths: a refusal reason the census cannot map to a rule prints as `UNATTRIBUTED`, is named, and moves
the exit code to 4; and the rule table is BOUND to the gate source (every anchor prefix must appear in
it, and the number of refusal sites in the gate must equal the number the table claims), so a gate edit
that renames or adds a refusal reason reddens the census even when no stored reading exercises it — the
pin-the-binding-not-the-presence rule of tick 155 applied to the rule vocabulary. The attribution is
also cross-checked against the band: the set of refusals whose swap window sits at or above the ceiling
(derived here from the key=value columns) must equal the set whose gate reason line names the swap rule
(the gate's own claim about itself). Two independent derivations of one set: a parser change, a ceiling
change, or a rule edit shows up as a named disagreement instead of a band quietly misclassifying rows.

A tenth set of cells (2026-11-16 07:19, tick 201): the v9 attribution reads the gate's text for EVERY
rule, but only ONE rule was ever re-derived from the readings themselves — the swap band. The state
rule is the cheapest rule in the gate to re-derive (no ceiling, no scope, one substring test: the gate
fires when `engine_state` contains `D`, so a `Dl` state fires too) and the one whose refusal text is the
least checked: a gate reading the launcher's state instead of the model's, a renamed anchor, or a
producer sampling the wrong pid would move refusals while no printed cell disagreed. The census now
derives the engine-state-D set from the reading's own key and requires it to equal the set the gate's
reason line names, at all three scopes, naming the disagreeing files and moving the exit code to 4.
The same rows answer a physical question this line has been asserting in prose: among the state-D
refusals, how many sit on a device the device rule calls quiet. Measured at the 07:19 reading: swap-in
161.3 MiB/s (8.07x the mean ceiling) with `blk_read_mib_per_s=0.1` at whole-disk scope and 7 274 MiB —
43.2 % of swap in use — page-cache resident, i.e. an uninterruptible wait served out of RAM rather than
off the NVMe, which is tick 200's finding seen from the state side. The row prints that count at three
scopes WITH its denominator (state-D refusals carrying a parseable device window), because a state-D
reading taken before the device key existed cannot be classified either way and a silent smaller
denominator is how a band starts describing only the sampler era. Census stamp `v9` -> `v10`; v1-v9
tables stay published as written.

A stale enumeration in this tool's OWN header, found while extending it (same tick): the stamp sentence
closed with "v1, v2, v3, v4, v5 and v6 tables are left as published; a v1, v2, v3, v4, v5 and v6 file
are not the same table shape" — written when the stamp was v7 and never touched again, so the v7 change
(30 rows added) and the v8 change (9 rows added, 5 relabelled) were each announced as the reason a shape
differs while the sentence saying WHICH shapes are preserved stopped two stamps short. A reader following
that sentence would treat a v6 and a v8 table as interchangeable, exactly the error the sentence exists to
prevent. The sentence is now generated from the stamp number, and the contract test pins that it covers
v1..(stamp-1) for the current stamp AND for a hypothetical later one, so the next bump cannot quietly
reintroduce the gap.

A ninth set of cells this tool could not compute, and the live cut that proved it mattered
(2026-11-16, tick 207): the corpus attributes every reading to an engine PROCESS (the producer's
`# engine pid=` comment) and never to an engine BUILD. The two axes answer different questions —
a pid asks "did this process swap?", a build answers "was this build ever refused?" — and on
2026-11-16 they disagreed: every one of the day's nine refusals was recorded against pid 175316
(retired at 09:59) while the live pid 438502 had produced nine GOs and zero refusals. The 09:59
restart was simultaneously a BUILD swap (serve context 262 144 -> 196 608, the sampling header
gone from the log, the binary path moved), and not one of the 174 readings stored that day carries
a byte naming the build. The producer now emits `health_body_sha16` (SHA-256/16 of the /health body
the `health_loaded` rule already fetches — zero extra fetches) and `health_max_context` (the same
body's advertised context), and the gate validates the pair without ever gating on it (absent =
coverage line, malformed or one-sided = input gap). The table gains the build-coverage split, the
per-build detail (verdict mix, span, pid set) and the pid-vs-build crosswalk, so a verdict can
finally be credited or blamed to a named build instead of an possibly-retired process. Census
stamp `v14` -> `v15`; v1-v14 tables stay published as written.

It moves no published benchmark byte and registers no contour feature.

Readings live OUTSIDE this repository (the producer command is untracked by the same rule that
keeps connection material out of the repo), so this census is not CI-enrolled: its arithmetic is
pinned by harness/pub_preflight_census_test.py over synthetic readings instead.

Usage:
  pub_preflight_census.py                     census over ~/pub-bench up to the newest reading
  pub_preflight_census.py --as-of 20261114-1755   freeze the window (a committed snapshot is
                                              reproducible while the readings are retained)
  pub_preflight_census.py --dir DIR [--day YYYYMMDD] [--window-hours 24]
  pub_preflight_census.py --markdown OUT.md   write the generated table
  pub_preflight_census.py --check OUT.md      re-derive and diff vs the committed table
                                              (exit 1 on any drift, like the bank census --check)
  pub_preflight_census.py --as-of W [--prev-as-of W2]   ALSO print the window transition on stdout
                                              only (aged-out / newly-entered readings, each with
                                              its gate rc and a launchable marker, and the
                                              launchable delta as its own arithmetic). W2 defaults
                                              to the PREVIOUS stored reading; --no-transition
                                              suppresses the block. The committed table is
                                              byte-identical with or without it.
Exit codes: 0 census written / matches, 1 census gap (missing dir, unreadable file, gate
returned something other than GO/NO-GO/input-gap, --check drift, a malformed /
not-earlier --prev-as-of, or a refusal-rule table that no longer matches the gate source),
4 census FINDING (the table was produced but a cell could not be filled honestly: a refusal
reason the rule table cannot attribute, gate output whose verdict line cannot be parsed, the
swap-band refusal set disagreeing with the gate's own swap-rule reason set, or the
engine-state-D set derived from the readings disagreeing with the gate's own state-D reason).
"""
import argparse
import datetime
import glob
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "pub_preflight.py")
NAME_RE = re.compile(r"^preflight-(\d{8})-(\d{4})\.txt$")
# Pre-registered by tick 151 and unchanged since: the peak statistic may only become a refusal
# reason once this many launchable (gate-GO) windows carry it.
ARMING_THRESHOLD = 30
# Printing bound on the `--check` drift evidence (tick 166, 2026-11-15), set far above the size of
# one census table (~70 lines) so a normal drift is printed IN FULL; if it is ever hit, the tool
# says so in words and the count line above the body already carries the whole drift.
DIFF_PRINT_MAX = 400
# Table-shape stamp. Bumping it must not require typing the "which earlier shapes are preserved"
# sentence: that sentence is GENERATED from this number (tick 197 found the hand-typed version two
# stamps short, announcing v7 and v8 shape changes while claiming only v1-v6 are preserved).
CENSUS_STAMP = 15


def census_stamp_name():
    return "pub-preflight-census-v%d" % CENSUS_STAMP


def preserved_stamp_sentence(stamp):
    """Which earlier census shapes stay published as written — derived, never hand-typed."""
    if stamp <= 1:
        return ""
    names = ["v%d" % i for i in range(1, stamp)]
    if len(names) == 1:
        listed = names[0]
    else:
        listed = ", ".join(names[:-1]) + " and " + names[-1]
    return ("%s tables are left published exactly as written; a file stamped any of them is not "
            "the same table shape as this v%d one." % (listed, stamp))


# ---------------------------------------------------------------------------
# WHICH GATE RULE refused a reading (census v9, 2026-11-16, tick 197)
# ---------------------------------------------------------------------------
# (rule id, match kind, anchor taken from the gate's own printed reason, refusal sites in the gate)
# ORDER MATTERS: the `loaded: false` reason also starts with `/health answered `, so the specific rule
# is listed first and matching stops at the first hit. `sites` is how many places in
# scripts/pub_preflight.py build this reason — refusal_rule_guard counts the real sites, so a NEW
# refusal in the gate makes the census fail closed even when no stored reading triggers it.
REFUSAL_RULES = [
    ("health-loaded-false", "prefix", '/health answered 200 but reports', 1),
    ("health-code-not-200", "prefix", '/health answered ', 1),
    ("engine-process-absent", "prefix", 'no `basalt --serve` engine process', 1),
    ("swap-free-low", "prefix", 'swap free ', 1),
    ("swap-rate", "prefix", 'live swap throughput ', 1),
    ("mem-available-low", "prefix", 'MemAvailable ', 1),
    ("device-read", "prefix", 'block-device reads ', 1),
    ("engine-state-D", "prefix", 'engine in uninterruptible I/O', 1),
    ("idle-spin", "prefix", 'idle-spin signature:', 2),
    ("gpu-busy", "prefix", 'the shared brain was busy', 1),
    ("foreign-legs", "contains", 'other leg(s) on this endpoint: one leg per endpoint', 1),
]


def refusal_rule_guard():
    """Bind the rule table to the gate source; return a problem list (empty = bound)."""
    src = open(GATE, encoding="utf-8").read()
    problems = []
    for rid, _kind, anchor, _sites in REFUSAL_RULES:
        if anchor not in src:
            problems.append("rule `%s` anchor %r no longer appears in the gate source" % (rid, anchor))
    sites = src.count("reasons.append(")
    known = sum(s for _r, _k, _a, s in REFUSAL_RULES)
    if sites != known:
        problems.append("the gate builds %d refusal reasons, the census rule table knows %d"
                        % (sites, known))
    # Census v11: the binding runs BOTH ways now. A rule the gate can refuse with and the census
    # cannot re-derive is a published attribution that rests on the gate's word alone, which is the
    # defect this census exists to close; a rule the census derives that the gate no longer has is
    # a derivation measuring nothing.
    table = {rid for rid, _k, _a, _s in REFUSAL_RULES}
    derived = set(DERIVED_RULES) | set(ALREADY_DERIVED_RULES)
    for rid in sorted(table - derived):
        problems.append("rule `%s` has a refusal site in the gate and no derivation in the census "
                        "(every rule's firing set must be computed from the readings)" % rid)
    for rid in sorted(derived - table):
        problems.append("the census derives rule `%s`, which the gate rule table does not know" % rid)
    return problems


def parse_decision(out):
    """The gate's own verdict line: (kind, texts), kind in GO / NO-GO / GAP / UNPARSED."""
    if "PREFLIGHT GO:" in out:
        return "GO", []
    if "PREFLIGHT NO-GO:" in out:
        tail = out.split("PREFLIGHT NO-GO:", 1)[1]
        return "NO-GO", [ln[4:] for ln in tail.splitlines() if ln.startswith("  - ")]
    m = re.search(r"^PREFLIGHT INPUT GAP: (.+)$", out, re.M)
    if m:
        return "GAP", [m.group(1)]
    return "UNPARSED", []


def rule_of(reason):
    for rid, kind, anchor, _sites in REFUSAL_RULES:
        if kind == "prefix" and reason.startswith(anchor):
            return rid
        if kind == "contains" and anchor in reason:
            return rid
    return None


def rule_label(rid):
    for _id, _kind, anchor, _sites in REFUSAL_RULES:
        if _id == rid:
            how = "gate reason starts" if _kind == "prefix" else "gate reason contains"
            # An anchor may itself contain inline code (the engine-process reason names the process
            # by its full path); a nested single-backtick span renders wrong in markdown, so such an
            # anchor gets a double-backtick span.
            span = ("`` %s ``" % anchor) if "`" in anchor else ("`%s`" % anchor)
            return "`%s` (%s %s)" % (rid, how, span)
    return "`%s`" % rid


def gap_class(text):
    """Class label for an input-gap reason: the gate's own leading phrase, numbers normalised.
    Printed IN FULL, never capped: the longest class in the corpus at the 2026-11-16 03:05 cut is
    182 chars because that reading is missing 13 keys, and a label truncated in the middle of that
    key list would hide WHICH keys are missing — the same defect as an unstated denominator.
    A missing-key list is also its own fail-closed risk: if the producer stops emitting a key the
    class appears with a count, and the count moving is the alarm."""
    head = text.split(" — ")[0]
    return re.sub(r"-?\d+(?:\.\d+)?", "N", head).strip()



def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def gate_constants():
    """Read the ceilings out of the gate source so the census can never disagree with it.

    Census v11 pulled the three remaining thresholds the per-rule derivations need
    (`SWAP_FREE_MIN_MIB`, `MEM_AVAILABLE_MIN_MIB`, `IDLE_SPIN_PCPU`) and the gate's own boolean
    vocabulary in here as well: a derivation that hardcoded 256 or 200 would keep printing an
    AGREES cell after the gate moved the number, which is the one failure this function exists to
    prevent. A renamed or removed constant raises, so a gate edit reddens the census instead of
    silently desynchronising it.
    """
    src = open(GATE, encoding="utf-8").read()
    out = {}
    for key in ("SWAP_RATE_MAX_MIB_S", "GPU_UTIL_MAX_MEAN_PCT",
                "BLK_READ_MAX_MIB_S", "BLK_READ_MAX_MIB_S_WHOLE",
                "SWAP_FREE_MIN_MIB", "MEM_AVAILABLE_MIN_MIB", "IDLE_SPIN_PCPU"):
        m = re.search(r"^%s\s*=\s*([0-9.]+)" % key, src, re.M)
        if not m:
            raise SystemExit("CENSUS GAP: gate source has no %s constant" % key)
        out[key] = float(m.group(1))
    for key in ("BOOL_TRUE", "BOOL_FALSE"):
        m = re.search(r"^%s\s*=\s*\(([^)]*)\)" % key, src, re.M)
        if not m:
            raise SystemExit("CENSUS GAP: gate source has no %s tuple" % key)
        out[key] = tuple(x.strip().strip('"\'') for x in m.group(1).split(",") if x.strip())
    return out


def device_scope(txt):
    """Which device-read scale a stored reading is on (mirrors the gate's own rule).

    The gate refuses at `BLK_READ_MAX_MIB_S_WHOLE` when `blk_scope=whole-disk` and at
    `BLK_READ_MAX_MIB_S` only when the key is ABSENT (the old doubled diskstats sum); an
    unrecognised value is an input gap. Naming one ceiling without naming its scope is how a
    table ends up disagreeing with the rule it claims to report, so the census reads the key per
    file and counts both groups.
    """
    m = re.search(r"^blk_scope\s*=\s*(\S*)", txt, re.M)
    if not m:
        return "unscoped"
    return "whole-disk" if m.group(1).strip() == "whole-disk" else "unknown"


# The gate's OWN key=value regex (scripts/pub_preflight.py, KEY_VALUE). The state cross-check below
# must read the field exactly as the rule that fires on it reads it: `key=value` tokens are found
# PER LINE anywhere in the line (the gate also accepts the single space-separated line the remote
# read prints, where no key sits at a line start), and a repeated key keeps its LAST value. A
# line-anchored parse here would see a state the gate never saw and the cross-check would report a
# disagreement that is only a parser difference.
GATE_KV = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=\s*(\S+)")


def gate_kv(txt):
    """The gate's parse: every key=value token, comment lines skipped, last occurrence wins."""
    vals = {}
    for line in txt.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for m in GATE_KV.finditer(line):
            vals[m.group(1)] = m.group(2)
    return vals


def state_of(txt):
    """The reading's own engine-state string, parsed the way the gate parses it (None if absent).

    The gate's state rule is `if "D" in vals["engine_state"]` — a SUBSTRING test, so `Dl` (uninterruptible
    plus lightweight) fires and a lowercase `d` does not. The cross-check mirrors that test literally
    rather than the intuitive equality test, because an equality test here would call a `Dl` refusal an
    unexplained rule firing.
    """
    return gate_kv(txt).get("engine_state")


# ---------------------------------------------------------------------------
# EVERY gate rule re-derived from the reading's own columns (census v11, 2026-11-16)
# ---------------------------------------------------------------------------
# The gate refuses with a reason STRING. v9 counted those strings, v10 re-derived two of the eleven
# rules from the stored bytes (the swap band, the engine-state substring); the other nine were the
# gate's bare word in a published table. The ceiling rules are the dangerous family: their verdict
# depends on WHICH key and WHICH constant the rule read, and 2026-11-14 measured a ceiling move
# (the whole-disk double-count, 100.0 -> 50.0 for scoped readings) that changed no refusal line's
# SHAPE at all — a rule table that only reads reason text cannot see that class. This block computes
# each rule's firing set from the columns using the constants read out of the gate source at run
# time, and requires the two sets to be equal at every published scope. `DERIVABLE_RULES` is checked
# against `REFUSAL_RULES` in `refusal_rule_guard`, so a gate that gains a refusal site reddens the
# census until its derivation exists.

def rule_fields(txt):
    """The columns the remaining gate rules compare, read through the GATE's own parse.

    None means "the columns cannot evaluate this rule": the key is absent (the rule was never fed,
    so the gate could not have fired it either — the pre-window readings) or unreadable (the gate
    answers input gap on the whole file, so that reading is not in the refusal set at all). The
    parse is `gate_kv`, not the census's line-anchored `num`, for the same reason v10 moved the
    state test: a different parser would see a different fact and report a parser difference as a
    rule disagreement.
    """
    v = gate_kv(txt)

    def f(key):
        raw = v.get(key)
        if raw is None:
            return None
        try:
            x = float(raw)
        except ValueError:
            return None
        return x if x == x else None      # NaN = a cut sample, never a value

    flag = v.get("health_loaded")
    return dict(health_code=f("health_code"),
                loaded=(flag.strip().lower() if flag is not None else None),
                serve_procs=f("engine_serve_procs"),
                swap_free=f("swap_free_mib"),
                mem_avail=f("mem_available_mib"),
                blk=f("blk_read_mib_per_s"),
                pcpu=f("engine_pcpu"),
                gpu_inst=f("gpu_util_pct"),
                gpu_mean=f("gpu_util_mean_pct"),
                foreign=f("foreign_legs"))


def derived_rule_set(rf, scope, consts):
    """(fired, not-evaluable) rule ids implied by one reading's own columns.

    Each predicate mirrors the call site in `scripts/pub_preflight.py`, including the places where
    the gate deliberately declines to claim: the idle-spin premise is the WINDOW mean when a window
    is present (a zero instantaneous sample inside a busy window is not a spin — measured
    2026-11-14 21:50), and the device ceiling is the whole-disk one only for readings that carry the
    scope key. `engine-state-D` and `swap-rate` keep their own v9/v10 rows and are excluded here so
    one rule has exactly one published cell.
    """
    fired, blind = set(), set()

    def simple(key, rid, pred):
        if rf[key] is None:
            blind.add(rid)
        elif pred(rf[key]):
            fired.add(rid)

    simple("health_code", "health-code-not-200", lambda x: int(x) != 200)
    if rf["loaded"] is None:
        blind.add("health-loaded-false")
    elif rf["loaded"] in consts["BOOL_FALSE"]:
        fired.add("health-loaded-false")
    simple("serve_procs", "engine-process-absent", lambda x: x < 1)
    simple("swap_free", "swap-free-low", lambda x: x < consts["SWAP_FREE_MIN_MIB"])
    simple("mem_avail", "mem-available-low", lambda x: x < consts["MEM_AVAILABLE_MIN_MIB"])
    simple("foreign", "foreign-legs", lambda x: x > 0)
    if rf["blk"] is None:
        blind.add("device-read")
    else:
        ceil = (consts["BLK_READ_MAX_MIB_S_WHOLE"] if scope == "whole-disk"
                else consts["BLK_READ_MAX_MIB_S"])
        if rf["blk"] >= ceil:
            fired.add("device-read")
    if rf["pcpu"] is None:
        blind.add("idle-spin")
    elif rf["pcpu"] > consts["IDLE_SPIN_PCPU"]:
        if rf["gpu_mean"] is not None:
            if rf["gpu_mean"] == 0.0:
                fired.add("idle-spin")
        elif rf["gpu_inst"] is not None and rf["gpu_inst"] == 0:
            fired.add("idle-spin")
        else:
            blind.add("idle-spin")   # high CPU and no GPU premise to judge against
    if rf["gpu_mean"] is None:
        blind.add("gpu-busy")
    elif rf["gpu_mean"] >= consts["GPU_UTIL_MAX_MEAN_PCT"]:
        fired.add("gpu-busy")
    return fired, blind


# The two rules v9/v10 already re-derive; every OTHER rule in the table must join DERIVED_RULES.
ALREADY_DERIVED_RULES = ("swap-rate", "engine-state-D")
DERIVED_RULES = ["health-loaded-false", "health-code-not-200", "engine-process-absent",
                 "swap-free-low", "mem-available-low", "device-read", "idle-spin",
                 "gpu-busy", "foreign-legs"]

# A drift or disagreement list is printed IN FULL up to this bound, with the not-printed count named
# in words (tick 166's rule: a report may not print a silent subset of its own evidence). One corpus
# refusal set is ~80 files; a cross-check that named 80 files would bury the arithmetic, so the cell
# prints its counts first and the names second, and says how many names it withheld.
DIFF_LIST_MAX = 6


def diff_names(names):
    names = sorted(names)
    if not names:
        return "none"
    shown = names[:DIFF_LIST_MAX]
    txt = ", ".join(shown)
    if len(names) > len(shown):
        txt += " (+%d more not printed)" % (len(names) - len(shown))
    return txt


ENGINE_PID_RE = re.compile(r"^#\s*engine pid=(\d+)", re.M)


def engine_pid_of(txt):
    """The engine process this reading actually sampled, from the producer's own comment line.

    The producer names the pid it picked (tick 113's lesson: a pgrep that lands on the lifecycle
    WRAPPER prints healthy numbers about a dead model), so the corpus carries an engine-GENERATION
    marker in every reading since the comment shipped. The gate never reads it — comments are
    skipped by its parser — which is exactly why no published statistic mentioned that a footprint
    band can pool two different processes.
    """
    m = ENGINE_PID_RE.search(txt)
    return m.group(1) if m else None


def parse_stamp(path):
    m = NAME_RE.match(os.path.basename(path))
    if not m:
        return None
    d, hm = m.group(1), m.group(2)
    try:
        return datetime.datetime(int(d[:4]), int(d[4:6]), int(d[6:8]), int(hm[:2]), int(hm[2:]))
    except ValueError:
        return None


def num(txt, key):
    """Parse one `key=value` reading. Returns (value, present, finite)."""
    m = re.search(r"^%s\s*=\s*(\S*)" % re.escape(key), txt, re.M)
    if not m:
        return None, False, False
    try:
        v = float(m.group(1))
    except ValueError:
        return None, True, False
    return v, True, (v == v)


def run_gate(path):
    """(returncode, stdout) from the REAL gate. The returncode is the verdict column; the stdout
    carries the gate's own refusal / input-gap text, which is what the rule attribution reads
    (census v9) — the census never restates the gate's rules in its own words."""
    p = subprocess.run([sys.executable, GATE, path], cwd=ROOT,
                       capture_output=True, text=True)
    return p.returncode, p.stdout


def census(directory, as_of, day, window_hours):
    files = sorted(glob.glob(os.path.join(directory, "preflight-*.txt")))
    if not files:
        raise SystemExit("CENSUS GAP: no preflight-*.txt readings under %s" % directory)
    named, unnamed = [], []
    for f in files:
        ts = parse_stamp(f)
        (named if ts else unnamed).append((ts, f))
    inwin = [(ts, f) for ts, f in named if ts <= as_of]
    rows = []
    for ts, f in inwin:
        rc, out = run_gate(f)
        if rc not in (0, 1, 3):
            raise SystemExit("CENSUS GAP: gate returned %s on %s" % (rc, os.path.basename(f)))
        kind, texts = parse_decision(out)
        if (rc, kind) not in ((0, "GO"), (3, "NO-GO"), (1, "GAP")) or (kind == "NO-GO" and not texts):
            # A returncode that disagrees with the gate's own verdict line is a finding, not a
            # silently empty rule cell: the attribution would then be wrong by construction.
            kind, texts = "UNPARSED", []
        txt = open(f, encoding="utf-8", errors="replace").read()
        pk, pk_present, pk_ok = num(txt, "swap_total_peak_mib_per_s")
        si, _, _ = num(txt, "swap_in_mib_per_s")
        so, _, _ = num(txt, "swap_out_mib_per_s")
        vw, vw_present, vw_ok = num(txt, "engine_vmswap_mib")
        sc, sc_present, sc_ok = num(txt, "swap_cached_mib")
        used, used_present, used_ok = num(txt, "swap_used_mib")
        if not (used_present and used_ok):
            tot, tot_p, tot_f = num(txt, "swap_total_mib")
            fre, fre_p, fre_f = num(txt, "swap_free_mib")
            used = (tot - fre) if (tot is not None and fre is not None) else None
        # Census v10 fields, read through the GATE's parser (see gate_kv): the engine-state
        # cross-check compares what the rule sees with what the rule says, and the device-quiet
        # complement needs the same device number the device rule compared. The older keys keep
        # their existing line-anchored parse so no published band cell moves retroactively.
        vals = gate_kv(txt)
        st = vals.get("engine_state")
        # Census v13 (2026-11-16, tick 205): the two FREE columns. `mem_available_mib` is already
        # gated by the gate's own `MEM_AVAILABLE_MIN_MIB` rule and `engine_rss_mib` is printed in
        # every reading, yet no published cell had ever banded either one — every headroom sentence
        # in 204 ticks was hand-typed prose ("MemAvailable 20 664 of 61 953").
        av, av_present, av_ok = num(txt, "mem_available_mib")
        rs, rs_present, rs_ok = num(txt, "engine_rss_mib")
        mt, mt_present, mt_ok = num(txt, "mem_total_mib")
        rss_val = rs if (rs_present and rs_ok) else None
        rss_bad = None
        if rss_val is not None and mt_ok and mt and mt > 0 and rss_val > mt:
            # A process cannot be more resident than the machine is large. Such a value is REPORTED
            # (the impossible-field row) and EXCLUDED from every delta, because a 1024x-scaled entry
            # silently poisons an attribution ratio: measured on the live corpus,
            # `preflight-20261111-0336.txt` carries `engine_rss_mib=58929928` on a 61 953 MiB box
            # while the same pid reads 57 470 MiB two windows later — a value emitted in KiB inside a
            # corpus that otherwise says MiB.
            rss_bad = (rss_val, mt)
            rss_val = None
        b_raw = vals.get("blk_read_mib_per_s")
        try:
            blk = float(b_raw) if b_raw is not None else None
        except ValueError:
            blk = None
        if blk is not None and blk != blk:
            blk = None    # a NaN device rate is a cut sample, never a quiet device
        # Census v15 (2026-11-16, tick 208): the engine BUILD axis. The pid comment names a
        # process; only the /health body hash names the build, and on 2026-11-16 the two axes
        # disagreed over a whole day (nine refusals on a retired pid, zero on the live one).
        id_sha, id_ctx, id_class = identity_of(vals)
        rows.append(dict(ts=ts, name=os.path.basename(f), rc=rc,
                         decision=kind, reasons=texts,
                         rules=[rule_of(t) for t in texts] if kind == "NO-GO" else [],
                         gap=gap_class(texts[0]) if kind == "GAP" else None,
                         peak=pk if (pk_present and pk_ok) else None,
                         peak_present=pk_present,
                         vmswap=vw if (vw_present and vw_ok) else None,
                         vmswap_present=vw_present,
                         cached=sc if (sc_present and sc_ok) else None,
                         used=used,
                         scope=device_scope(txt),
                         state=st, blk=blk,
                         avail=av if (av_present and av_ok) else None,
                         avail_present=av_present,
                         rss=rss_val,
                         rss_present=rs_present, rss_bad=rss_bad, mem_total=(mt if mt_ok else None),
                         rf=rule_fields(txt), pid=engine_pid_of(txt),
                         id_sha=id_sha, id_ctx=id_ctx, id_class=id_class,
                         mean=(si + so) if (si is not None and so is not None) else None))
    return rows, unnamed, as_of


RC_WORD = {0: "GO", 3: "NO-GO", 1: "input gap"}


def zone_scope_state(zones, swap_max):
    """Computed word for how much the SCOPE of a dead zone matters at this cut.

    `zones` is a list of (scope label, zone) where zone is None when that row set cannot state a
    zone (no launchable draw or no swap-rule refusal with a parseable window) or a tuple
    (lo, hi, inside). Occupancy counts, not just width: a wider row set can put a reading INSIDE a
    zone the narrower scope calls empty, and that is the difference between a boundary the rule has
    never been tested against and one it has.
    """
    present = [(k, z) for k, z in zones if z]
    missing = [k for k, z in zones if not z]

    def fmt(z):
        lo, hi, inside = z
        return ("bounds %s-%s x, width %s x (%s MiB/s), %s"
                % (xrate(lo), xrate(hi), xrate(hi - lo, 3), xrate((hi - lo) * swap_max, 1),
                   ("EMPTY (0 inside)" if inside == 0 else "POPULATED (%d inside)" % inside)))

    if not present:
        return ("NO DEAD ZONE AT ANY SCOPE — no scope holds both a launchable swap draw and a "
                "swap-rule refusal with a parseable swap window at this cut")
    if len(present) < len(zones):
        same = len({z for _, z in present}) == 1
        head = ("PARTLY UNMEASURABLE — a zone exists only at %s (%s)"
                % (", ".join(k for k, _ in present), fmt(present[0][1]))) if same else \
               ("PARTLY UNMEASURABLE — " + "; ".join("%s: %s" % (k, fmt(z)) for k, z in present))
        return ("%s; no zone at %s. Quote the scope word with any dead zone."
                % (head, ", ".join(missing)))
    if len({z for _, z in present}) == 1:
        lo, hi, inside = present[0][1]
        return ("IDENTICAL AT ALL THREE SCOPES (%s) — at this cut the scopes agree and any of them "
                "may be quoted" % fmt(present[0][1]))
    if len({(z[0], z[1]) for _, z in present}) == 1:
        return ("SAME BOUNDS, DIFFERENT OCCUPANCY — %s; the wider row sets put readings inside a "
                "zone a narrower scope calls empty: %s. Quote the scope word with any dead zone."
                % (fmt(present[0][1]),
                   "; ".join("%s %s" % (k, "EMPTY" if z[2] == 0 else "POPULATED (%d)" % z[2])
                             for k, z in present)))
    named = [(k, z[1] - z[0]) for k, z in present]
    wide_k, wide_v = max(named, key=lambda kv: kv[1])
    nar_k, nar_v = min(named, key=lambda kv: kv[1])
    tail = ("a dead zone quoted without its scope word overstates the rule's resolution by up to "
            "%.1fx" % (wide_v / nar_v)) if nar_v > 1e-9 else \
           ("at least one scope resolves the boundary exactly, so an unscoped quote carries no "
            "information")
    return ("SCOPE-DEPENDENT — the %s dead zone is %s x (%s MiB/s) wide and the %s one %s x "
            "(%s MiB/s): %s. Quote the scope word with any dead zone."
            % (wide_k, xrate(wide_v, 3), xrate(wide_v * swap_max, 1),
               nar_k, xrate(nar_v, 3), xrate(nar_v * swap_max, 1), tail))


def rule_boundary_row(d, swap_max, label):
    """One scope's SWAP-RULE decision boundary, computed on the rule's own decisions.

    Occupancy is not a column here: a judged draw strictly between the accepted maximum and the
    refused minimum cannot exist, because such a draw is itself either below the ceiling (accepted,
    so it moves the accepted bound up) or at/above it (refused, so it moves the refusal bound
    down). That is a theorem of the definition, and the row says so instead of pretending the
    band is an untested region the corpus might one day fill. What the band DOES measure is the
    rule's resolution at this cut, and the input-gap readings inside it are named because they are
    traffic evidence without a rule decision.
    """
    if d["accept_max"] is None or d["ref_min"] is None:
        return ("| %s | %s |"
                % (label, "NO BOUNDARY at this scope (no swap-rule-accepted draw or no swap-rule "
                          "refusal with a parseable swap window)"))
    w = d["ref_min"] - d["accept_max"]
    return ("| %s | accepted up to %s x, refused from %s x, unresolved band %s x (%s MiB/s) — %s; "
            "judged draws inside are impossible by the definition above, input-gap readings inside: "
            "%s |"
            % (label, xrate(d["accept_max"]), xrate(d["ref_min"]), xrate(w, 3),
               xrate(w * swap_max, 1), d["rule_state"],
               (", ".join("%s at %s x" % (n, xrate(v)) for n, v in d["gap_inside"])
                if d["gap_inside"] else "none")))


def boundary_scope_state(bands, swap_max):
    """Computed word for how much the SCOPE matters for the rule's OWN boundary (census v8).

    `bands` is a list of (scope label, boundary) where boundary is None when that row set cannot
    state one (no accepted draw, or no refusal with a parseable window) or a tuple
    (accepted_max, refusal_min). Unlike `zone_scope_state` there is no occupancy to compare — the
    band is empty by construction at every scope — so the only thing that varies with the row set
    is the WIDTH, i.e. the resolution the rule actually has, and which scopes may be quoted.
    """
    present = [(k, b) for k, b in bands if b]
    missing = [k for k, b in bands if not b]

    def fmt(b):
        a, r = b
        return ("accepted <= %s x, refused >= %s x, band %s x (%s MiB/s)"
                % (xrate(a), xrate(r), xrate(r - a, 3), xrate((r - a) * swap_max, 1)))

    if not present:
        return ("NO RULE BOUNDARY AT ANY SCOPE — no scope holds both a swap-rule-accepted draw and "
                "a swap-rule refusal with a parseable swap window at this cut")
    if len(present) < len(bands):
        same = len({b for _, b in present}) == 1
        head = ("PARTLY UNMEASURABLE — a rule boundary exists only at %s (%s)"
                % (", ".join(k for k, _ in present), fmt(present[0][1]))) if same else \
               ("PARTLY UNMEASURABLE — " + "; ".join("%s: %s" % (k, fmt(b)) for k, b in present))
        return ("%s; no boundary at %s. Quote the scope word with any rule boundary."
                % (head, ", ".join(missing)))
    if len({b for _, b in present}) == 1:
        return ("IDENTICAL AT ALL THREE SCOPES (%s) — at this cut the scopes agree and any of them "
                "may be quoted" % fmt(present[0][1]))
    named = [(k, b[1] - b[0]) for k, b in present]
    wide_k, wide_v = max(named, key=lambda kv: kv[1])
    nar_k, nar_v = min(named, key=lambda kv: kv[1])
    tail = ("quoting the boundary without its scope word misstates the rule's resolution by up to "
            "%.1fx" % (wide_v / nar_v)) if nar_v > 1e-9 else \
           ("at least one scope resolves the boundary exactly, so an unscoped quote carries no "
            "information")
    return ("SCOPE-DEPENDENT — the rule's unresolved band is %s x (%s MiB/s) wide at %s and %s x "
            "(%s MiB/s) at %s: %s. Quote the scope word with any rule boundary."
            % (xrate(wide_v, 3), xrate(wide_v * swap_max, 1), wide_k,
               xrate(nar_v, 3), xrate(nar_v * swap_max, 1), nar_k, tail))


def scope_band_text(scopes, swap_max, window_hours):
    """The DAY rule band of census v5 (see `day_band`) measured over three row sets at once.

    Why (2026-11-16 01:50, tick 195): a dead zone is a property of the row set it is measured
    over, and only the calendar-day row set was ever published. At that cut the day cell put the
    zone at 0.00-1.27 x — 25.3 MiB/s wide — while the corpus put the highest launchable swap draw
    at 0.905 x and the lowest swap-rule refusal at 1.06 x: 0.155 x = 3.1 MiB/s, 8.2x narrower,
    empty over the 25 launchable draws and 35 swap-rule refusals that carry a swap window. Only 70
    of the 158 stored files carry those keys at all (the producer added them 2026-11-14 09:26),
    which is why the block prints its own band denominator instead of trusting the reader to know
    it. Every tick sentence that said "the dead zone" (2026-11-15: "0.38-1.06 x", then
    "0.74-1.06 x") was a day-scoped number presented as a property of the rule — the tick-192/193
    scope-word defect a third time in the same column.
    No new arithmetic: each cell below is exactly what `day_band` computes for that row set.
    """
    def band_txt(lo, hi):
        return "%s-%s x" % (xrate(lo), xrate(hi)) \
            if (lo is not None and hi is not None) else "n/a x"

    def zone(d):
        if d["go_max"] is None or d["ref_min"] is None:
            return "NO ZONE at this scope (no launchable draw or no swap-rule refusal with a " \
                   "parseable window)", None
        z = (d["go_max"], d["ref_min"], d["inside"])
        return ("%s, bounds %s-%s x, width %s x (%s MiB/s)"
                % (d["zone_state"], xrate(z[0]), xrate(z[1]), xrate(z[1] - z[0], 3),
                   xrate((z[1] - z[0]) * swap_max, 1))), z

    L = ["| rule band at three scopes (added 2026-11-16, tick 195) | value |", "|---|---|"]
    L.append("| readings this scope can band at all (verdict GO or NO-GO AND a parseable "
             "`swap_in + swap_out` window) | %s |"
             % ", ".join("%s %d of %d" % (label, d["n_window"], d["n_day"]) for label, d in scopes))
    for label, d in scopes:
        L.append("| launchable (GO) swap draws, %s | %d, band %s the %s mean ceiling |"
                 % (label, d["n_go"], band_txt(d["go_min"], d["go_max"]), swap_max))
    for label, d in scopes:
        L.append("| swap-rule ACCEPTED draws (any verdict, the rule's own denominator), %s | %d, "
                 "band %s |" % (label, d["n_accept"],
                                band_txt(d["accept_min"], d["accept_max"])))
    for label, d in scopes:
        L.append("| swap-rule refusals (window at/above that ceiling), %s | %d, band %s, **median "
                 "%s x recomputed at this cut** |"
                 % (label, d["n_swap_ref"], band_txt(d["ref_min"], d["ref_max"]),
                    xrate(d["ref_median"], 3)))
    L.append("| refusals decided by a rule OTHER than swap (window below the ceiling) | %s |"
             % ", ".join("%s %d" % (label, d["n_other_ref"]) for label, d in scopes))
    bands = []
    for label, d in scopes:
        L.append(rule_boundary_row(d, swap_max, "swap-rule decision boundary, %s" % label))
        bands.append((label, ((d["accept_max"], d["ref_min"])
                              if (d["accept_max"] is not None and d["ref_min"] is not None)
                              else None)))
    L.append("| rule-boundary scope state (computed, never asserted) | %s |"
             % boundary_scope_state(bands, swap_max))
    zones = []
    for label, d in scopes:
        ztxt, z = zone(d)
        zones.append((label, z))
        L.append("| launchable-column gap (GO max to refusal min; VERDICT-scoped, not the rule "
                 "boundary), %s | %s |" % (label, ztxt))
    L.append("| launchable-column gap scope state (computed, never asserted) | %s |"
             % zone_scope_state(zones, swap_max))
    return L


def window_rows(rows, as_of, window_hours):
    """Subset of already-judged readings that this window covers: cut < ts <= as_of."""
    cut = as_of - datetime.timedelta(hours=window_hours)
    return [r for r in rows if cut < r["ts"] <= as_of]


def transition(all_rows, as_of, prev_as_of, window_hours):
    """What actually moved between two census windows — the attribution ticks 145-171 hand-wrote.

    `all_rows` is every reading judged up to `as_of` (one gate call per file, so the same file
    cannot carry two different verdicts inside one run — this function cannot and does not claim
    to detect a reclassification caused by a gate-byte change between ticks; that surfaces in the
    --check diff). Returns the aged-out set, the newly-entered set, and the launchable delta
    written as its own arithmetic, because "+1 entering -1 leaving = 0" is precisely the case the
    hand sentence got wrong at the 06:37 window on 2026-11-15.
    """
    now = window_rows(all_rows, as_of, window_hours)
    prev = window_rows(all_rows, prev_as_of, window_hours)
    now_names = set(r["name"] for r in now)
    prev_names = set(r["name"] for r in prev)
    aged = sorted((r for r in all_rows if r["name"] in prev_names - now_names),
                  key=lambda r: r["ts"])
    new = sorted((r for r in all_rows if r["name"] in now_names - prev_names),
                 key=lambda r: r["ts"])
    la = sum(1 for r in prev if r["rc"] == 0)
    lb = sum(1 for r in now if r["rc"] == 0)
    return dict(now=now, prev=prev, aged=aged, new=new,
                launchable_prev=la, launchable_now=lb,
                aged_go=sum(1 for r in aged if r["rc"] == 0),
                new_go=sum(1 for r in new if r["rc"] == 0))


def transition_text(t, as_of, prev_as_of, window_hours, bound_note=None):
    L = ["WINDOW TRANSITION (stdout evidence only; the committed census table does not carry it):"]
    for tag, a_of, rows, launchable, note in (
            ("prev window ", prev_as_of, t["prev"], t["launchable_prev"], bound_note),
            ("this window ", as_of, t["now"], t["launchable_now"], None)):
        cut = a_of - datetime.timedelta(hours=window_hours)
        L.append("  %s as-of %s%s (covers %s < t <= as-of): %d readings, %d launchable (GO)"
                 % (tag, a_of.strftime("%Y-%m-%d %H:%M"), (" [" + note + "]") if note else "",
                    cut.strftime("%Y-%m-%d %H:%M"), len(rows), launchable))
    L.append("  aged out of the window (%d):" % len(t["aged"]))
    for r in t["aged"]:
        L.append("      %-42s rc %d  %-10s%s" % (r["name"], r["rc"], RC_WORD.get(r["rc"], "?"),
                                                 "  <- launchable" if r["rc"] == 0 else ""))
    L.append("  newly inside the window (%d):" % len(t["new"]))
    for r in t["new"]:
        L.append("      %-42s rc %d  %-10s%s" % (r["name"], r["rc"], RC_WORD.get(r["rc"], "?"),
                                                 "  <- launchable" if r["rc"] == 0 else ""))
    L.append("  launchable delta: %d -> %d = +%d entering GO - %d aged-out GO"
             % (t["launchable_prev"], t["launchable_now"], t["new_go"], t["aged_go"]))
    L.append("  (one run judges every file with the SAME gate bytes, so a reading cannot change "
             "verdict between these two windows here; a gate-byte change BETWEEN ticks moves "
             "verdicts and surfaces in the --check diff, not in this block)")
    return "\n".join(L) + "\n"


def band(rows, swap_max):
    """Swap-peak band over the SWAP-MEAN RULE, gate-judged files only."""
    judged = [r for r in rows if r["rc"] in (0, 3)]
    withpeak = [r for r in judged if r["peak"] is not None]
    passing = [r for r in withpeak if r["mean"] is not None and r["mean"] < swap_max]
    failing = [r for r in withpeak if r["mean"] is not None and r["mean"] >= swap_max]
    verdict_nogo_peaks = [r["peak"] for r in judged if r["rc"] == 3 and r["peak"] is not None]
    verdict_go_peaks = [r["peak"] for r in judged if r["rc"] == 0 and r["peak"] is not None]
    pass_max = max((r["peak"] for r in passing), default=None)
    fail_min = min((r["peak"] for r in failing), default=None)
    # Band state, computed not asserted. The first version of this tool always printed
    # "Band: nothing between <pass_max> and <fail_min>", which is a claim about the ORDER of the
    # two numbers. Measured 2026-11-14 23:13 the order reversed: one live GO window carried an
    # in-window peak of 111.4 MiB/s while the lowest mean-failing peak is 107.0, so the printed
    # sentence described an empty interval that no longer exists — the same defect class tick 155
    # caught (a generated table disagreeing with the data it reports).
    if pass_max is None or fail_min is None:
        state = "no-data"
    elif pass_max < fail_min:
        state = "separated"
    else:
        state = "crossed"
    return dict(
        n_carried=sum(1 for r in rows if r["peak_present"]),
        n_nan=sum(1 for r in rows if r["peak_present"] and r["peak"] is None),
        n_parseable_all=sum(1 for r in rows if r["peak"] is not None),
        n_parseable=len(withpeak),
        n_no_mean=len(withpeak) - len(passing) - len(failing),
        pass_n=len(passing), fail_n=len(failing),
        pass_max=pass_max, fail_min=fail_min, band_state=state,
        go_max=max(verdict_go_peaks, default=None),
        nogo_min=min(verdict_nogo_peaks, default=None),
        arming=sum(1 for r in judged if r["rc"] == 0 and r["peak"] is not None),
    )


def median(vals):
    """Median of a non-empty list, or None. Kept here so the table cannot quote a mean of a
    skewed distribution: engine VmSwap on this box ranges over an order of magnitude."""
    if not vals:
        return None
    s = sorted(vals)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def mib(v):
    """MiB cell text: an empty group prints 'n/a', never Python's None, because a reader cannot tell
    'no window carried the key' from 'the value was zero' in the word None."""
    return "n/a" if v is None else ("%.0f" % v)


def pct(v):
    return "n/a" if v is None else ("%.1f" % v)


def rate(v):
    """MiB/s cell text with the same n/a rule as `mib`: an empty group must never print the word
    None, which a reader cannot tell apart from a measured value."""
    return "n/a" if v is None else ("%.1f" % v)


def band_state_text(b):
    """The band's ORDER as one computed cell, so the table cannot assert a separation the data
    withdrew. A ceiling is only worth proposing when the two groups are separated; once the
    launchable maximum sits at or above the mean-failing minimum, every candidate threshold either
    fires where the mean rule already fires or cuts a launchable window."""
    pm, fm = b["pass_max"], b["fail_min"]
    if b["band_state"] == "no-data":
        return ("NO-DATA (one of the two groups holds no parseable peak, so no interval exists "
                "to classify)")
    if b["band_state"] == "separated":
        return ("SEPARATED — no gate-judged window has a peak between %s and %s MiB/s, so a peak "
                "ceiling could be placed in that gap without refusing any window the mean rule "
                "launches (it would still only fire where the mean rule already refuses)"
                % (pm, fm))
    return ("CROSSED — the highest launchable peak %s MiB/s already sits AT OR ABOVE the lowest "
            "mean-failing peak %s MiB/s, so the groups overlap: a ceiling high enough to spare "
            "every launchable window lets a mean-failing window through, and a lower ceiling "
            "refuses a window the mean rule launches. On this corpus a peak rule adds no refusal "
            "the mean rule does not already make" % (pm, fm))


def footprint_sep_text(fp):
    """Footprint-group separation, also computed. At the current coverage (a handful of readings
    carry the key) this cell exists to stop the medians from reading as a band."""
    return "%s (launchable %d window(s) %s-%s MiB, refused %d window(s) %s-%s MiB; n=%d/%d cannot " \
           "support a ceiling in either direction)" % (
        fp["sep_state"].upper(),
        fp["n_go_launchable"], mib(fp["go_min"]), mib(fp["go_max"]),
        fp["n_nogo"], mib(fp["nogo_min"]), mib(fp["nogo_max"]),
        fp["n_go_launchable"], fp["n_nogo"])


def footprint_info_text(fp):
    """Coverage vs INFORMATION in the footprint arming counter (census v12, 2026-11-16, tick 204).

    The pre-registered arming rule counts launchable windows CARRYING `engine_vmswap_mib`. That is a
    coverage rule, and tick 203 caught it reading as an information rule: the live engine generation
    answered 0 MiB in every window it produced, so the counter was climbing while the statistic that
    would actually set the ceiling was not being observed at all. A ceiling drawn from an all-zero
    launchable group is `> 0 MiB` — a rule armed against a failure mode nobody in the corpus has
    demonstrated on a launchable window. The cell therefore states which of the two the counter is
    buying, and refuses to let a zero draw look like a measured ceiling."""
    n = fp["n_go_launchable"]
    if n == 0:
        return ("no denominator — no gate-GO window in this window carries `engine_vmswap_mib`, so "
                "the launchable side has neither coverage nor information")
    nz, z = fp["go_nonzero"], fp["go_zero"]
    if nz == 0:
        return ("ALL-ZERO — every launchable footprint draw in this window reads exactly 0 MiB (%d "
                "draw(s)). A zero is a real measurement (that process held no swap in that window), but "
                "it sets no ceiling: the only value the arming rule allows on this coverage is "
                "`> 0 MiB`, and the refused side holds %d non-zero draw(s), so arming now would arm a "
                "rule whose failure mode has never once been observed on a launchable window of this "
                "corpus" % (n, fp["nogo_nonzero"]))
    if z > nz:
        return ("ZERO-DRAW-DOMINATED — %d of the %d launchable draws read exactly 0 MiB and only %d "
                "carry a non-zero footprint, so the arming counter is mostly coverage: the ceiling it "
                "will admit is set by %d informative draw(s), highest %s MiB"
                % (z, n, nz, nz, mib(fp["go_nz_max"])))
    return ("INFORMATIVE — a non-zero footprint in %d of the %d launchable draws (highest %s MiB), "
            "exactly 0 MiB in %d; the refused side holds %d non-zero draw(s)"
            % (nz, n, mib(fp["go_nz_max"]), z, fp["nogo_nonzero"]))


def footprint_ceiling_text(fp):
    """The footprint ceiling DRY-RUN as two computed cells: the candidate ceiling with the exact
    windows it would fire on, and the state word. This answers the arming rule's question at every
    reading instead of letting a tick hand-compute it, and it names the inert case out loud: a
    ceiling armed above every launchable footprint is worthless if no refused window in the corpus
    exceeds that footprint."""
    if fp["dry_state"] == "no-data":
        return ("n/a — no gate-GO window in this window carries `engine_vmswap_mib` (or no refused "
                "window does), so there is no ceiling to dry-run")
    base = ("ceiling > %s MiB fires on %d of %d launchable and %d of %d refused stored windows"
            % (mib(fp["dry_ceiling"]), fp["dry_fires_go"], fp["n_go_launchable"],
               fp["dry_fires_nogo"], fp["n_nogo"]))
    if fp["dry_state"] == "inert-at-minimum-ceiling":
        return "%s. The lowest ceiling the arming rule allows spares every launchable window and " \
               "refuses NOTHING in this corpus, while any ceiling low enough to refuse a refused " \
               "window (highest refused footprint %s MiB) sits at or below a launchable footprint " \
               "(highest launchable %s MiB): armed on this corpus the rule would be mechanically " \
               "inert" % (base, mib(fp["nogo_max"]), mib(fp["go_max"]))
    return "%s. A ceiling above every launchable footprint also refuses at least one refused " \
           "window, so on this corpus the state rule would have real work to do" % base


def footprint(rows):
    """Coverage and distribution of the engine swap FOOTPRINT (added 2026-11-14, tick 159).

    Deliberately NOT a band: no footprint ceiling exists, so this census counts the statistic the
    way the peak census does — how many launchable windows carry it (the pre-registered arming
    rule) — and reports the distribution without proposing a number. The reason it is censused at
    all: every swap rule in force is a 6 s RATE, and a rate cannot see a state. The stored reading
    from 21:12 that gate-answered GO with `swap_in=0.0 swap_out=0.0` sits inside an evening whose
    engine footprint grew from 5.22 to 5.72 GiB, and at 21:30 52.5 % of the swap in use was
    page-cache resident in RAM (measured with a bounded read-only sweep on the box)."""
    carried = [r for r in rows if r["vmswap_present"]]
    judged = [r for r in rows if r["rc"] in (0, 3)]
    have = [r for r in rows if r["vmswap"] is not None]
    launchable = [r for r in judged if r["rc"] == 0 and r["vmswap"] is not None]
    nogo = [r for r in judged if r["rc"] == 3 and r["vmswap"] is not None]
    shares = [100.0 * r["cached"] / r["used"] for r in rows
              if r["cached"] is not None and r["used"] and r["used"] > 0]
    go_vals = [r["vmswap"] for r in launchable]
    nogo_vals = [r["vmswap"] for r in nogo]
    # Census v12 (2026-11-16, tick 204): a footprint draw of EXACTLY 0 MiB is a real measurement —
    # that process held no swap in that window — but it carries NO INFORMATION for a ceiling whose
    # whole job is to refuse a window where the process has swapped gigabytes. Measured on the live
    # corpus: the engine generation pid 438502 (up 09:59) recorded `engine_vmswap_mib=0` in every
    # window it produced, including one taken inside its own GPU-99 %/157 W campaign at 10:35, while
    # the retired generation 175316 held 6 970-10 770 MiB across 15-16 Nov. The arming counter counts
    # launchable windows CARRYING THE KEY, so it climbs through zeros: armed at 30 such windows the
    # only ceiling the pre-registered rule allows would be `> 0 MiB`, i.e. a guard whose failure mode
    # the live process has never demonstrated once. Coverage and information are now separate cells.
    go_nonzero = [v for v in go_vals if v > 0]
    go_zero = [v for v in go_vals if v == 0]
    nogo_nonzero = [v for v in nogo_vals if v > 0]
    nogo_zero = [v for v in nogo_vals if v == 0]
    # Same rule as the peak band: the separation is COMPUTED from the two groups, never asserted by
    # a fixed sentence. With n=2 per group on the live corpus this classifies nothing yet, and the
    # table has to say so instead of printing two medians side by side and letting a reader draw a
    # line through them.
    if not go_vals or not nogo_vals:
        sep = "no-data"
    elif max(go_vals) < min(nogo_vals):
        sep = "separated"
    elif min(go_vals) > max(nogo_vals):
        sep = "inverted"
    else:
        sep = "overlapping"
    # Ceiling DRY-RUN (added 2026-11-15, tick 174) — census arithmetic, NOT a rule, and it arms
    # nothing. The pre-registered arming rule places a footprint ceiling ABOVE every launchable
    # window, so the question the rule must answer on the day it is armed is: at that ceiling, does
    # anything actually fire? A guard that can only be armed at a value nothing in the corpus
    # exceeds is not a guard — the mirror image of the tick-159 lesson ("a guard that fires by
    # accident is not a guard"). Measured live at the 08:57 reading on 2026-11-15: the launchable
    # footprint maximum (8 520 MiB) had grown PAST the refused-group maximum (6 957 MiB), so the
    # minimum admissible ceiling fires on zero stored windows while every ceiling that fires on one
    # refuses a window the gate launches. Computing this per reading is what stops the next tick
    # from hand-deriving the sentence (tick 172's class of defect).
    ceiling = max(go_vals) if go_vals else None
    fires_go = sum(1 for v in go_vals if ceiling is not None and v > ceiling)
    fires_nogo = sum(1 for v in nogo_vals if ceiling is not None and v > ceiling)
    if ceiling is None or not nogo_vals:
        # Nothing to dry-run: no launchable footprint coverage means no candidate ceiling, and no
        # refused footprint coverage means nothing could ever fire. Both print n/a, never 0/0
        # arithmetic that would read as a measured inertness.
        dry = "no-data"
    elif fires_nogo == 0:
        # The whole point of the cell: the only ceiling the arming rule allows refuses nothing here.
        dry = "inert-at-minimum-ceiling"
    else:
        dry = "firing-at-minimum-ceiling"
    return dict(
        dry_state=dry,
        dry_ceiling=ceiling,
        dry_fires_go=fires_go,
        dry_fires_nogo=fires_nogo,
        sep_state=sep,
        n_carried=len(carried),
        n_nan=sum(1 for r in carried if r["vmswap"] is None),
        n_parseable=len(have),
        n_go_launchable=len(launchable),
        n_nogo=len(nogo),
        go_nonzero=len(go_nonzero),
        go_zero=len(go_zero),
        go_nz_max=(max(go_nonzero) if go_nonzero else None),
        nogo_nonzero=len(nogo_nonzero),
        nogo_zero=len(nogo_zero),
        go_median=median(go_vals),
        go_max=max(go_vals, default=None),
        go_min=min(go_vals, default=None),
        nogo_median=median(nogo_vals),
        nogo_min=min(nogo_vals, default=None),
        nogo_max=max(nogo_vals, default=None),
        n_share=len(shares),
        share_median=median(shares),
        share_max=max(shares, default=None),
    )


def xrate(v, nd=2):
    """Multiple-of-ceiling cell text with the same n/a rule as `mib`/`rate`."""
    return "n/a" if v is None else ("%%.%df" % nd) % v


def day_band(day_rows, swap_max):
    """Day-scoped rule-band arithmetic (census v5, 2026-11-15, tick 192).

    Why this joins the tool instead of living in a tick note: the day's refusal band, median and
    GO/refusal dead zone were quoted in prose from a cut taken several readings earlier. Measured
    live at the 2026-11-15 23:08 reading with a scratch parser over the same files: the swap-rule
    refusal median is 4.225x at the 24-reading cut, 3.985x at 30 and 3.745x at 31, while two
    consecutive ticks repeated "4.22x" as today's number. The arithmetic is trivial; what was
    missing is that nobody re-ran it. These cells now come out of the SAME per-file gate call as
    the verdict column, so a stale median becomes impossible rather than merely discouraged —
    the same class tick 155 (a ceiling attributed to the wrong scope) and tick 166 (a drift
    report printing a silent subset of its own evidence) close mechanically.

    Ratio = the reading's own sampled swap window (`swap_in + swap_out`) divided by the gate's
    `SWAP_RATE_MAX_MIB_S`, i.e. the number the swap-mean rule actually compares. Refusals whose
    swap window sits BELOW that ceiling are counted separately, because they were decided by the
    device or the GPU-mean rule and must never enter the swap-rule band (measured live 19:24 on
    2026-11-15: 0.00x swap traffic, 179.3 MiB/s of whole-disk reads, GPU mean 99.7 %).
    """
    judged = [r for r in day_rows if r["rc"] in (0, 3)]
    ratios = [(r, (r["mean"] / swap_max) if r["mean"] is not None else None) for r in judged]
    go = [v for r, v in ratios if r["rc"] == 0 and v is not None]
    swap_ref = [v for r, v in ratios if r["rc"] == 3 and v is not None and v >= 1.0]
    other_ref = [(r["name"], v) for r, v in ratios
                 if r["rc"] == 3 and v is not None and v < 1.0]
    # --- the RULE's own decision boundary (census v8, 2026-11-16, tick 196) ------------------
    # The `go`/`swap_ref` pair above bounds an interval on the gate VERDICT (the GO column) and
    # then gets quoted as a property of the SWAP RULE. Measured on the real corpus at the
    # committed 2026-11-16 02:14 cut: the corpus row set puts the highest gate-GO swap draw at
    # 0.905 x, while the swap rule itself accepted a draw at 0.940 x
    # (`preflight-20261116-0214.txt`: swap 0.0 in + 18.8 out = 0.94 x of the 20.0 ceiling, refused
    # instead by the device, state-D and GPU-mean rules). So the rule HAS been measured accepting
    # at 0.94 x: its unresolved band is 0.940-1.060 x, not 0.905-1.060 x, and the v7 table's
    # "POPULATED (1 windows inside)" at all three scopes was produced by that very reading — a
    # draw the rule ACCEPTED counted as evidence that the rule's band is unmeasured. A claim about
    # a rule takes the rule's own decisions as its denominator; this is tick 155's class (a cell
    # whose denominator does not match the claim it reports) in the same column as ticks
    # 192/193/195. Both quantities are now printed, each labelled with its denominator.
    accept = [v for r, v in ratios if v is not None and v < 1.0]
    a_max = (max(accept) if accept else None)
    r_min = (min(swap_ref) if swap_ref else None)
    inside_rule = sum(1 for r, v in ratios if v is not None
                      and a_max is not None and r_min is not None and a_max < v < r_min)
    # Readings the gate refused to JUDGE (input gap) can still carry a draw inside the band; they
    # are evidence of traffic, never of a rule decision, so they are named separately.
    gap_inside = sorted((r["name"], r["mean"] / swap_max) for r in day_rows
                        if r["rc"] == 1 and r["mean"] is not None
                        and a_max is not None and r_min is not None
                        and a_max < r["mean"] / swap_max < r_min)
    lo, hi = (max(go) if go else None), (min(swap_ref) if swap_ref else None)
    inside = sum(1 for r, v in ratios if v is not None and lo is not None and hi is not None
                 and lo < v < hi)
    # streaks over the day in reading order
    best_nogo = cur = 0
    for r in day_rows:
        cur = cur + 1 if r["rc"] == 3 else 0
        best_nogo = max(best_nogo, cur)
    best_notgo = cur = 0
    for r in day_rows:
        cur = cur + 1 if r["rc"] != 0 else 0
        best_notgo = max(best_notgo, cur)
    last_go = None
    for r in day_rows:
        if r["rc"] == 0:
            last_go = r
    since_go = None
    if last_go is not None:
        since_go = sum(1 for r in day_rows if r["ts"] > last_go["ts"])
    fp_go = [(r["vmswap"], r) for r in day_rows if r["rc"] == 0 and r["vmswap"] is not None]
    fp_max, fp_at = (max((v for v, _ in fp_go), default=None), None)
    if fp_go and fp_max is not None:
        fp_at = max((r for v, r in fp_go if v == fp_max), key=lambda r: r["ts"])
    trail = 0
    for r in reversed(day_rows):
        if r["vmswap"] is not None and fp_max is not None and r["vmswap"] > fp_max:
            trail += 1
        else:
            break
    return dict(
        n_day=len(day_rows),
        n_window=sum(1 for r, v in ratios if v is not None),
        n_go=len(go), go_min=(min(go) if go else None), go_max=lo,
        n_swap_ref=len(swap_ref), ref_min=hi,
        ref_max=(max(swap_ref) if swap_ref else None),
        ref_median=median(swap_ref),
        n_other_ref=len(other_ref), other_ref=other_ref,
        inside=inside,
        n_accept=len(accept), accept_min=(min(accept) if accept else None), accept_max=a_max,
        n_refuse=len(swap_ref), refuse_min=r_min, inside_rule=inside_rule,
        gap_inside=gap_inside,
        rule_state=(("NO BOUNDARY (no accepted swap draw or no swap-rule refusal with a parseable "
                     "swap window at this scope)" if (a_max is None or r_min is None)
                     else "EMPTY BY CONSTRUCTION (%d judged draws inside)" % inside_rule)),
        zone_state=(("NO-DATA (one group holds no parseable swap window)"
                     if (lo is None or hi is None) else
                     ("POPULATED (%d windows inside)" % inside if inside else
                      "EMPTY (%d windows inside)" % inside))),
        best_nogo=best_nogo, best_notgo=best_notgo,
        since_go=since_go,
        last_go=(last_go["ts"] if last_go else None),
        fp_go_max=fp_max,
        fp_go_at=(fp_at["ts"] if fp_at else None),
        fp_go_ago=(sum(1 for r in day_rows if r["ts"] > fp_at["ts"]) if fp_at else None),
        fp_trail_above=trail,
    )


def window_streak(win_rows, day_rows, as_of):
    """Window-scoped verdict continuity (census v6, 2026-11-16, tick 193).

    Why this joins the tool next to the day band: the day table is scoped to the calendar day and
    resets at midnight, which is correct as labelled and misleading as a streak. Measured live at
    the first reading of 2026-11-16 (`preflight-20261116-0004.txt`, gate NO-GO): the day cells
    printed a longest NO-GO run of 1 reading and `n/a — no GO of this day`, while the box had
    refused FOUR readings in a row across midnight (15 Nov 21:57, 22:32, 23:08 and 16 Nov 00:04)
    and its last GO was 162 minutes earlier at 21:22 — the same launchable set the table itself
    counts as 7 GO in the last 24 h. A tick reading only the day cells would have reported a fresh
    day with one refusal. This is tick 192's class again (a figure that lives only in prose stops
    being recomputed), so the streak is computed here from the same per-file gate returncodes as
    the verdict column, and the divergence between the two scopes gets a state word.
    """
    ordered = sorted(win_rows, key=lambda r: r["ts"])
    day_ordered = sorted(day_rows, key=lambda r: r["ts"])

    def trail(rows, pred):
        n = 0
        for r in reversed(rows):
            if pred(r):
                n += 1
            else:
                break
        return n

    w_nogo = trail(ordered, lambda r: r["rc"] == 3)
    w_notgo = trail(ordered, lambda r: r["rc"] != 0)
    d_nogo = trail(day_ordered, lambda r: r["rc"] == 3)
    last_go = None
    for r in ordered:
        if r["rc"] == 0:
            last_go = r
    since_go = None if last_go is None else sum(1 for r in ordered if r["ts"] > last_go["ts"])
    age_min = None if last_go is None else int(round((as_of - last_go["ts"]).total_seconds() / 60.0))
    newest = ordered[-1] if ordered else None
    if newest is None:
        state = "NO READINGS inside the window — nothing to carry across a day boundary"
    elif w_nogo == 0:
        state = ("NO TRAILING REFUSAL RUN (the newest reading is %s; any-verdict non-GO run %d "
                 "reading(s))" % ("a gate GO" if newest["rc"] == 0 else "an input gap", w_notgo))
    elif w_nogo == d_nogo:
        state = "MATCHED (the current refusal run starts inside the as-of day)"
    else:
        state = ("MIDNIGHT RESET — the current refusal run starts on an earlier day: window %d "
                 "reading(s) vs day %d" % (w_nogo, d_nogo))
    return dict(w_nogo=w_nogo, w_notgo=w_notgo, d_nogo=d_nogo,
                since_go=since_go, last_go=(last_go["ts"] if last_go else None),
                last_go_name=(last_go["name"] if last_go else None), age_min=age_min,
                state=state, n_win=len(ordered))


def window_streak_text(w, window_hours):
    """Window-scoped continuity rows, every cell computed from the same gate verdicts.

    The scope word in each label is the sliding `--window-hours` span the launchable-count row
    already uses, so a reader cannot mistake these for corpus-wide figures: a trailing run is the
    same walk either way, but `readings since the last GO` is only meaningful against a named span.
    """
    return [
        "| trailing consecutive NO-GO run ending at the newest reading (last %d h, crosses the "
        "day boundary) | %d readings (any-verdict non-GO run: %d) |" % (
            window_hours, w["w_nogo"], w["w_notgo"]),
        "| readings since the last gate-GO (last %d h, any day) | %s%s |" % (
            window_hours,
            ("n/a — no GO inside the %d h window" % window_hours if w["since_go"] is None
             else w["since_go"]),
            ("" if w["last_go"] is None else
             " (last GO %s at %s, %d min before as-of)"
             % (w["last_go_name"], w["last_go"].strftime("%Y-%m-%d %H:%M"), w["age_min"]))),
        "| window run vs day run (computed, never asserted) | %s |" % w["state"],
    ]


def day_band_text(d, swap_max):
    """The day-band table, every cell computed from the same gate verdicts the census prints."""
    return [
        "| day launchable (GO) swap draws | %d (band %s-%s x the %s mean ceiling) |" % (
            d["n_go"], xrate(d["go_min"]), xrate(d["go_max"]), swap_max),
        "| day refusals at or above the swap-mean ceiling | %d (band %s-%s x, **median %s x "
        "recomputed at this cut**) |" % (d["n_swap_ref"], xrate(d["ref_min"]), xrate(d["ref_max"]),
                                         xrate(d["ref_median"], 3)),
        "| day refusals decided by a rule OTHER than swap (window below ceiling) | %d%s |" % (
            d["n_other_ref"],
            (": " + ", ".join("%s at %s x" % (n, xrate(v)) for n, v in d["other_ref"])
             if d["other_ref"] else " (none)")),
        "| day swap-rule ACCEPTED draws (any verdict — the rule's own denominator) | %d (band "
        "%s-%s x) |" % (d["n_accept"], xrate(d["accept_min"]), xrate(d["accept_max"])),
        rule_boundary_row(d, swap_max,
                          "day swap-rule decision boundary (accepted max to refusal min)"),
        "| day launchable-column gap (GO max to lowest refusal; VERDICT-scoped, not the rule "
        "boundary) | %s-%s x — %s |" % (
            xrate(d["go_max"]), xrate(d["ref_min"]), d["zone_state"]),
        "| longest consecutive NO-GO run inside the day | %d readings (any-verdict non-GO run: "
        "%d) |" % (d["best_nogo"], d["best_notgo"]),
        "| readings since the day's last gate-GO | %s%s |" % (
            ("n/a — no GO of this day" if d["since_go"] is None else d["since_go"]),
            ("" if d["last_go"] is None else " (last GO %s)" % d["last_go"].strftime("%H:%M"))),
        "| launchable footprint maximum of the day and its age | %s MiB set at %s, %s reading(s) "
        "ago |" % (mib(d["fp_go_max"]),
                   ("n/a" if d["fp_go_at"] is None else d["fp_go_at"].strftime("%H:%M")),
                   ("n/a" if d["fp_go_ago"] is None else d["fp_go_ago"])),
        "| trailing consecutive day windows with footprint above that maximum | %d |"
        % d["fp_trail_above"],
    ]


def _rule_derived_cell(p, rid):
    """One published cell: this rule's derived firing set vs the gate's reason set, this scope.

    The not-evaluable count sits INSIDE the cell rather than in a footnote: an AGREES over a
    denominator the reader cannot see is the same defect as an unstated band denominator (tick
    198's two-denominators rule), and a rule whose key never shipped (the GPU window, the
    `health_loaded` flag) legitimately has a large not-evaluable group in the old corpus.
    """
    dv, rs, bl = p["derived"][rid], p["reason_sets"][rid], p["blind"][rid]
    base = "; %d of %d attributed refusals cannot be evaluated from the columns" % (
        len(bl), p["n_cap"])
    if dv == rs:
        return "AGREES (%d = %d%s)" % (len(dv), len(rs), base)
    return ("DISAGREES (derived %d, reason %d; derived-only %s; reason-only %s%s)"
            % (len(dv), len(rs), diff_names(dv - rs), diff_names(rs - dv), base))


def rule_attribution_text(scopes, swap_max, consts):
    """WHICH gate rule refused, counted per scope (census v9, tick 197).

    `scopes` is a list of (label, rows) — the as-of day, the sliding window, the whole corpus. The
    attribution reads the gate's OWN refusal text, never a restatement: the same subprocess run that
    produces the verdict column produces the reason lines. Two fail-closed cells (unattributable
    reason, unparsable verdict line) and one cross-check are part of the block, because the point of
    counting rules is that a rule can start or stop firing without anyone noticing.

    Census v10 (tick 201) adds the SECOND independent derivation: the engine-state-D set computed
    from each reading's own `engine_state` key (substring test, the gate's parse) against the set
    whose refusal line names the state rule, plus the device-quiet complement of the state-D
    refusals — how many of them sat on a device the device rule calls quiet, which is the number
    that separates "uninterruptible because the NVMe is saturated" from "uninterruptible on a page
    wait served from RAM". The denominator of that row is printed with it: a state-D refusal taken
    before the device key existed cannot be classified at all.
    Returns (lines, findings); a non-empty findings list moves the census exit code to 4.
    """
    L = []
    findings = []
    per = []
    for label, rows in scopes:
        refusals = [r for r in rows if r["rc"] == 3]
        captured = [r for r in refusals if r["decision"] == "NO-GO"]
        counts, multi, sole = {}, 0, 0
        unattr = []
        for r in captured:
            ids = sorted({rid for rid in r["rules"] if rid})
            if any(rid is None for rid in r["rules"]):
                unattr.append(r["name"])
            if len(ids) > 1:
                multi += 1
            elif len(ids) == 1:
                sole += 1
            for rid in ids:
                c = counts.setdefault(rid, [0, 0])
                c[0] += 1
                if len(ids) == 1:
                    c[1] += 1
        unparsed = [r["name"] for r in rows if r["decision"] == "UNPARSED"]
        ratio_set = {r["name"] for r in refusals
                     if r["mean"] is not None and r["mean"] >= swap_max}
        reason_set = {r["name"] for r in captured if "swap-rate" in r["rules"]}
        # v10: the state rule derived from the reading, and the same rule as the gate reports it
        state_set = {r["name"] for r in refusals if r["state"] and "D" in r["state"]}
        state_reason = {r["name"] for r in captured if "engine-state-D" in r["rules"]}
        state_missing = sum(1 for r in rows if r["state"] is None)
        d_named = [r for r in captured if "engine-state-D" in r["rules"]]
        d_with_blk = [r for r in d_named if r["blk"] is not None]
        d_quiet = sum(1 for r in d_with_blk
                      if r["blk"] < (consts["BLK_READ_MAX_MIB_S_WHOLE"]
                                     if r["scope"] == "whole-disk"
                                     else consts["BLK_READ_MAX_MIB_S"]))
        # Census v11: the same comparison for the nine rules that had no derivation. Over the
        # refusals this scope can attribute, the firing set computed from the reading's columns must
        # equal the set the gate's reason line names, rule by rule; a refusal whose columns cannot
        # evaluate a rule is counted separately, never silently dropped from one side of the set.
        d_sets = {rid: set() for rid in DERIVED_RULES}
        b_sets = {rid: set() for rid in DERIVED_RULES}
        r_sets = {rid: set() for rid in DERIVED_RULES}
        for r in captured:
            fired, blind = derived_rule_set(r["rf"], r["scope"], consts)
            named = set(r["rules"])
            for rid in DERIVED_RULES:
                if rid in fired:
                    d_sets[rid].add(r["name"])
                if rid in blind:
                    b_sets[rid].add(r["name"])
                if rid in named:
                    r_sets[rid].add(r["name"])
        per.append(dict(label=label, n_ref=len(refusals), n_cap=len(captured), counts=counts,
                        multi=multi, sole=sole, unattr=unattr, unparsed=unparsed,
                        ratio=len(ratio_set), reason=len(reason_set),
                        only_ratio=sorted(ratio_set - reason_set),
                        only_reason=sorted(reason_set - ratio_set),
                        n_rows=len(rows), state_missing=state_missing,
                        s_derived=len(state_set), s_reason=len(state_reason),
                        only_state=sorted(state_set - state_reason),
                        only_state_reason=sorted(state_reason - state_set),
                        d_named=len(d_named), d_blk=len(d_with_blk), d_quiet=d_quiet,
                        derived=d_sets, blind=b_sets, reason_sets=r_sets))

    def cell(fn):
        return " / ".join("%s: %s" % (p["label"], fn(p)) for p in per)

    L.append("| refusal-rule cell (every scope labelled) | value |")
    L.append("|---|---|")
    L.append("| refusals this scope can attribute (gate NO-GO with captured reason lines) | %s |"
             % cell(lambda p: "%d of %d refusals" % (p["n_cap"], p["n_ref"])))
    for rid, _kind, anchor, _sites in REFUSAL_RULES:
        L.append("| rule fired: %s | %s |" % (
            rule_label(rid),
            cell(lambda p, rid=rid: ("%d fired, %d sole"
                                     % tuple(p["counts"].get(rid, [0, 0]))
                                     if rid in p["counts"] else "0 fired"))))
    L.append("| refusals decided by exactly ONE rule | %s |" % cell(lambda p: "%d" % p["sole"]))
    L.append("| refusals where TWO OR MORE rules fired together | %s |" % cell(lambda p: "%d" % p["multi"]))
    L.append("| refusal reasons this rule table cannot attribute (fail closed) | %s |"
             % cell(lambda p: ("0" if not p["unattr"] else ", ".join(p["unattr"]))))
    L.append("| readings whose gate verdict line could not be parsed (fail closed) | %s |"
             % cell(lambda p: ("0" if not p["unparsed"] else ", ".join(p["unparsed"]))))
    L.append("| rule cross-check: swap-band refusals (key=value ratio at/above the ceiling) vs the "
             "gate's OWN swap-rule reason | %s |"
             % cell(lambda p: ("AGREES (%d = %d)" % (p["ratio"], p["reason"])
                               if not p["only_ratio"] and not p["only_reason"]
                               else "DISAGREES (ratio-set %d, reason-set %d; ratio-only %s; "
                                    "reason-only %s)" % (p["ratio"], p["reason"],
                                                         ", ".join(p["only_ratio"]) or "none",
                                                         ", ".join(p["only_reason"]) or "none"))))
    L.append("| state-rule cross-check: the reading's own `engine_state` contains `D` (the gate's "
             "substring test, so `Dl` fires) vs the gate's engine-state-D reason | %s |"
             % cell(lambda p: ("AGREES (%d = %d)" % (p["s_derived"], p["s_reason"])
                               if not p["only_state"] and not p["only_state_reason"]
                               else "DISAGREES (derived-set %d, reason-set %d; derived-only %s; "
                                    "reason-only %s)" % (p["s_derived"], p["s_reason"],
                                                         ", ".join(p["only_state"]) or "none",
                                                         ", ".join(p["only_state_reason"]) or "none"))))
    L.append("| readings with no `engine_state` key (this cross-check cannot see them; the gate "
             "judges such a reading an input gap, never healthy) | %s |"
             % cell(lambda p: "%d of %d readings" % (p["state_missing"], p["n_rows"])))
    L.append("| state-D refusals on a device the device rule calls quiet (device window present and "
             "below its ceiling, %s whole-disk / %s unscoped; denominator named) | %s |"
             % (consts["BLK_READ_MAX_MIB_S_WHOLE"], consts["BLK_READ_MAX_MIB_S"],
                cell(lambda p: ("%d of %d state-D refusals carry a device window (%d named by the "
                                "gate)" % (p["d_quiet"], p["d_blk"], p["d_named"])
                                if p["d_blk"] else
                                "no denominator — none of the %d state-D refusals carries a device "
                                "window" % p["d_named"]))))
    # Census v11: one cross-check row per remaining rule. The label carries the rule's own anchor so
    # the row says WHICH gate rule it audits, and the cell names how many refusals the rule cannot be
    # evaluated on, because an AGREES cell over a shrunken denominator is not an agreement.
    for rid in DERIVED_RULES:
        L.append("| rule re-derived from the reading's own columns and compared with the gate's "
                 "reason line: %s | %s |" % (
                     rule_label(rid),
                     cell(lambda p, rid=rid: _rule_derived_cell(p, rid))))
    L.append("| gate rules whose firing set is computed from the stored columns at this cut | %s |"
             % cell(lambda p: "%d of %d (v9 swap band, v10 engine state, v11 the other %d)"
                    % (len(DERIVED_RULES) + len(ALREADY_DERIVED_RULES), len(REFUSAL_RULES),
                       len(DERIVED_RULES))))
    gap_by = []
    for label, rows in scopes:
        c = {}
        for r in rows:
            if r["decision"] == "GAP":
                c[r["gap"]] = c.get(r["gap"], 0) + 1
        gap_by.append((label, c))
    L.append("| input-gap reason classes (the gate's own leading phrase, numbers as N) | %s |"
             % " / ".join("%s: %s" % (lbl, ("; ".join("%s x%d" % (k, v) for k, v in sorted(c.items()))
                                                if c else "0")) for lbl, c in gap_by))
    for p in per:
        if p["unattr"]:
            findings.append("%s: unattributed refusal reason in %s" % (p["label"], ", ".join(p["unattr"])))
        if p["unparsed"]:
            findings.append("%s: gate verdict line unparsable in %s" % (p["label"], ", ".join(p["unparsed"])))
        if p["only_ratio"] or p["only_reason"]:
            findings.append("%s: swap-band/refusal-reason sets disagree (ratio-only %s, reason-only %s)"
                            % (p["label"], ", ".join(p["only_ratio"]) or "none",
                               ", ".join(p["only_reason"]) or "none"))
        if p["only_state"] or p["only_state_reason"]:
            findings.append("%s: engine-state-D derived/refusal-reason sets disagree "
                            "(derived-only %s, reason-only %s)"
                            % (p["label"], ", ".join(p["only_state"]) or "none",
                               ", ".join(p["only_state_reason"]) or "none"))
        for rid in DERIVED_RULES:
            dv, rs = p["derived"][rid], p["reason_sets"][rid]
            if dv != rs:
                findings.append("%s: `%s` derived/refusal-reason sets disagree "
                                "(derived-only %s, reason-only %s)"
                                % (p["label"], rid, ", ".join(sorted(dv - rs)) or "none",
                                   ", ".join(sorted(rs - dv)) or "none"))
    return L, sorted(set(findings))


# How many engine generations a scope can list before the cell says how many it withheld. One day
# is normally one or two generations; the corpus spans however many restarts happened, and a cell
# that truncated silently would hide exactly the restart this block exists to make visible.
GENERATION_PRINT_MAX = 8


BUILD_PRINT_MAX = 8
BODY_SHA_RE = re.compile(r"[0-9a-f]{16}")


def identity_of(vals):
    """The reading's engine-BUILD identity, classed the way the GATE rules class it (census v15).

    (sha, ctx, class) where class is:
      "pair"      both keys present and valid (16 lowercase hex; positive integer)
      "onesided"  exactly one key — the two come from ONE /health body, the gate answers input gap
      "malformed" both present but a value fails the format (hash not 16-hex, ctx not > 0)
      "none"      neither key — the pre-v15 corpus: verdict stands, build unnamed

    The census never re-derives the gate's verdict here (it runs the gate); this classes only which
    readings may be credited to a NAMED build and which must not, so a malformed value can never
    lend its hash to a build row.
    """
    s = vals.get("health_body_sha16")
    c = vals.get("health_max_context")
    if s is None and c is None:
        return None, None, "none"
    if s is None or c is None:
        return None, None, "onesided"
    try:
        civ = int(c)
    except ValueError:
        civ = None
    if BODY_SHA_RE.fullmatch(s) and civ is not None and civ > 0:
        return s, civ, "pair"
    return None, None, "malformed"


def engine_build_text(scopes):
    """Which engine BUILD each reading was recorded against (census v15, 2026-11-16, tick 208).

    The pid comment names a PROCESS, and a pid answers only "did this process swap?". The /health
    body hash names the BUILD, and that answers "was this build ever refused?" — measured 2026-11-16,
    the two axes disagreed over one day: every refusal belonged to a retired pid while the live pid
    recorded only GOs, and the 09:59 restart that split the day was simultaneously a build swap no
    stored byte could see. The block prints the COVERAGE split first (a pair / one-sided / malformed /
    unrecorded — the first cut has no pair anywhere and must say so rather than print silence), then
    the per-build detail, then the crosswalk between the newest reading's build and its pid, then the
    two anomaly counts (one pid naming two builds = a build changed under a live process, impossible
    on a restart-based engine and named the day it is seen; one build under two pids = the same build
    restarted, normal and worth naming). No gate rule reads these keys, so no verdict here can move.
    """
    L = []
    per = []
    for label, rows in scopes:
        builds = {}
        cnt = dict(pair=0, onesided=0, malformed=0, none=0)
        newest = None
        for r in rows:
            cnt[r["id_class"]] += 1
            if r["id_class"] == "pair":
                b = builds.setdefault(r["id_sha"], dict(ctx=r["id_ctx"], n=0, go=0, nogo=0,
                                                        gap=0, first=r["ts"], last=r["ts"],
                                                        first_name=r["name"], last_name=r["name"],
                                                        pids=set()))
                b["n"] += 1
                if r["rc"] == 0:
                    b["go"] += 1
                elif r["rc"] == 3:
                    b["nogo"] += 1
                else:
                    b["gap"] += 1
                if r["pid"]:
                    b["pids"].add(r["pid"])
                if r["ts"] < b["first"]:
                    b["first"], b["first_name"] = r["ts"], r["name"]
                if r["ts"] > b["last"]:
                    b["last"], b["last_name"] = r["ts"], r["name"]
            if newest is None or r["ts"] > newest["ts"]:
                newest = r
        per.append(dict(label=label, builds=builds, cnt=cnt, n=len(rows), newest=newest,
                        rows=rows))

    def cell(fn):
        return " / ".join("%s: %s" % (p["label"], fn(p)) for p in per)

    L.append("| readings carrying a VALID build-identity pair (`health_body_sha16` + "
             "`health_max_context`, both keys from ONE /health body; census v15) | %s |"
             % cell(lambda p: "%d of %d readings" % (p["cnt"]["pair"], p["n"])))
    L.append("| readings carrying a BROKEN identity (exactly one key, or a value failing the "
             "format — the gate answers an input gap on every one of these, so they credit no "
             "build and lose no verdict) | %s |"
             % cell(lambda p: "%d one-sided / %d malformed"
                    % (p["cnt"]["onesided"], p["cnt"]["malformed"])))
    L.append("| readings carrying NO identity key (the pre-v15 corpus: the verdict stands, the "
             "BUILD is unnamed — every statistic pooled over them pools processes, not builds) | %s |"
             % cell(lambda p: "%d of %d readings" % (p["cnt"]["none"], p["n"])))

    def build_txt(p):
        items = sorted(p["builds"].items(), key=lambda kv: kv[1]["first"])
        if not items:
            return ("no denominator: this scope has 0 valid identity pairs over %d readings, so no "
                    "verdict in it can be credited or blamed to a named BUILD (the pid rows above "
                    "are the only generation axis this scope has)" % p["n"])
        parts = []
        for sha, b in items[:BUILD_PRINT_MAX]:
            parts.append("`%s` (ctx %d) — %d reading(s) (%d GO / %d NO-GO / %d input gap), first %s "
                         "last %s, engine pids: %s"
                         % (sha, b["ctx"], b["n"], b["go"], b["nogo"], b["gap"],
                            b["first_name"], b["last_name"],
                            ", ".join(sorted(b["pids"])) or "no pid comment"))
        withheld = len(items) - len(parts)
        txt = "%d distinct build(s) over %d identity-bearing reading(s)" % (
            len(items), p["cnt"]["pair"])
        if withheld > 0:
            txt += " (%d listed, %d not printed)" % (len(parts), withheld)
        return txt + ": " + "; ".join(parts)
    L.append("| distinct engine BUILDs recorded in this scope (body sha16 -> advertised context, "
             "verdict mix, span, pid set; at most %d listed, count precedes the list) | %s |"
             % (BUILD_PRINT_MAX, cell(build_txt)))

    def cross(p):
        nw = p["newest"]
        if nw is None:
            return "no denominator — empty scope"
        if nw["id_class"] == "pair":
            span = [r for r in p["rows"] if r["pid"] and r["pid"] == nw["pid"]]
            rec = [r for r in span if r["id_class"] == "pair"]
            same = [r for r in rec if r["id_sha"] == nw["id_sha"]]
            if not span:
                word = ("the newest reading names a build but its pid is unknown, so the crosswalk "
                        "cannot run")
            elif len(rec) < len(span):
                word = ("COVERAGE BOUNDARY INSIDE ONE PID: pid %s has %d reading(s) here without an "
                        "identity key — the coverage boundary is the KEY shipping, not the process, "
                        "and the pid rows must not be read as build rows"
                        % (nw["pid"], len(span) - len(rec)))
            elif len(same) < len(rec):
                others = sorted({r["id_sha"] for r in rec} - {nw["id_sha"]})
                word = ("PID SPANS %d BUILD(S): pid %s also appears under %s — a build changed "
                        "under a live pid, impossible on a restart-based engine: name it, do not "
                        "average it" % (len({r["id_sha"] for r in rec}),
                                        nw["pid"], ", ".join(others)))
            else:
                word = ("MATCHED: every identity-bearing reading of pid %s names this one build, so "
                        "this pid's GOs and refusals may be quoted as this build's record"
                        % nw["pid"])
            return ("newest reading `%s` (pid %s) -> build `%s` ctx %d; that pid carries a valid "
                    "pair in %d of its %d reading(s) in scope -> %s"
                    % (nw["name"], nw["pid"] or "unknown", nw["id_sha"], nw["id_ctx"],
                       len(rec), len(span), word))
        pid = nw["pid"]
        span = [r for r in p["rows"] if r["pid"] and r["pid"] == pid] if pid else []
        nrec = sum(1 for r in span if r["id_class"] == "pair")
        return ("newest reading `%s` carries NO build identity (pid %s; %d of its %d reading(s) "
                "here do) -> BUILD-UNRECORDED: this scope cannot name the build the newest verdict "
                "was recorded against, only the process"
                % (nw["name"], pid or "unknown", nrec, len(span)))
    L.append("| the newest reading's BUILD vs its engine pid (the two axes crosswalked; a pid whose "
             "readings split recorded/unrecorded means the KEY arrived mid-process, not the build) "
             "| %s |" % cell(cross))

    def anom(p):
        pid2b = {}
        for r in p["rows"]:
            if r["id_class"] == "pair" and r["pid"]:
                pid2b.setdefault(r["pid"], set()).add(r["id_sha"])
        multi_b = {pid: s for pid, s in pid2b.items() if len(s) > 1}
        multi_p = {sha: sorted(b["pids"]) for sha, b in p["builds"].items() if len(b["pids"]) > 1}
        a = ("none" if not multi_b else
             "; ".join("pid %s -> %s" % (pid, ", ".join(sorted(s)))
                       for pid, s in sorted(multi_b.items())))
        q = ("none" if not multi_p else
             "; ".join("`%s` on pids %s" % (sha, ", ".join(ps))
                       for sha, ps in sorted(multi_p.items())))
        return "one pid naming more than one build: %s / one build under more than one pid " \
               "(restart of the SAME build, normal): %s" % (a, q)
    L.append("| pid<->build anomalies (a pid spanning builds = a live change of build, never "
             "happens on this engine and gets NAMED the day it does; a build under several pids = "
             "the same build restarted, ordinary) | %s |" % cell(anom))
    return L


def engine_generation_text(scopes):
    """Which ENGINE GENERATION each pooled statistic in this table actually belongs to.

    The producer writes the pid it sampled into a comment line, and the gate's parser skips comments,
    so no published statistic had ever seen it. That matters the moment the endpoint's engine is
    restarted (a version bump, a config ladder, a watchdog restart): every footprint, RSS and
    page-cache figure in this table is then pooled over processes with different configs, and the
    pre-registered footprint ceiling would be drawn from a process this cut no longer samples. The
    block prints generation counts first and the per-generation detail up to GENERATION_PRINT_MAX,
    and says so when a scope has no pid comment at all rather than printing 0.
    """
    L = []
    per = []
    for label, rows in scopes:
        gens = {}
        nopid = 0
        for r in rows:
            if r["pid"] is None:
                nopid += 1
                continue
            g = gens.setdefault(r["pid"], dict(n=0, go=0, nogo=0, gap=0,
                                               first=r["ts"], last=r["ts"],
                                               first_name=r["name"], last_name=r["name"],
                                               fp_go=None, fp_go_name=None,
                                               fp_no=None, fp_no_name=None,
                                               fp_key=0, fp_go_n=0, fp_go_nz=0,
                                               fp_no_n=0, fp_no_nz=0))
            g["n"] += 1
            if r["vmswap"] is not None:
                # Census v12: per-generation footprint coverage AND information. A generation that
                # answers 0 MiB in every window carries the key and demonstrates nothing; a generation
                # that never carries the key at all carries neither. The two must not print alike.
                g["fp_key"] += 1
            if r["rc"] == 0:
                g["go"] += 1
                if r["vmswap"] is not None and (g["fp_go"] is None or r["vmswap"] > g["fp_go"]):
                    g["fp_go"], g["fp_go_name"] = r["vmswap"], r["name"]
                if r["vmswap"] is not None:
                    g["fp_go_n"] += 1
                    if r["vmswap"] > 0:
                        g["fp_go_nz"] += 1
            elif r["rc"] == 3:
                g["nogo"] += 1
                if r["vmswap"] is not None and (g["fp_no"] is None or r["vmswap"] > g["fp_no"]):
                    g["fp_no"], g["fp_no_name"] = r["vmswap"], r["name"]
                if r["vmswap"] is not None:
                    g["fp_no_n"] += 1
                    if r["vmswap"] > 0:
                        g["fp_no_nz"] += 1
            else:
                g["gap"] += 1
            if r["ts"] < g["first"]:
                g["first"], g["first_name"] = r["ts"], r["name"]
            if r["ts"] > g["last"]:
                g["last"], g["last_name"] = r["ts"], r["name"]
        go_pids = {r["pid"] for r in rows if r["rc"] == 0 and r["pid"]}
        no_pids = {r["pid"] for r in rows if r["rc"] == 3 and r["pid"]}
        newest = None
        for r in rows:
            if r["pid"] and (newest is None or r["ts"] > newest["ts"]):
                newest = r
        best = None
        for r in rows:
            if r["rc"] == 0 and r["vmswap"] is not None and r["pid"]:
                if best is None or r["vmswap"] > best["vmswap"]:
                    best = r
        per.append(dict(label=label, gens=gens, nopid=nopid, n=len(rows),
                        go_pids=go_pids, no_pids=no_pids, newest=newest, best=best))

    def cell(fn):
        return " / ".join("%s: %s" % (p["label"], fn(p)) for p in per)

    def gen_txt(p):
        items = sorted(p["gens"].items(), key=lambda kv: kv[1]["first"])
        parts = []
        for pid, g in items[:GENERATION_PRINT_MAX]:
            parts.append("pid %s — %d readings (%d GO / %d NO-GO / %d input gap), first %s last %s, "
                         "footprint max launchable %s / refused %s, non-zero footprint draws %d of %d "
                         "launchable / %d of %d refused"
                         % (pid, g["n"], g["go"], g["nogo"], g["gap"], g["first_name"],
                            g["last_name"],
                            ("%d MiB" % g["fp_go"]) if g["fp_go"] is not None else "no key",
                            ("%d MiB" % g["fp_no"]) if g["fp_no"] is not None else "no key",
                            g["fp_go_nz"], g["fp_go_n"], g["fp_no_nz"], g["fp_no_n"]))
        withheld = len(items) - len(parts)
        txt = "%d generations over %d readings" % (len(items), p["n"] - p["nopid"])
        if withheld > 0:
            txt += " (%d listed, %d not printed)" % (len(parts), withheld)
        if parts:
            txt += ": " + "; ".join(parts)
        else:
            txt += " — no denominator, no reading in this scope carries an engine pid"
        return txt

    L.append("| engine generations sampled in this scope (the producer's own `# engine pid=` "
             "comment; the count precedes the list, at most %d generations listed) | %s |"
             % (GENERATION_PRINT_MAX, cell(gen_txt)))
    L.append("| readings in this scope whose producer comment carries no engine pid (unattributable "
             "by this block; the gate never reads comments, so its verdict is unaffected) | %s |"
             % cell(lambda p: "%d of %d readings" % (p["nopid"], p["n"])))

    def overlap(p):
        if not p["go_pids"] or not p["no_pids"]:
            return ("no denominator — this scope has %d launchable-generation(s) and %d "
                    "refused-generation(s)" % (len(p["go_pids"]), len(p["no_pids"])))
        shared = p["go_pids"] & p["no_pids"]
        word = ("SAME GENERATION (the launchable and refused statistics describe one process)"
                if shared == p["go_pids"] == p["no_pids"] else
                ("PARTIALLY OVERLAPPING (%d generation(s) carry both)" % len(shared)
                 if shared else
                 "DISJOINT GENERATIONS — launchable windows sit on %s and refused windows on %s, so "
                 "the footprint band pools two processes with different configs"
                 % (", ".join(sorted(p["go_pids"])), ", ".join(sorted(p["no_pids"])))))
        return word
    L.append("| launchable windows and refused windows on the same engine generation? | %s |"
             % cell(overlap))

    def stale(p):
        if p["best"] is None:
            return "no denominator — no launchable reading in this scope carries a footprint key"
        b = p["best"]
        txt = ("launchable footprint maximum %d MiB (`%s`) belongs to pid %s"
               % (b["vmswap"], b["name"], b["pid"]))
        if p["newest"] is None:
            return txt + "; no newest generation to compare with"
        if b["pid"] == p["newest"]["pid"]:
            return txt + " — CURRENT (the newest reading in this scope sampled the same pid)"
        return (txt + ", while the newest reading in this scope sampled pid %s (`%s`); pid %s was "
                "last sampled by `%s` → GENERATION-STALE: a footprint ceiling drawn from this value "
                "describes a process this cut no longer samples"
                % (p["newest"]["pid"], p["newest"]["name"], b["pid"],
                   p["gens"][b["pid"]]["last_name"]))
    L.append("| the footprint dry-run ceiling's binding value, and the generation that produced it | %s |"
             % cell(stale))

    def neverobs(p):
        """Has this generation ever demonstrated a non-zero footprint (census v12, tick 204)?

        Tick 203's open question, made mechanical. The arming counter is per-window coverage, so a
        generation that answers 0 MiB in every window still feeds it; the question a decision needs is
        not "how many windows carry the key" but "has THIS process ever swapped at all", because a
        ceiling over an all-zero launchable group is `> 0 MiB` and every refusal it makes would be a
        first occurrence of an unexercised failure mode."""
        keyed = {pid: g for pid, g in p["gens"].items() if g["fp_key"]}
        if not keyed:
            return ("no denominator — no generation in this scope carries `engine_vmswap_mib` in any "
                    "window, so none of them has footprint coverage at all")
        obs = sorted(pid for pid, g in keyed.items() if g["fp_go_nz"] + g["fp_no_nz"] > 0)
        zero = sorted(pid for pid, g in keyed.items() if g["fp_go_nz"] + g["fp_no_nz"] == 0)
        txt = ("%d generation(s) carry the footprint key here: %d recorded a footprint above 0 MiB in "
               "at least one window (%s), %d recorded only zeros in every window it produced (%s)"
               % (len(keyed), len(obs), ", ".join(obs) or "none",
                  len(zero), ", ".join(zero) or "none"))
        if p["newest"] is None:
            return txt + "; no newest sampled pid to compare with"
        npid = p["newest"]["pid"]
        g = keyed.get(npid)
        if g is None:
            return (txt + "; the newest sampled pid %s carries no footprint key in this scope → "
                    "NO FOOTPRINT COVERAGE for the live process" % npid)
        nz = g["fp_go_nz"] + g["fp_no_nz"]
        if nz == 0:
            return (txt + "; the NEWEST generation pid %s (`%s`) carries the key in %d window(s) and "
                    "answered exactly 0 MiB in every one → ZERO-FOOTPRINT GENERATION: the only ceiling "
                    "this coverage admits is `> 0 MiB`, so arming on it arms a rule whose failure mode "
                    "this very process has never demonstrated once"
                    % (npid, p["newest"]["name"], g["fp_key"]))
        return (txt + "; the NEWEST generation pid %s records a non-zero footprint in %d of its %d "
                "footprint window(s), so a ceiling drawn from this generation is exercised"
                % (npid, nz, g["fp_key"]))
    L.append("| has the newest sampled engine generation ever recorded a footprint above 0 MiB? | %s |"
             % cell(neverobs))
    return L


# ---------------------------------------------------------------------------
# THE FREE COLUMNS: memory headroom as a state with a trend (census v13)
# ---------------------------------------------------------------------------
# Why this block exists, measured on the live corpus at the 2026-11-16 12:40 cut. The gate has
# always had a memory rule (`mem-available-low`, `MEM_AVAILABLE_MIN_MIB = 2048`) and the producer has
# always printed `mem_available_mib` and `engine_rss_mib`, and yet no published cell ever banded
# either number: 204 ticks wrote headroom into prose ("MemAvailable 20 664 of 61 953") and moved on.
# That prose hid a regime change. Through the whole of 16 Nov up to 07:19 the retired generation
# 175316 sat at MemAvailable 17 675-21 441 MiB with 16 062-16 839 MiB of swap in use; the live
# generation 438502, sampled five times from 10:07 to 12:40, reads MemAvailable 6 618 -> 4 938 MiB
# with swap in use FLAT at 65 MiB. The two free columns moved in OPPOSITE directions across the
# restart: the engine stopped swapping (which is why the morning's page-in storms — 6.82x, 6.91x,
# 10.69x of the swap ceiling — simply stopped) and spent almost 15 GiB of RAM headroom re-holding in
# RAM what it used to hold in swap. The failure mode this box carries has therefore moved from
# "swap throughput" to "distance to the gate's own memory floor", and a table that bands only rates
# cannot see that at all.
#
# What is deliberately NOT done here: no ceiling is registered, no rule is armed, and the projection
# row is labelled a projection in its own cell. The floor this block quotes is the gate's OWN
# constant, read out of the gate source by `gate_constants()`, so the table can disagree with a tick
# note and never with the gate.

MEM_SLOPE_FLAT_MIB_PER_H = 1.0     # below this the trend cell says FLAT instead of projecting
MEM_ATTRIBUTION_MIN = 0.80         # share of a headroom fall an RSS growth must explain to be
                                   # called ATTRIBUTED; below 0.20 it is called UNATTRIBUTED
MEM_PROJECTION_MIN_DRAWS = 3       # a straight line through two points is not a trend
MEM_GEN_PRINT = 3                  # generations printed per scope: the NEWEST ones, because a
                                   # trajectory row exists to say what happens next, and the whole-
                                   # corpus scope would otherwise print 15 of them
MEM_INTERVAL_FLAT_RATIO = 1.5      # widest/narrowest interval inside a monotone run at or below
                                   # which the reading-count projection collapses to ONE number
                                   # (census v14). Above it the cell prints the band the intervals
                                   # actually support, because a reading count derived from a mean
                                   # cadence is only a count when the cadence is the one observed.


def _positive_intervals(rows):
    """Consecutive timestamp gaps in MINUTES, oldest-first, dropping any gap <= 0.

    A census that converts a projected time into "how many more readings until X" is dividing by
    the sampling cadence, so the cadence needs the same treatment as every other rate on this
    line: a measured window, never a nominal one. Rows sharing a timestamp (two producers reading
    the same minute, or a fixture with one name) contribute a zero gap, which must never reach a
    denominator, so they are dropped rather than averaged in. No positive gap at all is reported
    as an empty list and the caller prints no reading count (fail closed).
    """
    out = []
    for prev, cur in zip(rows, rows[1:]):
        gap = (cur["ts"] - prev["ts"]).total_seconds() / 60.0
        if gap > 0:
            out.append(gap)
    return out


def _monotone_tail(rows, key):
    """The trailing strictly-monotone run of one column of a row list, oldest-first.

    Returns (run, direction) where direction is 'down' / 'up' / 'flat' and `run` is a slice of the
    ROWS, not of the numbers: every cell that needs the trend also needs the file names and the
    timestamps behind it (taking the numeric slice and then reaching back for rows is how the first
    draft of this cell crashed on live bytes). A series of one row has no direction, and a mixed
    series still yields its trailing monotone run, because the decision this feeds ("what happens
    next") only follows the run that is currently open.
    """
    if len(rows) < 2:
        return rows, None
    n = len(rows)
    d = None
    run = 1
    for i in range(n - 1, 0, -1):
        step = key(rows[i]) - key(rows[i - 1])
        cur = "down" if step < 0 else ("up" if step > 0 else "flat")
        if d is None:
            d = cur
        elif cur != d:
            break
        run += 1
    return rows[n - run:], d


def memory_headroom_text(scopes, consts):
    """MemAvailable / swap-in-use / engine-RSS as a per-generation state with a computed trend.

    Three claims this block refuses to merge, each because the corpus has already shown the merge
    being wrong: (a) headroom belongs to an ENGINE GENERATION, not to the box (tick 202's lesson,
    applied to a column that block never touched); (b) a headroom fall is either attributed to the
    sampled process's own RSS growth or named unattributed, never assumed; (c) a slope is a
    projection, so the cell that prints it prints the word."""
    floor = consts["MEM_AVAILABLE_MIN_MIB"]
    L = []
    per = []
    for label, rows in scopes:
        have = [r for r in rows if r["avail"] is not None]
        newest = None
        for r in have:
            if newest is None or r["ts"] > newest["ts"]:
                newest = r
        low = None
        for r in have:
            if low is None or r["avail"] < low["avail"]:
                low = r
        gens = {}
        for r in sorted(rows, key=lambda r: r["ts"]):
            if not r["pid"]:
                continue
            g = gens.setdefault(r["pid"], dict(rows=[], first=r["ts"], last=r["ts"]))
            g["rows"].append(r)
            if r["ts"] < g["first"]:
                g["first"] = r["ts"]
            if r["ts"] > g["last"]:
                g["last"] = r["ts"]
        newest_pid = newest["pid"] if newest and newest["pid"] else None
        per.append(dict(label=label, n=len(rows), have=have, newest=newest, low=low,
                        bad=[r for r in rows if r.get("rss_bad")],
                        gens=gens, newest_pid=newest_pid,
                        nopid=sum(1 for r in rows if not r["pid"])))

    def cell(fn):
        return " / ".join("%s: %s" % (p["label"], fn(p)) for p in per)

    def cov(p):
        miss = p["n"] - len(p["have"])
        return ("%d of %d readings carry a parseable `mem_available_mib`%s"
                % (len(p["have"]), p["n"], (", %d do not" % miss) if miss else ""))
    L.append("| memory-headroom coverage in this scope | %s |" % cell(cov))

    def band(p):
        if not p["have"]:
            return "no denominator — no reading in this scope carries `mem_available_mib`"
        vs = sorted(r["avail"] for r in p["have"])
        return ("min %s MiB (`%s`), median %s MiB, max %s MiB over %d reading(s)"
                % (mib(p["low"]["avail"]), p["low"]["name"], mib(median(vs)),
                   mib(vs[-1]), len(vs)))
    L.append("| MemAvailable band in this scope | %s |" % cell(band))

    def against_floor(p):
        if not p["have"]:
            return "no denominator — no `mem_available_mib` in this scope"
        r = p["newest"]
        d = r["avail"] - floor
        base = ("newest draw `%s` reads %s MiB against the gate's own floor "
                "`MEM_AVAILABLE_MIN_MIB` = %s MiB (rule `mem-available-low`) → "
                % (r["name"], mib(r["avail"]), mib(floor)))
        if d < 0:
            if r["rc"] == 0:
                return (base + "BELOW THE FLOOR AND THE GATE LAUNCHED IT — the gate's own memory "
                        "rule did not fire on this reading: a gate/census contradiction, not a "
                        "reporting difference")
            return (base + "BELOW the floor by %s MiB — the memory rule refuses such a window "
                    "(this reading's verdict: %s)" % (mib(-d), RC_WORD.get(r["rc"], r["rc"])))
        return (base + "ABOVE the floor by %s MiB (%.2fx the floor; verdict %s)"
                % (mib(d), r["avail"] / floor, RC_WORD.get(r["rc"], r["rc"])))
    L.append("| the newest reading's headroom against that floor | %s |" % cell(against_floor))

    def closest(p):
        if not p["have"]:
            return "no denominator — no `mem_available_mib` in this scope"
        r = p["low"]
        d = r["avail"] - floor
        later = sum(1 for x in p["have"] if x["ts"] > r["ts"])
        word = ("THE MINIMUM IS THE NEWEST DRAW (headroom is falling, not resting)"
                if later == 0 else
                "the minimum sits %d reading(s) before the newest draw, which reads %s MiB"
                % (later, mib(p["newest"]["avail"])))
        return ("closest approach to the floor in this scope: %s MiB (`%s`), %s MiB above it; %s"
                % (mib(r["avail"]), r["name"], mib(d), word))
    L.append("| closest approach to that floor in this scope | %s |" % cell(closest))

    def traj(p):
        if not p["gens"]:
            return ("no denominator — no reading in this scope carries an engine pid, so no "
                    "headroom trajectory can be attributed to a process")
        items = sorted(p["gens"].items(), key=lambda kv: kv[1]["first"])
        shown = items[-MEM_GEN_PRINT:]
        parts = []
        for pid, g in shown:
            ser = [r for r in g["rows"] if r["avail"] is not None]
            if not ser:
                parts.append("pid %s — %d readings, no `mem_available_mib`" % (pid, len(g["rows"])))
                continue
            run, direction = _monotone_tail(ser, lambda r: r["avail"])
            d = ("monotonically %s over the last %d draw(s)" % (direction, len(run))
                 if direction else "single draw")
            used = [r["used"] for r in g["rows"] if r["used"] is not None]
            rss = [r["rss"] for r in g["rows"] if r["rss"] is not None]
            parts.append("pid %s — %d draw(s), MemAvailable %s → %s MiB (Δ %s %s MiB, %s), "
                         "swap in use %s → %s MiB, engine RSS %s → %s MiB"
                         % (pid, len(ser), mib(ser[0]["avail"]), mib(ser[-1]["avail"]),
                            ("+" if ser[-1]["avail"] >= ser[0]["avail"] else "−"),
                            mib(abs(ser[-1]["avail"] - ser[0]["avail"])), d,
                            (mib(used[0]) if used else "no key"),
                            (mib(used[-1]) if used else "no key"),
                            (mib(rss[0]) if rss else "no key"),
                            (mib(rss[-1]) if rss else "no key")))
        withheld = len(p["gens"]) - len(parts)
        txt = "%d generation(s) with headroom draws: %s" % (len(p["gens"]), "; ".join(parts))
        if withheld > 0:
            txt += " (%d not printed)" % withheld
        return txt
    L.append("| MemAvailable / swap-in-use / engine-RSS trajectory per engine generation "
             "(the free columns belong to a process, not to the box) | %s |" % cell(traj))

    def attrib(p):
        if p["newest_pid"] is None or p["newest_pid"] not in p["gens"]:
            return "no denominator — the newest headroom draw carries no engine pid"
        g = p["gens"][p["newest_pid"]]
        ser = [r for r in g["rows"] if r["avail"] is not None and r["rss"] is not None]
        if len(ser) < 2:
            return ("no denominator — the newest generation pid %s has %d draw(s) carrying BOTH "
                    "`mem_available_mib` and `engine_rss_mib`" % (p["newest_pid"], len(ser)))
        a0, a1 = ser[0]["avail"], ser[-1]["avail"]
        r0, r1 = ser[0]["rss"], ser[-1]["rss"]
        span = (ser[-1]["ts"] - ser[0]["ts"]).total_seconds() / 60.0
        base = ("newest generation pid %s, `%s` → `%s` over %.0f min: MemAvailable %s → %s MiB, "
                "engine RSS %s → %s MiB. "
                % (p["newest_pid"], ser[0]["name"], ser[-1]["name"], span,
                   mib(a0), mib(a1), mib(r0), mib(r1)))
        if a1 >= a0:
            return base + ("headroom did NOT fall in this generation (Δ +%s MiB), no attribution owed"
                           % mib(a1 - a0))
        fall = a0 - a1
        grow = r1 - r0
        if grow <= 0:
            return (base + "UNATTRIBUTED: the engine's own RSS did not grow (Δ %s MiB) while "
                    "headroom fell %s MiB, so the memory went somewhere this producer does not "
                    "sample" % ("−" + mib(-grow), mib(fall)))
        frac = grow / fall
        residual = fall - grow
        word = ("ATTRIBUTED TO THE SAMPLED ENGINE" if frac >= MEM_ATTRIBUTION_MIN
                else ("PARTIALLY ATTRIBUTED" if frac >= 0.20 else "UNATTRIBUTED"))
        return (base + "%s: RSS grew %s MiB against a headroom fall of %s MiB — the sampled engine "
                "accounts for %.0f %s of it, residual %s MiB"
                % (word, mib(grow), mib(fall), 100.0 * frac, "%", mib(abs(residual))))
    L.append("| how much of the newest generation's headroom change its own RSS change explains | %s |"
             % cell(attrib))

    def trend(p):
        if p["newest_pid"] is None or p["newest_pid"] not in p["gens"]:
            return "no denominator — the newest headroom draw carries no engine pid"
        ser = [r for r in p["gens"][p["newest_pid"]]["rows"] if r["avail"] is not None]
        run, direction = _monotone_tail(ser, lambda r: r["avail"])
        if direction != "down":
            return ("newest generation pid %s: %s — no projection is admissible"
                    % (p["newest_pid"],
                       ("only %d headroom draw(s)" % len(ser)) if len(ser) < 2
                       else "NOT DECREASING"))
        if len(run) < MEM_PROJECTION_MIN_DRAWS:
            return ("newest generation pid %s: TOO FEW MONOTONE DRAWS (%d of %d) — a line through "
                    "two points is not a trend, no projection" % (p["newest_pid"], len(run),
                                                                  len(ser)))
        span = (run[-1]["ts"] - run[0]["ts"]).total_seconds() / 60.0
        if span <= 0:
            return "newest generation pid %s: the monotone draws share one timestamp — no rate" % (
                p["newest_pid"],)
        per_h = (run[0]["avail"] - run[-1]["avail"]) * 60.0 / span
        cadence = span / (len(run) - 1)
        base = ("newest generation pid %s: %d consecutive decreasing draws `%s` → `%s` lost %s MiB "
                "over %.0f min = −%.1f MiB/h, mean cadence %.1f min"
                % (p["newest_pid"], len(run), run[0]["name"], run[-1]["name"],
                   mib(run[0]["avail"] - run[-1]["avail"]), span, per_h, cadence))
        if per_h < MEM_SLOPE_FLAT_MIB_PER_H:
            return base + "; FLAT at this resolution — no projection"
        last = run[-1]["avail"]
        if last <= floor:
            return base + "; the newest draw already sits at or below the floor"
        mins = (last - floor) * 60.0 / per_h
        # Census v14 (2026-11-16, tick 206): a projection that converts MINUTES into READINGS
        # through the run's MEAN cadence owes that cadence a denominator. Measured at the
        # 2026-11-16 13:37 cut: the newest generation's monotone fall spans 210 min with
        # intervals 28, 39, 35, 51, 9, 16 and 32 min (a 5.7x spread), and v13 printed
        # "about 9 further readings" from 298.0 min / 30.0 min mean. The same 298 minutes are
        # 33 readings at this run's fastest observed interval and 5 at its slowest, so the
        # single number was not a conservative estimate, it was an unstated assumption —
        # tick 196's missing denominator, now inside a cell that already labels itself a
        # projection. The minutes stay the primary quantity (a rate, divided by a measured
        # window); the reading count becomes a band over the run's OWN intervals, with the
        # interval denominator printed, and collapses to one number only when the intervals
        # are uniform. A run whose draws share timestamps has no measured interval at all and
        # prints no reading count (fail closed, never a division by zero and never a guess).
        gaps = _positive_intervals(run)
        if not gaps:
            return (base + "; PROJECTION (not a promise, one generation, n=%d): at that constant "
                    "slope the gate's own %s MiB floor arrives ≈%.0f min after `%s`; NO reading "
                    "count — the monotone draws share timestamps, so no measured interval exists "
                    "to convert minutes into readings"
                    % (len(run), mib(floor), mins, run[-1]["name"]))
        lo, hi = min(gaps), max(gaps)
        denom = ("%d interval(s), %.0f-%.0f min, mean %.1f" % (len(gaps), lo, hi, cadence))
        if hi <= lo * MEM_INTERVAL_FLAT_RATIO:
            tail = ("in READINGS ≈%d further draws, a single count being admissible at this "
                    "cadence (%s)" % (int(mins // lo), denom))
        else:
            tail = ("in READINGS %d-%d further draws, because the run's own intervals span "
                    "%.0f-%.0f min (%s), a %.1fx spread: v13 divided the minutes by that mean "
                    "alone and printed the single number %d, which this run's interval range "
                    "refutes by %.1fx"
                    % (int(mins // hi), int(mins // lo), lo, hi, denom, hi / lo,
                       int(mins // cadence), hi / lo))
        return (base + "; PROJECTION (not a promise, one generation, n=%d): at that constant slope "
                "the gate's own %s MiB floor arrives ≈%.0f min after `%s`; %s"
                % (len(run), mib(floor), mins, run[-1]["name"], tail))
    L.append("| headroom trend of the newest generation, and what it projects against that floor | %s |"
             % cell(trend))

    def flip(p):
        items = sorted(p["gens"].items(), key=lambda kv: kv[1]["first"])
        pairs = []
        for (pida, ga), (pidb, gb) in zip(items, items[1:]):
            ra = next((r for r in reversed(ga["rows"]) if r["avail"] is not None), None)
            rb = next((r for r in gb["rows"] if r["avail"] is not None), None)
            if ra is None or rb is None:
                continue
            pairs.append((pida, pidb, ra, rb))
        if not pairs:
            return ("no denominator — this scope holds %d generation(s) with headroom draws, so "
                    "there is no restart to compare across" % len(p["gens"]))
        parts = []
        for pida, pidb, ra, rb in pairs[-(MEM_GEN_PRINT - 1):]:
            da = rb["avail"] - ra["avail"]
            # The swap column is read from the SAME two rows the headroom delta comes from: the pair
            # this row describes is one window of the old process and one window of the new one, so
            # borrowing each column from a different row would invent a pairing.
            ua, ub = ra["used"], rb["used"]
            if ua is None or ub is None:
                parts.append("pid %s → %s: ΔMemAvailable %s MiB, swap-in-use key absent → "
                             "ONE-SIDED (only the headroom column is comparable)"
                             % (pida, pidb, ("+" if da >= 0 else "−") + mib(abs(da))))
                continue
            du = ub - ua
            if du < 0 and da < 0:
                word = ("REGIME FLIP — swap in use fell %s MiB (%s → %s) while MemAvailable fell %s "
                        "MiB (%s → %s) across the restart: the new process re-admitted what the old "
                        "one held in swap and spent RAM headroom doing it, so the rate rules went "
                        "quiet while the memory floor got closer"
                        % (mib(-du), mib(ua), mib(ub), mib(-da), mib(ra["avail"]), mib(rb["avail"])))
            elif du < 0 and da > 0:
                word = ("RECOVERY — swap in use fell %s MiB while headroom ROSE %s MiB"
                        % (mib(-du), mib(da)))
            elif du > 0 and da < 0:
                word = ("REGIME FLIP, OUTWARD — swap grew %s MiB while headroom fell %s MiB"
                        % (mib(du), mib(-da)))
            elif du == 0:
                word = ("SWAP IN USE UNCHANGED (%s MiB both sides) while MemAvailable moved %s %s MiB"
                        % (mib(ua), "+" if da >= 0 else "−", mib(abs(da))))
            else:
                word = ("ONE-SIDED — Δswap in use %s %s MiB, ΔMemAvailable %s %s MiB"
                        % ("+" if du >= 0 else "−", mib(abs(du)),
                           "+" if da >= 0 else "−", mib(abs(da))))
            parts.append("pid %s (`%s`) → pid %s (`%s`): %s"
                         % (pida, ra["name"], pidb, rb["name"], word))
        withheld = len(pairs) - len(parts)
        txt = "; ".join(parts)
        if withheld > 0:
            txt += " (%d older restart pair(s) not printed)" % withheld
        return txt
    L.append("| do the two free columns move in OPPOSITE directions when the engine generation "
             "changes? | %s |" % cell(flip))
    L.append("| readings in this scope with no engine pid, excluded from every trajectory above | %s |"
             % cell(lambda p: "%d of %d readings" % (p["nopid"], p["n"])))

    def badrss(p):
        if not p["bad"]:
            return "none (every `engine_rss_mib` in this scope is at or below `mem_total_mib`)"
        det = ["`%s` reads %s MiB against `mem_total_mib` = %s MiB"
               % (r["name"], mib(r["rss_bad"][0]), mib(r["rss_bad"][1])) for r in p["bad"][:3]]
        return ("%d reading(s) carry an engine RSS larger than the machine's total memory and are "
                "excluded from every delta above: %s%s"
                % (len(p["bad"]), "; ".join(det),
                   (" (%d more not printed)" % (len(p["bad"]) - 3)) if len(p["bad"]) > 3 else ""))
    L.append("| readings whose `engine_rss_mib` exceeds the box's own `mem_total_mib` "
             "(an impossible field value: reported, named, and never used in arithmetic) | %s |"
             % cell(badrss))
    return L


def build(rows, as_of, consts, day, window_hours, legs_started):
    go = [r for r in rows if r["rc"] == 0]
    nogo = [r for r in rows if r["rc"] == 3]
    gap = [r for r in rows if r["rc"] == 1]
    day_rows = [r for r in rows if r["ts"].strftime("%Y%m%d") == day]
    cut = as_of - datetime.timedelta(hours=window_hours)
    win_go = [r for r in go if r["ts"] > cut]
    win_rows = [r for r in rows if r["ts"] > cut]
    b = band(rows, consts["SWAP_RATE_MAX_MIB_S"])
    fp = footprint(rows)
    db = day_band(day_rows, consts["SWAP_RATE_MAX_MIB_S"])
    wb = day_band(win_rows, consts["SWAP_RATE_MAX_MIB_S"])
    cb = day_band(rows, consts["SWAP_RATE_MAX_MIB_S"])
    scopes = [("DAY `%s`" % day, db), ("last %d h" % window_hours, wb), ("whole corpus", cb)]
    ws = window_streak(win_rows, day_rows, as_of)
    L = []
    L.append("# PUB preflight reading census (generated)")
    L.append("")
    L.append("Written by `scripts/pub_preflight_census.py`; this file is that tool's output, never a")
    L.append("transcription of a tick note. It moves no benchmark byte and registers no contour feature.")
    L.append("Readings are stored outside this repository (the producer command is untracked, like every")
    L.append("connection seam on this line), so this census runs on the workstation only and is not")
    L.append("CI-enrolled; its arithmetic is pinned by `harness/pub_preflight_census_test.py` over")
    L.append("synthetic readings, and `--check` re-derives this table from the retained readings.")
    L.append("")
    L.append("Census stamp: `%s`, gate sha16 `%s`, window `as-of %s` "
             "(%d readings inside the window). v15 adds the BUILD axis the corpus never had "
             "(tick 208, 2026-11-16): the producer now emits `health_body_sha16` (SHA-256/16 of "
             "the /health body the `health_loaded` rule already fetches — zero extra fetches) and "
             "`health_max_context` (the same body's advertised context); the gate validates the "
             "pair as INPUT — exactly one key, or a value failing its format, is an input gap, "
             "absence is a coverage line, and no refusal rule reads either key, so every stored "
             "reading keeps a byte-identical verdict — and the table groups readings by build, "
             "crosswalks build against pid, and names the pid<->build anomalies, because at the "
             "16.11 cut the two axes disagreed: all nine refusals of the day sat on pid 175316 "
             "(retired 09:59) while live pid 438502 knew only GOs, and the 09:59 restart that also "
             "swapped the build (serve context 262 144 -> 196 608, sampling header gone, binary "
             "path moved) was invisible to every stored byte. Until a reading carries a valid "
             "pair, every build cell prints its coverage split and no verdict may be credited or "
             "blamed to a named build. v14 gives the READINGS half of the headroom "
             "projection its cadence denominator: v13 converted a projected number of MINUTES into "
             "a number of READINGS by dividing by the monotone run's MEAN cadence and printed one "
             "integer, while the intervals inside that same run were 28, 39, 35, 51, 9, 16 and 32 "
             "min (a 5.7x spread), so at the 2026-11-16 13:37 cut its `about 9 further readings` was "
             "one value drawn from a 5-33 range — the projection was labelled a projection, but its "
             "second number rested on an unstated uniform-cadence assumption, which is the producer "
             "rule 'divide by a measured window, never a nominal count' arriving one level further "
             "down. v14 keeps the minutes primary (rate over a measured span), prints the reading "
             "count as the band the run's own intervals support, names that denominator in the cell "
             "(interval count, min-max, mean), collapses to a single count only when the intervals "
             "are uniform within `MEM_INTERVAL_FLAT_RATIO`, and prints NO reading count when no "
             "positive interval exists, because two draws sharing a timestamp must never reach a "
             "denominator. v10 derives the engine-state-D refusal set from the "
             "readings' own `engine_state` key and requires it to equal the set the gate's reason line "
             "names, at all three scopes, and prints how many state-D refusals sat on a device the "
             "device rule calls quiet, with the denominator of state-D refusals that carry a device "
             "window: until now only the swap rule was ever re-derived from the columns, and the state "
             "rule is the one rule with no ceiling to disagree about (the gate fires when "
             "`engine_state` contains `D`, so a `Dl` state fires). v9 counts WHICH GATE RULE refused each reading, read "
             "out of the gate's own refusal text at the three published scopes, and cross-checks the "
             "swap-band refusal set (derived here from the key=value columns) against the set whose "
             "gate reason line names the swap rule (the gate's own claim): every tick sentence that "
             "attributed a refusal to a rule had never been computed. The rule table is BOUND to the "
             "gate source — each anchor prefix must appear in it and the refusal-site count must match "
             "— an unmappable reason prints UNATTRIBUTED and moves the exit code to 4, and the "
             "preserved-shape sentence at the end of this paragraph is now GENERATED from the stamp "
             "number, because the hand-typed one claimed only v1-v6 are preserved: two stamps short of "
             "the v7 and v8 changes this same sentence describes. v8 splits one row that carried two denominators: "
             "the swap rule's OWN decision boundary (highest window the rule accepted, lowest "
             "window it refused, judged on the rule's decision whatever the gate verdict was) and "
             "the launchable-column gap (highest gate-GO draw to lowest refusal), which is what "
             "v5-v7 printed as 'dead zone' and what every tick quoted as the rule's resolution. At "
             "the committed 2026-11-16 02:14 cut the corpus gap is 0.905-1.060 x while the rule "
             "boundary is 0.940-1.060 x, because `preflight-20261116-0214.txt` carries swap "
             "18.8 MiB/s = 0.94 x of the 20.0 ceiling, which the swap rule ACCEPTED (the reading "
             "was refused instead by the device, state-D and GPU-mean rules): the rule is measured "
             "accepting at 0.94 x, and the v7 'POPULATED (1 windows inside)' at all three scopes "
             "was produced by exactly that accepted draw. A judged draw inside the rule band is "
             "impossible by definition — it would itself be an accepted or a refused point and move "
             "the bound that excludes it — so the boundary row prints EMPTY BY CONSTRUCTION and "
             "names input-gap readings inside the band separately. v7 prints the v5 rule band at "
             "THREE scopes "
             "(the as-of calendar day, the sliding 24 h window, the whole corpus) with the scope "
             "word inside every row label and a computed dead-zone scope state, because a dead zone "
             "is a property of the row set it is measured over and only the day scope was ever "
             "published: at the 2026-11-16 01:50 cut the day cell put the GO-to-refusal zone 25.3 "
             "MiB/s wide while the corpus put it at 3.1 MiB/s (highest launchable draw 0.905x, "
             "lowest swap-rule refusal 1.06x, empty over the 25 launchable draws and 35 swap-rule "
             "refusals that carry a swap window — only 70 of the 158 stored files carry those keys "
             "at all, so the block prints its band denominator), and the 2026-11-15 tick sentences "
             "that said \"the dead zone\" (0.38-1.06x, "
             "then 0.74-1.06x) were day-scoped numbers presented as a property of the rule — tick "
             "192 and 193's scope-word defect a third time in the same column. v6 adds three "
             "COMPUTED continuity rows over the "
             "sliding 24 h window — the trailing consecutive-refusal run ending at the newest "
             "reading, readings/hours since the last gate-GO with that GO named and aged, and a "
             "window-run-vs-day-run state word — because the v5 DAY table resets at midnight: at "
             "the first reading of 2026-11-16 (00:04) the day cells printed a run of 1 and "
             "`n/a — no GO of this day` while the box had refused FOUR readings in a row across "
             "midnight and its last GO was 162 minutes back, one of the 7 launchable windows this "
             "same table counts in the last 24 h. The day cells were correct as labelled and useless "
             "as a streak, which is tick 192's class (a figure that lives only in prose stops being "
             "recomputed) one level down. v5 adds the DAY rule-band table (8 computed cells: "
             "the GO and swap-refusal ratio bands, the refusal median, refusals decided by a rule "
             "other than swap, the GO-to-refusal dead zone with its EMPTY/POPULATED state word and "
             "the count inside it, the longest consecutive-refusal run, readings since the last GO, "
             "and the age of the launchable-footprint maximum with the trailing windows above it) — "
             "those figures had lived only in tick prose and had been re-typed from a stale cut: on "
             "2026-11-15 the refusal median is 4.225x at 24 readings, 3.985x at 30 and 3.745x at 31, "
             "while two consecutive ticks quoted 4.22x as today's number. v4 adds two COMPUTED "
             "footprint ceiling rows — the "
             "ceiling dry-run and its state word — because at the 08:57 reading on 2026-11-15 the "
             "launchable footprint maximum (8 520 MiB) grew ABOVE the refused-group maximum "
             "(6 957 MiB), so the only footprint ceiling the arming rule allows fires on nothing in "
             "the corpus; that consequence was hand-derived in a tick note and now belongs to the "
             "tool (tick 172's class of defect). v3 removes the CORPUS-WIDE reading count from "
             "that window-identity sentence: the number counted every `preflight-*.txt` file "
             "present at run time, so taking one reading after the frozen window made `--check` "
             "of an untouched snapshot report drift (measured 2026-11-15 01:00 at the committed "
             "window `as-of 2026-11-14 23:47`: `123 stored readings` became `124 stored "
             "readings`, while the window count, every verdict and every band cell stayed "
             "identical). The corpus count is now printed on stdout only, outside the committed "
             "file. v2 added two COMPUTED group-state rows — the swap-peak band state and the "
             "footprint group separation — because v1 printed \"Band: nothing between X and Y\" "
             "unconditionally, and at 23:13 on 2026-11-14 the order of X and Y reversed: the "
             "table went on asserting an empty interval the data had withdrawn. %s"
             % (census_stamp_name(), sha16(GATE), as_of.strftime("%Y-%m-%d %H:%M"), len(rows),
                preserved_stamp_sentence(CENSUS_STAMP)))
    L.append("")
    L.append("Ceilings read out of the gate source at run time, so this table cannot disagree with "
             "the rule it reports: `SWAP_RATE_MAX_MIB_S = %s` (window MEAN; the peak statistic is "
             "reported, not gated), `GPU_UTIL_MAX_MEAN_PCT = %s` (the window mean, never the peak), "
             "and the device-read ceiling is SCOPE-DEPENDENT: `BLK_READ_MAX_MIB_S_WHOLE = %s` applies "
             "to every reading carrying `blk_scope=whole-disk`, while `BLK_READ_MAX_MIB_S = %s` "
             "applies only to readings with NO scope key (the old diskstats sum, which double-counts "
             "partitions, i.e. about 2x the device). The two numbers are the SAME physical point; a "
             "file with an unrecognised scope value is an input gap the gate never judges. Naming one "
             "of these numbers without its scope is exactly how a generated table starts disagreeing "
             "with the rule it claims to report (measured 2026-11-14 18:47: a whole-disk reading of "
             "56.2 MiB/s was refused by the gate while the first version of this table printed 100.0 "
             "as the whole-disk ceiling)."
             % (consts["SWAP_RATE_MAX_MIB_S"], consts["GPU_UTIL_MAX_MEAN_PCT"],
                consts["BLK_READ_MAX_MIB_S_WHOLE"], consts["BLK_READ_MAX_MIB_S"]))
    L.append("")
    L.append("| census cell | value |")
    L.append("|---|---|")
    L.append("| gate verdict GO | %d |" % len(go))
    L.append("| gate verdict NO-GO | %d |" % len(nogo))
    L.append("| gate verdict input gap | %d |" % len(gap))
    L.append("| device scope of the readings in this window | %d whole-disk (`%s` ceiling) / %d unscoped "
             "(`%s` ceiling) / %d unknown scope |" % (
                 sum(1 for r in rows if r["scope"] == "whole-disk"),
                 consts["BLK_READ_MAX_MIB_S_WHOLE"],
                 sum(1 for r in rows if r["scope"] == "unscoped"),
                 consts["BLK_READ_MAX_MIB_S"],
                 sum(1 for r in rows if r["scope"] == "unknown")))
    L.append("| readings of the as-of day | %d (%d GO / %d NO-GO / %d gap) |" % (
        len(day_rows),
        sum(1 for r in day_rows if r["rc"] == 0),
        sum(1 for r in day_rows if r["rc"] == 3),
        sum(1 for r in day_rows if r["rc"] == 1)))
    L.append("| launchable (GO) windows in the last %d h | %d |" % (window_hours, len(win_go)))
    L.append("| leg completions recorded in that window | %d |" % legs_started)
    L.append("| readings carrying the swap-peak key | %d (NaN %d, parseable %d) |" % (
        b["n_carried"], b["n_nan"], b["n_parseable_all"]))
    L.append("| ...of those, gate-JUDGED readings with a parseable peak (the band's set) | %d "
             "(the other %d sit in readings the gate refuses to judge at all) |" % (
                 b["n_parseable"], b["n_parseable_all"] - b["n_parseable"]))
    L.append("| swap-mean-passing windows with a peak | %d |" % b["pass_n"])
    L.append("| swap-mean-failing windows with a peak | %d |" % b["fail_n"])
    L.append("| highest peak inside a swap-mean-PASSING window | %s MiB/s |" % rate(b["pass_max"]))
    L.append("| lowest peak inside a swap-mean-FAILING window | %s MiB/s |" % rate(b["fail_min"]))
    L.append("| swap-peak band state (computed, never asserted) | %s |" % band_state_text(b))
    L.append("| arming counter (launchable windows carrying the peak) | %d of %d |" % (
        b["arming"], ARMING_THRESHOLD))
    L.append("")
    L.append("Engine swap FOOTPRINT (added 2026-11-14, tick 159) — reported, never banded:")
    L.append("")
    L.append("| footprint cell | value |")
    L.append("|---|---|")
    L.append("| readings carrying `engine_vmswap_mib` | %d (NaN %d, parseable %d) |" % (
        fp["n_carried"], fp["n_nan"], fp["n_parseable"]))
    L.append("| footprint on gate-GO windows (launchable) | %d (median %s MiB, max %s MiB) |" % (
        fp["n_go_launchable"], mib(fp["go_median"]), mib(fp["go_max"])))
    L.append("| footprint on gate-NO-GO windows | %d (median %s MiB, min %s MiB) |" % (
        fp["n_nogo"], mib(fp["nogo_median"]), mib(fp["nogo_min"])))
    L.append("| footprint group separation (computed, never asserted) | %s |" % footprint_sep_text(fp))
    L.append("| footprint ceiling dry-run (computed; it arms NOTHING) | %s |"
             % footprint_ceiling_text(fp))
    L.append("| footprint ceiling state (computed) | %s |" % str(fp["dry_state"]).upper())
    L.append("| page-cache share of swap in use (`swap_cached_mib` / used) | %d readings, median %s "
             "percent, max %s percent |" % (fp["n_share"], pct(fp["share_median"]),
                                            pct(fp["share_max"])))
    L.append("| footprint arming counter (launchable windows carrying it) | %d of %d |" % (
        fp["n_go_launchable"], ARMING_THRESHOLD))
    L.append("| ...of those launchable draws: non-zero footprint / exactly 0 MiB | %d non-zero / %d "
             "zero (the counter above counts COVERAGE; a 0 MiB draw says that process held no swap in "
             "that window, which is a measurement and sets no ceiling) |" % (
        fp["go_nonzero"], fp["go_zero"]))
    L.append("| ...the same split on the refused side | %d non-zero / %d zero (the non-zero refused "
             "draws are the only work a footprint rule could ever be given) |" % (
        fp["nogo_nonzero"], fp["nogo_zero"]))
    L.append("| footprint informative-coverage state (computed) | %s |" % footprint_info_text(fp))
    L.append("")
    L.append("The as-of **DAY** rule band (added 2026-11-15, tick 192) — today's verdicts only, every")
    L.append("ratio taken against `SWAP_RATE_MAX_MIB_S = %s` and every number recomputed at this"
             % consts["SWAP_RATE_MAX_MIB_S"])
    L.append("reading, because the same three figures quoted in tick prose had been carried forward")
    L.append("from an earlier cut instead of re-derived (the median reads 4.225x at 24 readings,")
    L.append("3.985x at 30 and 3.745x at 31 on this day's files):")
    L.append("")
    L.append("| day cell | value |")
    L.append("|---|---|")
    L.extend(day_band_text(db, consts["SWAP_RATE_MAX_MIB_S"]))
    L.append("")
    L.append("The `rule OTHER than swap` row is the day's honest split of the refusal column: a")
    L.append("refusal whose swap window is quiet was decided by the device or the GPU-mean rule and")
    L.append("must not enter the swap-rule band (the 19:24 reading on 2026-11-15 is that case at")
    L.append("0.00x swap traffic with 179.3 MiB/s of whole-disk reads). The launchable-footprint age")
    L.append("row is the same warning for the state variable: the ceiling the dry-run uses was set by")
    L.append("one launchable window, and every reading since then may sit far above it without that")
    L.append("ceiling meaning anything about the box right now.")
    L.append("")
    L.append("The SAME rule band at three scopes (added 2026-11-16, tick 195) — because a dead zone")
    L.append("is a property of the row set it is measured over, and only the calendar-day row set was")
    L.append("ever published. Measured at the 2026-11-16 01:50 cut (dated, not current): the day cell")
    L.append("spanned a dead zone 25.3 MiB/s wide while the corpus put the highest launchable swap")
    L.append("draw at 0.905x of the ceiling and the lowest swap-rule refusal at 1.06x, a 3.1 MiB/s")
    L.append("band, 8.2x narrower. Every tick")
    L.append("sentence that said \"the dead zone\" (2026-11-15: \"0.38-1.06x\", then \"0.74-1.06x\") was")
    L.append("a day-scoped number presented as a property of the rule, so the scope word now travels")
    L.append("with the cell, and the block prints its own band denominator: only a reading that")
    L.append("carries `swap_in + swap_out` can be banded at all (the producer added those keys")
    L.append("2026-11-14 09:26), so a corpus band describes the sampler era since that hour, never")
    L.append("the whole archive. Each ratio is still the reading's own sampled window against the")
    L.append("gate's current ceiling, which is what the swap-mean rule compares:")
    L.append("")
    L.extend(scope_band_text(scopes, consts["SWAP_RATE_MAX_MIB_S"], window_hours))
    L.append("")
    L.append("Verdict continuity across the sliding window (added 2026-11-16, tick 193) — the day")
    L.append("table above is scoped to the calendar day and resets at midnight, which is correct as")
    L.append("labelled and misleading as a streak. At the first reading of 2026-11-16 (00:04, gate")
    L.append("NO-GO) the day cells printed a longest run of 1 reading and `n/a — no GO of this day`,")
    L.append("while the box had refused four readings in a row across midnight (21:57, 22:32, 23:08")
    L.append("on 15 Nov and 00:04 on 16 Nov) and its last GO sat 162 minutes earlier at 21:22, one of")
    L.append("the 7 launchable windows this same table counts in the last 24 h. A tick that reads only")
    L.append("the day cells would report a fresh day with one refusal, so the streak is computed here")
    L.append("too, from the same per-file gate returncodes, and the scope divergence gets a state word:")
    L.append("")
    L.append("| window cell (last %d h) | value |" % window_hours)
    L.append("|---|---|")
    L.extend(window_streak_text(ws, window_hours))
    L.append("")
    L.append("Which gate RULE refused (added 2026-11-16, tick 197) — the verdict column says a reading")
    L.append("was refused and never says BY WHAT. Every tick attributed refusals in prose (\"the night's")
    L.append("first out-heavy swap window\", \"02:14 died on the device, state-D and GPU-mean rules\") and")
    L.append("not one of those sentences was ever computed. The counts below come out of the gate's own")
    L.append("refusal lines, from the same subprocess run that produced the verdict column, so a rule that")
    L.append("starts or stops firing moves a cell here instead of hiding in a report. The rule table is")
    L.append("BOUND to the gate source (every anchor must appear in it and the refusal-site count must")
    L.append("match), an unmappable reason names its file and moves the exit code to 4, and TWO rows")
    L.append("compare two independent derivations of one set. The swap row (v9) takes the refusals whose")
    L.append("sampled window sits at or above `SWAP_RATE_MAX_MIB_S` against the refusals whose gate")
    L.append("reason line names the swap rule. The state row (v10) takes the refusals whose own")
    L.append("`engine_state` key contains `D` — the gate's exact substring test, so `Dl` fires, read")
    L.append("through the gate's own key=value parser — against the refusals whose reason line names the")
    L.append("state rule; a gate that sampled the launcher instead of the model, or a reason string")
    L.append("renamed under the rule table, moves that cell instead of quietly changing refusals. The")
    L.append("device-quiet row then splits the state-D refusals physically: a state-D wait on a device")
    L.append("the device rule calls quiet is a page wait served from RAM (tick 200's re-admission class),")
    L.append("a state-D wait at a saturated device is the foreign-reader class that motivated that rule,")
    L.append("and the row prints how many state-D refusals have a device window at all, because a")
    L.append("refusal taken before that key existed belongs to neither class. A rule that fired on")
    L.append("nothing still gets a row: a missing row and a zero row")
    L.append("read the same way in prose, which is how a rule that never fires gets mistaken for a rule")
    L.append("nobody counted:")
    L.append("")
    attr_lines, attr_findings = rule_attribution_text(
        [("DAY `%s`" % day, day_rows), ("last %d h" % window_hours, win_rows),
         ("whole corpus", rows)], consts["SWAP_RATE_MAX_MIB_S"], consts)
    L.extend(attr_lines)
    L.append("")
    L.append("**Which engine process a pooled statistic describes (census v11).** The producer names")
    L.append("the pid it actually sampled in a comment line, and the gate's parser skips comments — so")
    L.append("every footprint, RSS and page-cache figure above has always been pooled over whatever")
    L.append("engine processes the corpus happened to contain. That is harmless while one process")
    L.append("serves the whole window and wrong the moment the endpoint's engine is restarted (a")
    L.append("version bump, a config ladder, a watchdog restart): a footprint maximum recorded by a")
    L.append("retired process is not a property of the endpoint, and the pre-registered footprint")
    L.append("ceiling would be drawn from precisely such a maximum. Generation counts are printed")
    L.append("before the per-generation detail, the unattributable readings are printed as their own")
    L.append("row, and the state word is computed:")
    L.append("")
    L.extend(engine_generation_text([("DAY `%s`" % day, day_rows),
                                     ("last %d h" % window_hours, win_rows),
                                     ("whole corpus", rows)]))
    L.append("")
    L.append("**A pid generation and a build generation are different axes, and on 2026-11-16 they")
    L.append("disagreed (census v15, tick 208).** Every generation row above is a PROCESS id, and a")
    L.append("pid answers only \"did this process swap?\". At the 14:38 cut the live pid 438502 had")
    L.append("nine readings and zero refusals while all nine of the day's refusals belonged to pid")
    L.append("175316, retired at 09:59 — and that same 09:59 restart was a BUILD swap (serve context")
    L.append("262 144 -> 196 608, sampling header gone, binary path moved) that not one of the 174")
    L.append("stored readings named in a byte. A refusal set that belongs to a retired PROCESS tells")
    L.append("you nothing about the endpoint you are about to launch into, and it tells you less about")
    L.append("the BUILD you are actually quoting. The producer now hashes the /health body it already")
    L.append("fetches for the `health_loaded` rule (`health_body_sha16`, SHA-256/16) and emits the")
    L.append("context that body advertises (`health_max_context`); the gate validates the pair and")
    L.append("never gates on it, so the whole stored corpus keeps byte-identical verdicts. The")
    L.append("build rows below print the coverage split first — until the first post-change reading")
    L.append("lands, every scope says 0 pairs and no verdict may be credited to a named build:")
    L.extend(engine_build_text([("DAY `%s`" % day, day_rows),
                                ("last %d h" % window_hours, win_rows),
                                ("whole corpus", rows)]))
    L.append("")
    L.append("**Coverage is not information (census v12, 2026-11-16, tick 204).** The footprint arming")
    L.append("counter counts launchable windows that CARRY `engine_vmswap_mib`, and a window reading")
    L.append("`engine_vmswap_mib=0` carries it. Tick 203 caught the consequence on live bytes: the")
    L.append("generation the endpoint runs now answered 0 MiB in every window it produced — including")
    L.append("one taken inside its own GPU-99 %/157 W campaign — while the pooled dry-run ceiling still")
    L.append("bound to a retired process. Arming a footprint rule off that coverage admits exactly one")
    L.append("value, `> 0 MiB`, i.e. a guard against a failure mode the live process has never")
    L.append("demonstrated once. The split is now printed rather than argued: the footprint block")
    L.append("separates non-zero from exactly-zero draws on BOTH sides and states what the counter is")
    L.append("buying (INFORMATIVE / ZERO-DRAW-DOMINATED / ALL-ZERO), and the generation block reports")
    L.append("per generation how many of its footprint draws are non-zero and whether the NEWEST")
    L.append("sampled generation has ever recorded a footprint above 0 MiB (ZERO-FOOTPRINT GENERATION).")
    L.append("A zero draw is never dropped from the coverage count — it is a real measurement — it just")
    L.append("stops being able to pose as a ceiling.")
    L.append("")
    L.append("**The two FREE columns, and the regime change that prose had been hiding (census v13,")
    L.append("2026-11-16, tick 205).** Every rule this table bands is a RATE over one 6 s window, and")
    L.append("the gate's memory rule (`mem-available-low`, floor `MEM_AVAILABLE_MIN_MIB`, read out of")
    L.append("the gate source at run time like every other ceiling) was the one threshold in force that")
    L.append("no published cell ever quoted a distance to. 204 ticks of prose wrote MemAvailable into a")
    L.append("sentence next to a verdict and never trended it, and that prose hid a regime change:")
    L.append("generation 175316 ran 15-16 Nov at MemAvailable 17 675-21 441 MiB with 16 062-16 839 MiB")
    L.append("of swap in use, and the live generation 438502 runs at 4 938-6 618 MiB with swap in use")
    L.append("flat at 65 MiB. The two free columns moved in OPPOSITE directions across that restart —")
    L.append("which is also why the morning's page-in storms (6.82x, 6.91x and 10.69x of the swap")
    L.append("ceiling, ticks 196/199/200) simply stopped: there was nothing left swapped to page in.")
    L.append("The block below therefore states headroom as a per-generation STATE with a computed")
    L.append("trend, attributes a headroom fall to the sampled process's own RSS growth or names it")
    L.append("UNATTRIBUTED, and labels its own forward look a projection in the cell that prints it.")
    L.append("No ceiling is registered here and no rule is armed: the numbers this block prints are the")
    L.append("evidence a decision would need, not the decision.")
    L.append("")
    L.extend(memory_headroom_text([("DAY `%s`" % day, day_rows),
                                   ("last %d h" % window_hours, win_rows),
                                   ("whole corpus", rows)], consts))
    L.append("")
    L.append("**A projection that counts READINGS has a sampling cadence in its denominator (census "
             "v14, 2026-11-16, tick 206).** The trend row above answers two different questions and "
             "v13 answered the second one badly. `≈298 min after the newest draw` is a rate over a "
             "measured span and is quotable. `about 9 further readings` is that same quantity "
             "divided by a CADENCE, and v13 used the run's mean cadence without naming it. At the "
             "2026-11-16 13:37 cut the newest generation's monotone fall spans 210 min over 8 draws, "
             "so the mean cadence is 30.0 min — and the intervals behind that mean are 28, 39, 35, "
             "51, 9, 16 and 32 min, a 5.7x spread with a 9-minute interval inside it, because these "
             "readings are taken by ticks and reports, not by a scheduler. The projected 298 minutes "
             "is therefore 5 readings at the run's slowest interval and 33 at its fastest, and v13's "
             "printed `9` was neither bound: it was the mean assumption wearing the costume of a "
             "measurement. This is the same defect the producer rules already forbid one level up "
             "(MiB/s computed over a nominal 6 s loop instead of the measured 6.17 s, tick 14.11) and "
             "the same one the band rows were corrected for twice (scope, then denominator): a rate "
             "or a conversion may only be quoted with the window it was divided by. The row now "
             "prints the interval count, the min-max range and the mean beside the count, states the "
             "count as a band whenever the intervals are not uniform within "
             "`MEM_INTERVAL_FLAT_RATIO` = %s, and prints NO count at all when the monotone draws "
             "share timestamps — a zero interval must never reach a denominator. Nothing in the gate "
             "moved: the projection describes when the gate's own `mem-available-low` floor would be "
             "reached at the observed slope, and the floor, the ceiling set and the rule order are "
             "byte-identical to the run that produced every stored verdict in this table."
             % (MEM_INTERVAL_FLAT_RATIO,))
    L.append("**Why a state variable joins a table of rates.** Every swap rule the gate has is a rate")
    L.append("over one 6 s window, and a rate is blind in BOTH directions: measured 2026-11-14")
    L.append("21:31-21:38, three back-to-back 5 s windows on the endpoint box took 320 MiB / 0 / 0 of")
    L.append("swap-in, a producer-shaped 6 s window read 134.3 MiB/s in and 0.0 out, a second such")
    L.append("window 3 min later read ONE page in, and across that whole span `pswpout` moved")
    L.append("1 741.9 MiB that not one 6 s window saw — a ceiling on a rate can neither stop the")
    L.append("outward storm (which is what the machine note says restarts the engine mid-leg) nor")
    L.append("detect the refault load that precedes it. The footprint is the state behind those rates:")
    L.append("the engine's own `VmSwap` grew 5 478 008 -> 6 004 096 kB across eight minutes while")
    L.append("`MemAvailable` read 19-21 GiB and `SwapFree` 53.6 GiB, 35 359 of 35 361 major faults in")
    L.append("a 6 s window belonged to the engine pid, and 52.5-57.1 % of the swap in use was ALSO")
    L.append("page-cache resident in RAM, which is why the device rule saw 0.1 MiB/s of reads through")
    L.append("the whole event (tick 151 measured the same complementarity from the other side: a")
    L.append("443.8 MiB/s swap window at 0.1 MiB/s of device reads). The footprint series that joined")
    L.append("the census the same evening shows that state walking on its own: one engine process")
    L.append("(pid unchanged since 16:31) held 3 576 -> 6 291 -> 3 965 MiB of `VmSwap` at 22:39 / 23:13")
    L.append("/ 23:47 — +2 715 MiB between two gate-`GO` readings whose sampled 6 s windows took 0.0 and")
    L.append("18.1 MiB/s in, then -2 326 MiB into a window that sampled 92.7 MiB/s in and 0.0 out while")
    L.append("swap in use fell 12 573 -> 10 967 MiB, i.e. the pages coming back home. A state variable")
    L.append("that moves 2.7 GiB in 34 minutes with no leg running is exactly why the footprint is")
    L.append("censused and NOT banded. No ceiling is proposed here:")
    L.append("arming this statistic needs the same pre-registered threshold as the peak, and the")
    L.append("footprint column starts filling with the first reading that carries the key, so this")
    L.append("table's zeros are a coverage fact about stored history, not a measurement of health.")
    L.append("")
    L.append("**The two denominators, side by side, because they are not the same set.** The band above")
    L.append("is defined on the **swap-mean rule**, not on the verdict column: the highest peak in a")
    L.append("gate-`GO` window is %s MiB/s and the lowest peak in a gate-`NO-GO` window is %s MiB/s, and"
             % (rate(b["go_max"]), rate(b["nogo_min"])))
    L.append("the second number is the trap - a reading can be NO-GO on the device or the GPU-mean rule")
    L.append("while its swap window is quiet at 0.0, and a NaN-carrying reading is an INPUT GAP the gate")
    L.append("never judges at all (%d such readings carry the peak key)." % b["n_nan"])
    if b["band_state"] == "crossed":
        L.append("**The band has CROSSED**: the highest launchable peak (%s MiB/s) now sits at or above"
                 % b["pass_max"])
        L.append("the lowest mean-failing peak (%s MiB/s), so the two groups overlap. A threshold high"
                 % b["fail_min"])
        L.append("enough to spare every launchable window leaves at least one mean-failing window")
        L.append("unrefused, and any lower threshold refuses a window the mean rule launches — on this")
        L.append("corpus a peak rule adds no refusal the mean rule does not already make. The arming")
        L.append("counter (%d of %d launchable windows carrying the statistic) counts COVERAGE, not"
                 % (b["arming"], ARMING_THRESHOLD))
        L.append("support for a ceiling, and reaching 30 would not change that conclusion.")
    elif b["band_state"] == "separated":
        L.append("Band: nothing between %s and %s MiB/s, so a ceiling placed in that gap fires only"
                 % (b["pass_max"], b["fail_min"]))
        L.append("where the mean rule already refuses — it is safe to add, not informative. The peak")
        L.append("stays REPORTED, not gated, until the pre-registered arming threshold")
        L.append("(%d launchable windows carrying the statistic) is met." % ARMING_THRESHOLD)
    else:
        L.append("Band: NO-DATA — one of the two groups holds no parseable peak, so no interval exists")
        L.append("to classify yet. The peak stays REPORTED, not gated, until the pre-registered arming")
        L.append("threshold (%d launchable windows carrying the statistic) is met." % ARMING_THRESHOLD)
    L.append("")
    return "\n".join(L) + "\n", attr_findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.expanduser("~/pub-bench"))
    ap.add_argument("--as-of", default=None, help="YYYYMMDD-HHMM bound (default: newest reading)")
    ap.add_argument("--day", default=None, help="YYYYMMDD for the per-day row (default: as-of day)")
    ap.add_argument("--window-hours", type=int, default=24)
    ap.add_argument("--markdown", default=None)
    ap.add_argument("--check", default=None)
    ap.add_argument("--prev-as-of", default=None,
                    help="earlier window bound (YYYYMMDD-HHMM) for the window transition printed "
                         "on stdout only; defaults to the previous stored reading, so the "
                         "attribution is never composed by hand again. The committed table is "
                         "byte-identical with or without it.")
    ap.add_argument("--no-transition", action="store_true",
                    help="suppress the stdout window-transition block")
    a = ap.parse_args()

    if not os.path.isdir(a.dir):
        print("CENSUS GAP: readings dir %s does not exist" % a.dir)
        return 1
    files = sorted(glob.glob(os.path.join(a.dir, "preflight-*.txt")))
    if not files:
        print("CENSUS GAP: no preflight-*.txt readings under %s" % a.dir)
        return 1
    # Bound the refusal-rule table to the gate BEFORE paying for one gate subprocess per reading:
    # if the gate renamed or added a refusal reason, every attribution cell would be wrong, and the
    # census must say so rather than print a confident rule count (census v9, tick 197).
    rule_problems = refusal_rule_guard()
    if rule_problems:
        print("CENSUS GAP: the refusal-rule table no longer matches the gate source — "
              + "; ".join(rule_problems))
        return 1
    stamps = [parse_stamp(f) for f in files]
    if a.as_of:
        try:
            as_of = datetime.datetime.strptime(a.as_of, "%Y%m%d-%H%M")
        except ValueError:
            print("CENSUS GAP: --as-of must be YYYYMMDD-HHMM, got %r" % a.as_of)
            return 1
    else:
        good = [s for s in stamps if s]
        if not good:
            print("CENSUS GAP: no readable reading stamp in %s" % a.dir)
            return 1
        as_of = max(good)
    day = a.day or as_of.strftime("%Y%m%d")
    prev_as_of = None
    derived_bound = None
    if a.prev_as_of:
        derived_bound = "operator-supplied bound"
        # Validate before any gate call: a bad bound must cost nothing.
        try:
            prev_as_of = datetime.datetime.strptime(a.prev_as_of, "%Y%m%d-%H%M")
        except ValueError:
            print("CENSUS GAP: --prev-as-of must be YYYYMMDD-HHMM, got %r" % a.prev_as_of)
            return 1
        if prev_as_of >= as_of:
            print("CENSUS GAP: --prev-as-of %s is not earlier than --as-of %s — a window "
                  "transition needs an earlier bound"
                  % (prev_as_of.strftime("%Y%m%d-%H%M"), as_of.strftime("%Y%m%d-%H%M")))
            return 1

    rows, unnamed, as_of = census(a.dir, as_of, day, a.window_hours)
    if unnamed:
        print("CENSUS GAP: %d file(s) whose name is not preflight-YYYYMMDD-HHMM.txt: %s"
              % (len(unnamed), ", ".join(os.path.basename(f) for _, f in unnamed)))
        return 1
    if prev_as_of is None and not a.no_transition:
        # The default bound is the PREVIOUS stored reading, which is exactly what a tick compares
        # against when it writes "N -> M with X aged out". Making it the default is the point: the
        # sentence stops being composed by hand, so the net-zero case cannot be missed again.
        earlier = [r["ts"] for r in rows if r["ts"] < as_of]
        if earlier:
            prev_as_of = max(earlier)
            derived_bound = "derived: previous stored reading"
    if prev_as_of:
        # stdout evidence only: this block is written in no mode and joins no committed table.
        sys.stdout.write(transition_text(transition(rows, as_of, prev_as_of, a.window_hours),
                                         as_of, prev_as_of, a.window_hours, derived_bound))
    consts = gate_constants()

    legs = 0
    qlog = os.path.join(a.dir, "queue.log")
    if os.path.exists(qlog):
        cut = as_of - datetime.timedelta(hours=a.window_hours)
        for line in open(qlog, encoding="utf-8", errors="replace"):
            m = re.search(r"done\s+(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}):\d{2}", line)
            if not m:
                continue
            try:
                ts = datetime.datetime.strptime(m.group(1) + m.group(2), "%Y-%m-%d%H:%M")
            except ValueError:
                continue
            if cut < ts <= as_of:
                legs += 1

    total_files = len(files)
    # The corpus-wide count is operator context, NOT window identity: it changes when a reading
    # is taken after a frozen --as-of, so it lives on stdout only and never in the committed
    # table (see the module docstring, 2026-11-15).
    md, attr_findings = build(rows, as_of, consts, day, a.window_hours, legs)

    if a.check:
        if not os.path.exists(a.check):
            print("CENSUS GAP: committed census %s is missing" % a.check)
            return 1
        old = open(a.check, encoding="utf-8").read()
        if old == md:
            print("CENSUS CHECK: matches the committed table (%d readings judged in the window; "
                  "%d preflight-*.txt files retained in the corpus at run time, corpus count is "
                  "not part of the window identity)" % (len(rows), total_files))
            if attr_findings:
                print("CENSUS FINDING (the table was produced, but a cell could not be filled "
                      "honestly — the committed table names the same files):")
                for f in attr_findings:
                    print("  - " + f)
                return 4
            return 0
        print("CENSUS DRIFT: the committed table is not what the current gate + readings produce")
        import difflib
        # Tick 166 (2026-11-15), tooling only: this print used `[:40]` SILENTLY. Measured on the real
        # corpus at the 03:08 window: the drift was 63 diff lines / 30 changed table lines, and the
        # cap hid the last 10 changed lines — EVERY engine-footprint row plus the band prose sentence.
        # The exit code stayed correct, so the only damage was evidence: a tick reading this output
        # would have attributed 20 of 30 moved cells and missed the whole footprint section. That is
        # this line's own class ("the number printed beside a verdict is not the verdict"), so the
        # total is printed BEFORE the body (a pipe to `head` still carries it), the body is printed in
        # full up to DIFF_PRINT_MAX, and a hit cap names itself instead of ending the output.
        dl = list(difflib.unified_diff(old.splitlines(), md.splitlines(),
                                       "committed", "recomputed", lineterm=""))
        n_changed = sum(1 for l in dl
                        if l[:1] in "+-" and l[:3] not in ("+++", "---"))
        print("DRIFT LINES: %d total, %d changed table lines, %d printed, %d not printed%s"
              % (len(dl), n_changed, min(len(dl), DIFF_PRINT_MAX),
                 max(0, len(dl) - DIFF_PRINT_MAX),
                 "" if len(dl) <= DIFF_PRINT_MAX else " (print cap %d hit)" % DIFF_PRINT_MAX))
        for line in dl[:DIFF_PRINT_MAX]:
            print(line)
        if len(dl) > DIFF_PRINT_MAX:
            print("(the print stopped at %d diff lines; the DRIFT LINES count above is the "
                  "whole drift)" % DIFF_PRINT_MAX)
        return 1
    if a.markdown:
        with open(a.markdown, "w", encoding="utf-8") as fh:
            fh.write(md)
        print("CENSUS WRITTEN: %s (%d readings judged in the window; %d files in the corpus at "
              "run time: %d GO / %d NO-GO / %d gap)"
              % (a.markdown, len(rows), total_files,
                 sum(1 for r in rows if r["rc"] == 0),
                 sum(1 for r in rows if r["rc"] == 3),
                 sum(1 for r in rows if r["rc"] == 1)))
        if attr_findings:
            print("CENSUS FINDING (written, but a cell could not be filled honestly; the table "
                  "names the same files):")
            for f in attr_findings:
                print("  - " + f)
            return 4
        return 0
    sys.stdout.write(md)
    if attr_findings:
        print("CENSUS FINDING (the table above names the same files):")
        for f in attr_findings:
            print("  - " + f)
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
