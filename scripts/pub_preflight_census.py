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
Exit codes: 0 census written / matches, 1 census gap (missing dir, unreadable file, gate
returned something other than GO/NO-GO/input-gap, or --check drift).
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
        rows.append(dict(ts=ts, name=os.path.basename(f), rc=rc,
                         peak=pk if (pk_present and pk_ok) else None,
                         peak_present=pk_present,
                         scope=device_scope(txt),
                         mean=(si + so) if (si is not None and so is not None) else None))
    return rows, unnamed, as_of


def band(rows, swap_max):
    """Swap-peak band over the SWAP-MEAN RULE, gate-judged files only."""
    judged = [r for r in rows if r["rc"] in (0, 3)]
    withpeak = [r for r in judged if r["peak"] is not None]
    passing = [r for r in withpeak if r["mean"] is not None and r["mean"] < swap_max]
    failing = [r for r in withpeak if r["mean"] is not None and r["mean"] >= swap_max]
    verdict_nogo_peaks = [r["peak"] for r in judged if r["rc"] == 3 and r["peak"] is not None]
    verdict_go_peaks = [r["peak"] for r in judged if r["rc"] == 0 and r["peak"] is not None]
    return dict(
        n_carried=sum(1 for r in rows if r["peak_present"]),
        n_nan=sum(1 for r in rows if r["peak_present"] and r["peak"] is None),
        n_parseable_all=sum(1 for r in rows if r["peak"] is not None),
        n_parseable=len(withpeak),
        n_no_mean=len(withpeak) - len(passing) - len(failing),
        pass_n=len(passing), fail_n=len(failing),
        pass_max=max((r["peak"] for r in passing), default=None),
        fail_min=min((r["peak"] for r in failing), default=None),
        go_max=max(verdict_go_peaks, default=None),
        nogo_min=min(verdict_nogo_peaks, default=None),
        arming=sum(1 for r in judged if r["rc"] == 0 and r["peak"] is not None),
    )


def build(rows, as_of, consts, day, window_hours, legs_started, total_files):
    go = [r for r in rows if r["rc"] == 0]
    nogo = [r for r in rows if r["rc"] == 3]
    gap = [r for r in rows if r["rc"] == 1]
    day_rows = [r for r in rows if r["ts"].strftime("%Y%m%d") == day]
    cut = as_of - datetime.timedelta(hours=window_hours)
    win_go = [r for r in go if r["ts"] > cut]
    b = band(rows, consts["SWAP_RATE_MAX_MIB_S"])
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
    L.append("Census stamp: `pub-preflight-census-v1`, gate sha16 `%s`, window `as-of %s` "
             "(%d stored readings, %d inside the window)." % (sha16(GATE), as_of.strftime("%Y-%m-%d %H:%M"),
                                                              total_files, len(rows)))
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
    L.append("| highest peak inside a swap-mean-PASSING window | %s MiB/s |" % b["pass_max"])
    L.append("| lowest peak inside a swap-mean-FAILING window | %s MiB/s |" % b["fail_min"])
    L.append("| arming counter (launchable windows carrying the peak) | %d of %d |" % (
        b["arming"], ARMING_THRESHOLD))
    L.append("")
    L.append("**The two denominators, side by side, because they are not the same set.** The band above")
    L.append("is defined on the **swap-mean rule**, not on the verdict column: the highest peak in a")
    L.append("gate-`GO` window is %s MiB/s and the lowest peak in a gate-`NO-GO` window is %s MiB/s, and"
             % (b["go_max"], b["nogo_min"]))
    L.append("the second number is the trap - a reading can be NO-GO on the device or the GPU-mean rule")
    L.append("while its swap window is quiet at 0.0, and a NaN-carrying reading is an INPUT GAP the gate")
    L.append("never judges at all (%d such readings carry the peak key). Band: nothing between" % b["n_nan"])
    L.append("%s and %s MiB/s, so a peak ceiling anywhere in that interval would refuse windows the mean"
             % (b["pass_max"], b["fail_min"]))
    L.append("rule passes. The peak stays REPORTED, not gated, until the pre-registered arming threshold")
    L.append("(%d launchable windows carrying the statistic) is met." % ARMING_THRESHOLD)
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

    rows, unnamed, as_of = census(a.dir, as_of, day, a.window_hours)
    if unnamed:
        print("CENSUS GAP: %d file(s) whose name is not preflight-YYYYMMDD-HHMM.txt: %s"
              % (len(unnamed), ", ".join(os.path.basename(f) for _, f in unnamed)))
        return 1
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
    md = build(rows, as_of, consts, day, a.window_hours, legs, total_files)

    if a.check:
        if not os.path.exists(a.check):
            print("CENSUS GAP: committed census %s is missing" % a.check)
            return 1
        old = open(a.check, encoding="utf-8").read()
        if old == md:
            print("CENSUS CHECK: matches the committed table (%d readings judged)" % len(rows))
            return 0
        print("CENSUS DRIFT: the committed table is not what the current gate + readings produce")
        import difflib
        for line in list(difflib.unified_diff(old.splitlines(), md.splitlines(),
                                              "committed", "recomputed", lineterm=""))[:40]:
            print(line)
        return 1
    if a.markdown:
        with open(a.markdown, "w", encoding="utf-8") as fh:
            fh.write(md)
        print("CENSUS WRITTEN: %s (%d readings judged: %d GO / %d NO-GO / %d gap)"
              % (a.markdown, len(rows),
                 sum(1 for r in rows if r["rc"] == 0),
                 sum(1 for r in rows if r["rc"] == 3),
                 sum(1 for r in rows if r["rc"] == 1)))
        return 0
    sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
