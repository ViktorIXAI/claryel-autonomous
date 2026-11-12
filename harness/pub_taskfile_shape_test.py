#!/usr/bin/env python3
"""Contract test for the pinned-task-file record boundary (added 2026-11-12, tick 79).

Why it exists: a zero-call publication audit on this tick read
`benchmarks/public/gpqa-diamond.tasks.jsonl` with the obvious
`pathlib.Path(...).read_text().splitlines()` and died with `Unterminated string starting at:
line 1 column 55`. ONE of the 198 GPQA prompts carries U+2028 (LINE SEPARATOR) inside its JSON
string. `str.splitlines()` splits on Unicode line boundaries, not just on `\\n`, so it cuts that
one record in half: 198 records become 199 fragments and 2 of them are unparseable. A tool that
reads a pinned task file that way does not merely crash - the `if l.strip()` idiom many of these
tools use would drop the two halves silently and publish a percent over the wrong denominator.

The shipped readers are safe: `pub_bench_run.py`, `pub_bench_score.py`, `pub_bench_compare.py`,
`pub_bench_exec.py` and `pub_bench_bfcl.py` all iterate the file object, which splits on `\\n`
only. So no published number is affected - this tick re-scored every shipped arm and all
fractions reproduced. This test pins (a) the record-boundary invariant for every pinned task
file, (b) the exact separator census that makes the GPQA file the one with the trap, and
(c) the trap itself, so nobody reintroduces the unsafe reader by "tidying" a loader.

Every invariant carries a tamper control, run against scratch copies, so the checks cannot be
vacuous. Run with no arguments; exits non-zero on the first failed invariant. Registers no
contour feature and moves no published byte.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PUB = ROOT / "benchmarks" / "public"

PASSED = 0
FAILED = []

# Measured 2026-11-12 over the pinned bytes: the GPQA prompt `gpqa-167` (quantum-mechanics
# eigenvector question, LaTeX text) carries exactly one U+2028. No other pinned set has one.
EXPECTED_SEPARATORS = {"gpqa-diamond": 1}
SEPARATORS = ("\u2028", "\u2029", "\x85")


def ok(cond, msg):
    global PASSED
    if cond:
        PASSED += 1
    else:
        FAILED.append(msg)
        print("FAIL: " + msg)


def records(path: Path):
    """The safe reader: file-object iteration splits on \\n only."""
    out = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line))
    return out


def separator_count(text: str) -> int:
    return sum(text.count(ch) for ch in SEPARATORS)


def main() -> int:
    man = json.loads((PUB / "MANIFEST.json").read_text(encoding="utf-8"))
    census_now = {}
    for bench, meta in sorted(man["benches"].items()):
        n_pin = meta.get("tasks") or 0
        if not n_pin:
            continue
        tf = PUB / ("%s.tasks.jsonl" % bench)
        if not tf.exists():
            ok(False, "%s: pinned with %d tasks but no task file on disk" % (bench, n_pin))
            continue
        raw = tf.read_bytes()
        # (1) byte-level boundary: the file is exactly `tasks` LF-terminated JSON records.
        frags = [f for f in raw.split(b"\n") if f.strip()]
        ok(len(frags) == n_pin,
           "%s: LF-delimited records %d != pinned tasks %d" % (bench, len(frags), n_pin))
        recs = records(tf)
        ok(len(recs) == n_pin,
           "%s: file-iteration records %d != pinned tasks %d" % (bench, len(recs), n_pin))
        ids = [r.get("id") for r in recs]
        ok(len(set(ids)) == len(ids) and all(ids),
           "%s: ids not unique/non-empty (%d rows)" % (bench, len(ids)))
        ok(all(json.loads(f.decode("utf-8")).get("id") for f in frags),
           "%s: a byte-level fragment carries no id" % bench)
        # (2) separator census, pinned per set
        text = tf.read_text(encoding="utf-8")
        census_now[bench] = separator_count(text)

    drift = {b: (EXPECTED_SEPARATORS.get(b, 0), census_now[b])
             for b in census_now if census_now[b] != EXPECTED_SEPARATORS.get(b, 0)}
    ok(set(census_now) == set(man["benches"]) - {b for b, m in man["benches"].items()
                                                if not (m.get("tasks") or 0)}
       and not drift,
       "separator census drifted (expected -> got): %r (a pinned task file gained or lost a "
       "Unicode line separator - re-measure the bytes before changing this pin)" % drift)

    # (3) the trap itself, on the real bytes: the unsafe reader changes the record count.
    gpqa = PUB / "gpqa-diamond.tasks.jsonl"
    text = gpqa.read_text(encoding="utf-8")
    frags = [l for l in text.splitlines() if l.strip()]
    bad = 0
    for l in frags:
        try:
            json.loads(l)
        except Exception:
            bad += 1
    ok(len(frags) == man["benches"]["gpqa-diamond"]["tasks"] + 1 and bad == 2,
       "splitlines() trap not reproduced on the GPQA bytes (fragments=%d unparseable=%d; "
       "expected 199/2) - this test exists to pin that trap" % (len(frags), bad))
    # ... while the safe reader gives the pinned count on the same file.
    ok(len(records(gpqa)) == man["benches"]["gpqa-diamond"]["tasks"],
       "safe reader disagrees with the pinned GPQA count")

    # (4) tamper controls, scratch only: the census and the boundary check are live.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "tampered.tasks.jsonl"
        tmp.write_text(text.replace("\u2028", " "), encoding="utf-8")
        ok(separator_count(tmp.read_text(encoding="utf-8")) == 0,
           "tamper control: removing the U+2028 did NOT change the census (census is vacuous)")
        # a dropped record reddens the boundary check
        keep = [f for f in gpqa.read_bytes().split(b"\n") if f.strip()][:-1]
        tmp2 = Path(td) / "short.tasks.jsonl"
        tmp2.write_bytes(b"\n".join(keep) + b"\n")
        ok(len(records(tmp2)) == 197,
           "tamper control: a truncated task file still read as %d records" % len(records(tmp2)))
        ok(separator_count(tmp2.read_text(encoding="utf-8")) == 1,
           "tamper control: separator census is position-sensitive (it must not be)")

    # (5) hash-convention pin for the file with the trap: the bytes the census describes are the
    # bytes the published rows cite (SHA-256/16, the digest convention).
    sha = hashlib.sha256(gpqa.read_bytes()).hexdigest()[:16]
    ok(sha == man["benches"]["gpqa-diamond"]["tasks_sha16"],
       "GPQA bytes sha256/16 %s disagree with the published tasks pin %s"
       % (sha, man["benches"]["gpqa-diamond"]["tasks_sha16"]))

    print("pub_taskfile_shape_test: %d checks passed, %d failed" % (PASSED, len(FAILED)))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
