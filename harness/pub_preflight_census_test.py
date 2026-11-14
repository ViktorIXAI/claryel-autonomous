#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for `scripts/pub_preflight_census.py` (added 2026-11-14).

The census re-judges every stored endpoint reading with the CURRENT gate and derives the
swap-peak band plus the pre-registered arming counter. Stored readings live OUTSIDE the repo
(the producer command is untracked, like every connection seam on this line), so the census
itself cannot run in CI — THIS test runs it over synthetic readings instead, and it is the only
thing standing between the band numbers and a hand-typed table.

What it pins:

  1. the census takes the gate's RETURN CODE per file (GO / NO-GO / input gap) and the counts it
     prints are the arithmetic of those return codes, never a restatement of a tick note;
  2. the swap-peak band is computed on the **swap-mean rule**, not on the verdict column. The
     fixture set contains a reading that NO-GOs on the GPU-mean rule with a quiet swap window and
     a peak of 0.0: it must land in the PASSING group, so it cannot become the failing-group
     minimum. That is exactly the misreading a hand census makes, and the tool prints the wrong
     denominator (min peak across gate-NO-GO windows) beside the right one so the trap is named;
  3. a reading the gate refuses to judge (an input gap, e.g. a NaN engine_pcpu) is in neither band
     group even when it carries a big parseable peak: it is counted in the coverage census and in
     the excluded count, with zero band credit;
  4. a NaN peak is zero credit: the gate itself answers INPUT GAP on it, so it leaves the band,
     the coverage census marks it, and the arming counter — which counts only gate-GO windows
     carrying a PARSEABLE peak — does not move;
  5. the band is conditional, not echoed: flipping one swap counter in a GO fixture moves that
     file into the failing group and moves BOTH group extremes. (The flip also raises that file's
     peak, because the gate itself answers INPUT GAP when a window peak sits below the window mean
     — measured live on the fixture: peak 5.0 against mean 25.0 is refused as a producer bug, which
     is the right answer and is why a naive flip would test nothing.)
  6. fail-closed census gaps: a missing readings dir, a file whose name is not
     preflight-YYYYMMDD-HHMM.txt, and an --as-of bound in the wrong format all exit 1;
  7. `--check` is byte-exact against the committed table, and editing a stored reading inside the
     window makes it drift — stored readings are immutable evidence;
  8. the ceilings printed in the table are read out of the gate source at run time, so the census
     can never print a number the gate does not enforce, AND each number sits next to the scope it
     governs: the device ceiling is scope-dependent (50.0 for `blk_scope=whole-disk`, 100.0 only for
     readings carrying no scope key). Non-vacuity runs the REAL gate on one device number (60.0)
     three ways - scoped (NO-GO), unscoped (GO), unknown scope value (input gap) - which is the only
     control that separates a correct ceiling table from one that mislabels the number;
  9. the table is deterministic over a frozen `--as-of` window, and that bound really excludes
     later readings.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOL = os.path.join(ROOT, "scripts", "pub_preflight_census.py")
GATE = os.path.join(ROOT, "scripts", "pub_preflight.py")

CHECKS = 0
FAILED = []


def check(cond, label):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(label)


# A reading the current gate answers GO on (the 2026-11-14 17:51 live reading, simplified).
HEALTHY = {
    "mem_total_mib": "61953",
    "mem_available_mib": "20278",
    "swap_total_mib": "65535",
    "swap_free_mib": "57507",
    "swap_used_mib": "8028",
    "engine_state": "S",
    "engine_pcpu": "9.6",
    "engine_rss_mib": "57374",
    "gpu_util_pct": "0",
    "gpu_power_w": "27.42",
    "load1": "9.07",
    "health_code": "200",
    "foreign_legs": "0",
    "health_loaded": "true",
    "engine_serve_procs": "1",
    "swap_in_mib_per_s": "0.1",
    "swap_out_mib_per_s": "0.0",
    "swap_total_peak_mib_per_s": "5.0",
    "gpu_util_mean_pct": "0.0",
    "gpu_util_peak_pct": "0",
    "blk_read_mib_per_s": "0.1",
    "blk_top_reader": "basalt",
    "blk_scope": "whole-disk",
}

