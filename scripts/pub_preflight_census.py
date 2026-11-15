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
returned something other than GO/NO-GO/input-gap, --check drift, or a malformed /
not-earlier --prev-as-of).
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


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def gate_constants():
    """Read the ceilings out of the gate source so the census can never disagree with it."""
    src = open(GATE, encoding="utf-8").read()
    out = {}
    for key in ("SWAP_RATE_MAX_MIB_S", "GPU_UTIL_MAX_MEAN_PCT",
                "BLK_READ_MAX_MIB_S", "BLK_READ_MAX_MIB_S_WHOLE"):
        m = re.search(r"^%s\s*=\s*([0-9.]+)" % key, src, re.M)
        if not m:
            raise SystemExit("CENSUS GAP: gate source has no %s constant" % key)
        out[key] = float(m.group(1))
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
    return subprocess.run([sys.executable, GATE, path], cwd=ROOT,
                          capture_output=True, text=True).returncode


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
        rc = run_gate(f)
        if rc not in (0, 1, 3):
            raise SystemExit("CENSUS GAP: gate returned %s on %s" % (rc, os.path.basename(f)))
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
        rows.append(dict(ts=ts, name=os.path.basename(f), rc=rc,
                         peak=pk if (pk_present and pk_ok) else None,
                         peak_present=pk_present,
                         vmswap=vw if (vw_present and vw_ok) else None,
                         vmswap_present=vw_present,
                         cached=sc if (sc_present and sc_ok) else None,
                         used=used,
                         scope=device_scope(txt),
                         mean=(si + so) if (si is not None and so is not None) else None))
    return rows, unnamed, as_of


RC_WORD = {0: "GO", 3: "NO-GO", 1: "input gap"}


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
        n_go=len(go), go_min=(min(go) if go else None), go_max=lo,
        n_swap_ref=len(swap_ref), ref_min=hi,
        ref_max=(max(swap_ref) if swap_ref else None),
        ref_median=median(swap_ref),
        n_other_ref=len(other_ref), other_ref=other_ref,
        inside=inside,
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
        "| day dead zone, highest GO draw to lowest swap-rule refusal | %s-%s x — %s |" % (
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


def build(rows, as_of, consts, day, window_hours, legs_started):
    go = [r for r in rows if r["rc"] == 0]
    nogo = [r for r in rows if r["rc"] == 3]
    gap = [r for r in rows if r["rc"] == 1]
    day_rows = [r for r in rows if r["ts"].strftime("%Y%m%d") == day]
    cut = as_of - datetime.timedelta(hours=window_hours)
    win_go = [r for r in go if r["ts"] > cut]
    b = band(rows, consts["SWAP_RATE_MAX_MIB_S"])
    fp = footprint(rows)
    db = day_band(day_rows, consts["SWAP_RATE_MAX_MIB_S"])
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
    L.append("Census stamp: `pub-preflight-census-v5`, gate sha16 `%s`, window `as-of %s` "
             "(%d readings inside the window). v5 adds the DAY rule-band table (8 computed cells: "
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
             "table went on asserting an empty interval the data had withdrawn. v1, v2, v3, v4 and "
             "v5 tables are left as published; a v1, v2, v3, v4 and v5 file are not the same table "
             "shape."
             % (sha16(GATE), as_of.strftime("%Y-%m-%d %H:%M"), len(rows)))
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
    return "\n".join(L) + "\n"


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
    md = build(rows, as_of, consts, day, a.window_hours, legs)

    if a.check:
        if not os.path.exists(a.check):
            print("CENSUS GAP: committed census %s is missing" % a.check)
            return 1
        old = open(a.check, encoding="utf-8").read()
        if old == md:
            print("CENSUS CHECK: matches the committed table (%d readings judged in the window; "
                  "%d preflight-*.txt files retained in the corpus at run time, corpus count is "
                  "not part of the window identity)" % (len(rows), total_files))
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
        return 0
    sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