DAY = "20300101"
F1 = "preflight-%s-0001.txt" % DAY   # GO, quiet swap, parseable peak 5.0
F2 = "preflight-%s-0002.txt" % DAY   # swap-churn NO-GO, peak 300.0
F3 = "preflight-%s-0003.txt" % DAY   # GPU-contention NO-GO, swap quiet, peak 0.0  -> PASSING group
F4 = "preflight-%s-0004.txt" % DAY   # INPUT GAP (NaN engine_pcpu), peak 400.0     -> no band credit
F5 = "preflight-%s-0005.txt" % DAY   # INPUT GAP (NaN peak)                        -> n_nan

FIXTURES = {
    F1: {},
    F2: {"swap_in_mib_per_s": "120.0", "swap_out_mib_per_s": "40.0",
         "swap_total_peak_mib_per_s": "300.0"},
    F3: {"gpu_util_pct": "100", "gpu_util_mean_pct": "97.0", "gpu_util_peak_pct": "100",
         "gpu_power_w": "128.0",
         "swap_in_mib_per_s": "0.0", "swap_out_mib_per_s": "0.0",
         "swap_total_peak_mib_per_s": "0.0"},
    F4: {"engine_pcpu": "NaN", "swap_total_peak_mib_per_s": "400.0"},
    F5: {"swap_total_peak_mib_per_s": "NaN"},
}


def write_fixtures(d, fixtures=None):
    for name, over in (fixtures if fixtures is not None else FIXTURES).items():
        vals = dict(HEALTHY)
        vals.update(over)
        # an override value of None deletes the key: how the unscoped/old-scale reading is built
        vals = {k: v for k, v in vals.items() if v is not None}
        with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
            for k, v in vals.items():
                fh.write("%s=%s\n" % (k, v))


def run(args):
    p = subprocess.run([sys.executable, TOOL] + args, cwd=ROOT,
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def cell(md, label):
    m = re.search(r"^\| %s \| (.*?) \|$" % re.escape(label), md, re.M)
    return m.group(1) if m else None


def int_cell(md, label):
    v = cell(md, label)
    if v is None:
        return None
    m = re.match(r"^(-?\d+)", v.strip())
    return int(m.group(1)) if m else None


def main():
    with tempfile.TemporaryDirectory() as tmp:
        write_fixtures(tmp)
        rc, out = run(["--dir", tmp, "--as-of", "%s-0005" % DAY])
        check(rc == 0, "census over fixtures exits 0 (rc=%s: %s)" % (rc, out[:400]))

        # 1. verdict arithmetic (1 GO, 2 NO-GO, 2 input gaps)
        check(int_cell(out, "gate verdict GO") == 1,
              "GO count is 1, got %r" % cell(out, "gate verdict GO"))
        check(int_cell(out, "gate verdict NO-GO") == 2,
              "NO-GO count is 2, got %r" % cell(out, "gate verdict NO-GO"))
        check(int_cell(out, "gate verdict input gap") == 2,
              "input-gap count is 2, got %r" % cell(out, "gate verdict input gap"))

        # 2. the band is on the swap-mean rule, not on the verdict column
        check(int_cell(out, "swap-mean-passing windows with a peak") == 2,
              "the GPU-contention fixture stays in the swap-mean-PASSING group (expected 2), got %r"
              % cell(out, "swap-mean-passing windows with a peak"))
        check(int_cell(out, "swap-mean-failing windows with a peak") == 1,
              "only the swap-churn fixture fails the mean rule (expected 1), got %r"
              % cell(out, "swap-mean-failing windows with a peak"))
        check(cell(out, "highest peak inside a swap-mean-PASSING window") == "5.0 MiB/s",
              "passing-group max peak is 5.0, got %r"
              % cell(out, "highest peak inside a swap-mean-PASSING window"))
        check(cell(out, "lowest peak inside a swap-mean-FAILING window") == "300.0 MiB/s",
              "failing-group min peak is 300.0, got %r"
              % cell(out, "lowest peak inside a swap-mean-FAILING window"))
        check("lowest peak in a gate-`NO-GO` window is 0.0 MiB/s" in out,
              "the trap denominator (min peak across gate-NO-GO windows = 0.0) is printed explicitly")

        # 3+4. coverage census: carried / NaN / parseable, and the input-gap peak excluded
        check(cell(out, "readings carrying the swap-peak key") == "5 (NaN 1, parseable 4)",
              "coverage cell names carried / NaN / parseable, got %r"
              % cell(out, "readings carrying the swap-peak key"))
        bandset = cell(out, "...of those, gate-JUDGED readings with a parseable peak (the band's set)")
        check(bool(bandset) and bandset.startswith("3 (the other 1 sit in readings the gate refuses"),
              "band set is 3 and the input-gap 400.0 peak is named as excluded, got %r" % bandset)
        m = re.search(r"\| arming counter \(launchable windows carrying the peak\) \| (\d+) of (\d+) \|", out)
        check(bool(m), "arming counter cell present")
        if m:
            check(m.group(1) == "1",
                  "arming counter counts only GO windows with a PARSEABLE peak, got %s" % m.group(1))
            check(int(m.group(2)) >= 2, "arming threshold printed and non-trivial, got %s" % m.group(2))

        # 5. non-vacuity: one flipped swap counter moves the verdict AND the band
        flipped = dict(FIXTURES)
        flipped[F1] = {"swap_in_mib_per_s": "25.0", "swap_total_peak_mib_per_s": "30.0"}
        with tempfile.TemporaryDirectory() as tmp2:
            write_fixtures(tmp2, flipped)
            rc2, out2 = run(["--dir", tmp2, "--as-of", "%s-0005" % DAY])
            check(rc2 == 0, "flipped census exits 0")
            check(int_cell(out2, "gate verdict GO") == 0,
                  "the flipped fixture is NO-GO now, got %r" % cell(out2, "gate verdict GO"))
            check(cell(out2, "lowest peak inside a swap-mean-FAILING window") == "30.0 MiB/s",
                  "the failing-group minimum follows the flipped file (30.0), got %r"
                  % cell(out2, "lowest peak inside a swap-mean-FAILING window"))
            check(cell(out2, "highest peak inside a swap-mean-PASSING window") == "0.0 MiB/s",
                  "the passing-group maximum follows the flip too (0.0), got %r"
                  % cell(out2, "highest peak inside a swap-mean-PASSING window"))

        # 6. fail-closed census gaps
        rc3, _ = run(["--dir", os.path.join(tmp, "no-such-dir")])
        check(rc3 == 1, "missing readings dir exits 1, got %s" % rc3)
        with open(os.path.join(tmp, "preflight-bogus.txt"), "w", encoding="utf-8") as fh:
            fh.write("mem_total_mib=1\n")
        rc4, out4 = run(["--dir", tmp, "--as-of", "%s-0005" % DAY])
        check(rc4 == 1, "an unreadable reading name exits 1, got %s" % rc4)
        check("preflight-bogus.txt" in out4, "the name gap names the file")
        os.remove(os.path.join(tmp, "preflight-bogus.txt"))
        rc5, _ = run(["--dir", tmp, "--as-of", "not-a-stamp"])
        check(rc5 == 1, "a malformed --as-of exits 1, got %s" % rc5)

        # 7. --check is byte-exact; a stored reading edited inside the window drifts
        md_path = os.path.join(tmp, "CENSUS.md")
        rc6, _ = run(["--dir", tmp, "--as-of", "%s-0005" % DAY, "--markdown", md_path])
        check(rc6 == 0 and os.path.exists(md_path), "--markdown writes the table")
        rc7, out7 = run(["--dir", tmp, "--as-of", "%s-0005" % DAY, "--check", md_path])
        check(rc7 == 0, "--check matches a freshly written table, got %s: %s" % (rc7, out7[:200]))
        with tempfile.TemporaryDirectory() as tmp3:
            for name in FIXTURES:
                shutil.copyfile(os.path.join(tmp, name), os.path.join(tmp3, name))
            with open(os.path.join(tmp3, F2), "a", encoding="utf-8") as fh:
                # the gate keeps the LAST token per key, so this rewrites F2's whole swap window:
                # mean 160.0 -> 0.2, i.e. the file moves NO-GO -> GO and its 300.0 peak moves
                # groups. A census that only counted files (instead of re-running the gate) would
                # print the old table and call it verified.
                fh.write("swap_in_mib_per_s=0.2\nswap_out_mib_per_s=0.0\n")
            rc8, out8 = run(["--dir", tmp3, "--as-of", "%s-0005" % DAY, "--check", md_path])
            check(rc8 == 1, "editing a stored reading inside the window drifts --check, got %s" % rc8)
            check("CENSUS DRIFT" in out8, "the drift mode names itself")

        # 8. ceilings come out of the gate source, so the table cannot disagree with the rule
        gate_src = open(GATE, encoding="utf-8").read()
        for const in ("SWAP_RATE_MAX_MIB_S", "GPU_UTIL_MAX_MEAN_PCT",
                      "BLK_READ_MAX_MIB_S", "BLK_READ_MAX_MIB_S_WHOLE"):
            m = re.search(r"^%s\s*=\s*([0-9.]+)" % const, gate_src, re.M)
            check(bool(m), "the gate defines %s" % const)
            if m:
                check("`%s = %s`" % (const, m.group(1)) in out,
                      "the census prints the gate's own %s = %s" % (const, m.group(1)))
        # 8b. the DEVICE ceiling is scope-dependent, and printing the number is not enough: the
        #     first version of this table printed only the 100.0 and labelled it "whole-disk
        #     scope", which contradicted its own verdict column (the gate refused a whole-disk
        #     56.2 MiB/s reading). Each number must sit next to the scope it governs.
        flat = " ".join(out.split())
        check("BLK_READ_MAX_MIB_S_WHOLE = 50.0` applies to every reading carrying "
              "`blk_scope=whole-disk" in flat,
              "the whole-disk ceiling is printed WITH its scope")
        check("BLK_READ_MAX_MIB_S = 100.0` applies only to readings with NO scope key" in flat,
              "the old inflated-scale ceiling is printed WITH its scope")
        check("unknown scope" in flat, "an unknown scope value is named as its own class")
        with tempfile.TemporaryDirectory() as tmp2:
            rows = {
                "preflight-%s-0001.txt" % DAY: {"blk_read_mib_per_s": "60.0"},
                "preflight-%s-0002.txt" % DAY: {"blk_read_mib_per_s": "60.0",
                                                "blk_scope": None},
                "preflight-%s-0003.txt" % DAY: {"blk_read_mib_per_s": "60.0",
                                                "blk_scope": "diskstats-sum"},
            }
            write_fixtures(tmp2, rows)
            rc2a, out2a = run(["--dir", tmp2, "--as-of", "%s-0003" % DAY])
            check(rc2a == 0, "census over the scope-control fixtures exits 0 (rc=%s)" % rc2a)
            check(int_cell(out2a, "gate verdict NO-GO") == 1,
                  "the same device number 60.0 IS refused when blk_scope=whole-disk "
                  "(ceiling 50.0), got NO-GO=%r" % cell(out2a, "gate verdict NO-GO"))
            check(int_cell(out2a, "gate verdict GO") == 1,
                  "the same 60.0 passes with NO scope key (ceiling 100.0) - the two scales "
                  "give different verdicts, so one printed number cannot cover both")
            check(int_cell(out2a, "gate verdict input gap") == 1,
                  "an unrecognised blk_scope value is never judged by borrowing a ceiling")
            sc = cell(out2a, "device scope of the readings in this window") or ""
            check(sc.startswith("1 whole-disk (`50.0` ceiling) / 1 unscoped (`100.0` ceiling) "
                                "/ 1 unknown scope"),
                  "the census counts readings per device scale, got %r" % sc)

        # 9. determinism over a frozen window, and the bound really windows
        rc9, out9 = run(["--dir", tmp, "--as-of", "%s-0005" % DAY])
        rc10, out10 = run(["--dir", tmp, "--as-of", "%s-0005" % DAY])
        check(rc9 == 0 and out9 == out10, "two runs over the same window are byte-identical")
        rc11, out11 = run(["--dir", tmp, "--as-of", "%s-0004" % DAY])
        check(rc11 == 0, "an earlier --as-of bound still exits 0")
        if rc11 == 0:
            check(int_cell(out11, "gate verdict input gap") == 1,
                  "the bound excludes the 0005 reading (its NaN peak), got %r"
                  % cell(out11, "gate verdict input gap"))

    # the census must not be able to reach the endpoint by accident: no ssh, no sockets
    src = open(TOOL, encoding="utf-8").read()
    for bad in ("ssh ", "requests", "urllib", "socket."):
        check(bad not in src, "the census tool contains no %s seam" % bad)
    check("pub_preflight.py" in src, "the census drives the real gate, not a copy of its rules")

    if FAILED:
        print("PUB PREFLIGHT CENSUS TEST: %d/%d FAILED:" % (len(FAILED), CHECKS))
        for f in FAILED:
            print("  - " + f)
        return 1
    print("PUB PREFLIGHT CENSUS TEST: %d/%d checks green" % (CHECKS, CHECKS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
