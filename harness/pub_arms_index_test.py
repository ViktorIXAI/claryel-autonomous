#!/usr/bin/env python3
"""Contract test for the public-line PIN conventions (added 2026-11-10 after the pin audit).

What it pins, and why each half is non-vacuous (a tamper control proves it):

1. `benchmarks/public/arms/README.md` is a generated index that pins BOTH hash conventions per
   file, covers every shipped artifact, keeps its GFM delimiter row, and every `.sha16` sidecar
   carries SHA-256/16 of its target. The audit that produced this test measured 161 rows with ONE
   ambiguous column (125 SHA-256/16, 36 SHA-1/16), 35 sidecars in the wrong convention, 35 files
   with no row at all, one stale line count and a table GitHub rendered as prose.
2. A digest row's tasks cell is READ from `MANIFEST.json` (`pub_bench_score.manifest_tasks_cell`),
   because the published IFEval tasks pin is SHA-1/16 while every other set's pin is SHA-256/16;
   re-hashing in whichever convention a local helper used is what made the two incomparable.

Run with no arguments; exits non-zero on the first failed invariant.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

PASSED = 0
FAILED = []


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ok(cond, label):
    global PASSED
    if cond:
        PASSED += 1
    else:
        FAILED.append(label)
        print("FAIL:", label)


def raises_exit(fn, label):
    try:
        fn()
    except SystemExit as ex:
        ok(ex.code == 2, label)
    except Exception as ex:                                  # noqa: BLE001
        FAILED.append("%s (wrong failure: %r)" % (label, ex))
    else:
        FAILED.append("%s (no failure at all)" % label)


# ---------------------------------------------------------------- live repo state
pai = load("pub_arms_index", "scripts/pub_arms_index.py")
pbs = load("pub_bench_score_for_pin_test", "scripts/pub_bench_score.py")

ok(pai.check() == [], "live arms/ index is drift-free")
tracked, on_disk = pai.tracked_files()
ok(set(tracked) == set(on_disk), "every artifact in arms/ is git-tracked")
ok(len(on_disk) >= 190, "the index covers the whole artifact directory (%d files)" % len(on_disk))

manifest = json.loads((ROOT / "benchmarks/public/MANIFEST.json").read_text(encoding="utf-8"))
for bench, entry in sorted(manifest["benches"].items()):
    if not entry.get("tasks_sha16"):
        continue
    tasks = ROOT / ("benchmarks/public/%s.tasks.jsonl" % bench)
    ok(pbs.manifest_tasks_cell(bench, tasks) == entry["tasks_sha16"],
       "tasks pin reproduces for %s" % bench)

# ---------------------------------------------------------------- tamper controls (temp tree)
with tempfile.TemporaryDirectory() as td:
    src = ROOT / "benchmarks/public/arms"
    tmp = Path(td) / "arms"
    shutil.copytree(src, tmp)
    files = sorted(f.name for f in tmp.iterdir() if f.is_file() and f.name != "README.md")
    pai.ARMS, pai.README = str(tmp), str(tmp / "README.md")
    pai.tracked_files = lambda: (sorted(files), sorted(files))
    ok(pai.check() == [], "tamper baseline: the copied tree is clean")

    # (a) one answer byte edited -> pin drift
    victim = next(f for f in files if f.endswith("-answers.jsonl"))
    data = (tmp / victim).read_bytes()
    (tmp / victim).write_bytes(data + b"\n")
    d = pai.check()
    ok(any("STALE PIN (sha256/16)" in x and victim in x for x in d)
       and any("STALE PIN (sha1/16)" in x for x in d),
       "tamper A: an edited artifact reddens both pins")
    (tmp / victim).write_bytes(data)

    # (b) a row pinned with the WRONG convention -> drift
    readme = (tmp / "README.md").read_text(encoding="utf-8")
    target = "ifeval-basalt-answers.jsonl"
    good = hashlib.sha256((tmp / target).read_bytes()).hexdigest()[:16]
    wrong = hashlib.sha1((tmp / target).read_bytes()).hexdigest()[:16]
    (tmp / "README.md").write_text(readme.replace("`%s`" % good, "`%s`" % wrong), encoding="utf-8")
    ok(any("STALE PIN (sha256/16)" in x and target in x for x in pai.check()),
       "tamper B: a SHA-1 value in the SHA-256 column reddens the index")
    (tmp / "README.md").write_text(readme, encoding="utf-8")

    # (c) a sidecar written with SHA-1 (the old writer behaviour) -> drift
    side = next(f for f in files if f.endswith(".sha16"))
    keep = (tmp / side).read_text(encoding="utf-8")
    (tmp / side).write_text(hashlib.sha1((tmp / side[: -len(".sha16")]).read_bytes()).hexdigest()[:16] + "\n",
                            encoding="utf-8")
    ok(any("SIDECAR CONVENTION" in x and side in x for x in pai.check()),
       "tamper C: a SHA-1 sidecar reddens the index")
    (tmp / side).write_text(keep, encoding="utf-8")

    # (d) a new artifact with no index row -> drift
    (tmp / "zz-unindexed-arm-answers.jsonl").write_text('{"id": "x"}\n', encoding="utf-8")
    files.append("zz-unindexed-arm-answers.jsonl")
    ok(any("NO INDEX ROW" in x and "zz-unindexed-arm-answers.jsonl" in x for x in pai.check()),
       "tamper D: an artifact without an index row reddens the index")
    (tmp / "zz-unindexed-arm-answers.jsonl").unlink()
    files.remove("zz-unindexed-arm-answers.jsonl")

    # (e) a stale line count (the LiveCodeBench stats defect) -> drift
    stats = "livecodebench-contour-matched-stats.json"
    text = (tmp / "README.md").read_text(encoding="utf-8")
    rows = [l for l in text.split("\n") if l.startswith("| %s |" % stats)]
    real = pai.pins(str(tmp / stats))[0]
    ok(len(rows) == 1 and int(rows[0].split("|")[2]) == real,
       "tamper E baseline: the stats row prints the real line count (%d)" % real)
    (tmp / "README.md").write_text(text.replace(rows[0], rows[0].replace("| %d |" % real,
                                                                       "| %d |" % (real - 1))),
                                   encoding="utf-8")
    ok(any("STALE LINE COUNT" in x and stats in x for x in pai.check()),
       "tamper E: a stale line count reddens the index")

    # (f) the delimiter row removed -> the table renders as prose, so it is a finding
    lines = (tmp / "README.md").read_text(encoding="utf-8").split("\n")
    for i, ln in enumerate(lines):
        if pai.HEADER_RE.match(ln):
            del lines[i + 1]
            break
    (tmp / "README.md").write_text("\n".join(lines), encoding="utf-8")
    ok(any("NO delimiter row" in x for x in pai.check()),
       "tamper F: a table without its delimiter row reddens the index")

# ---------------------------------------------------------------- manifest pin guards
with tempfile.TemporaryDirectory() as td:
    tasks = ROOT / "benchmarks/public/ifeval.tasks.jsonl"
    edited = Path(td) / "ifeval.tasks.jsonl"
    edited.write_bytes(tasks.read_bytes() + b'{"bench": "ifeval", "id": "extra"}\n')
    raises_exit(lambda: pbs.manifest_tasks_cell("ifeval", edited),
                "guard G: a moved task file refuses its published pin")
    m = json.loads((ROOT / "benchmarks/public/MANIFEST.json").read_text(encoding="utf-8"))
    del m["benches"]["ifeval"]["tasks_sha256_16"]
    fake = Path(td) / "MANIFEST.json"
    fake.write_text(json.dumps(m), encoding="utf-8")
    pbs.MANIFEST_PATH = str(fake)
    raises_exit(lambda: pbs.manifest_tasks_cell("ifeval", tasks),
                "guard H: an unlabelled SHA-1-era pin refuses to write a digest cell")
    pbs.MANIFEST_PATH = str(ROOT / "benchmarks/public/MANIFEST.json")
    raises_exit(lambda: pbs.manifest_tasks_cell("no-such-bench", tasks),
                "guard I: an unknown bench has no tasks cell")

# ---------------------------------------------------------------- writer convention guard
WRITERS = ["scripts/pub_bench_repair.py", "scripts/pub_bench_ifeval.py",
           "scripts/pub_bench_ifeval_v2.py"]


def sidecar_writes(src):
    """The source text of every `.sha16` sidecar write in a script."""
    lines = src.split("\n")
    return ["\n".join(lines[i:i + 2]) for i, ln in enumerate(lines) if ".sha16" in ln]


for rel in WRITERS:
    src = (ROOT / rel).read_text(encoding="utf-8")
    ws = sidecar_writes(src)
    ok(bool(ws) and all("sha1(" not in w for w in ws),
       "%s: %d sidecar writes, none of them SHA-1" % (rel, len(ws)))
    ok("manifest_tasks_cell" in src, "%s: the digest tasks cell reads the MANIFEST pin" % rel)
ok(all(("def sha256_16" in (ROOT / r).read_text(encoding="utf-8")
        or "def tasks_sha256_16" in (ROOT / r).read_text(encoding="utf-8")) for r in WRITERS),
   "every writer names its hash function in the helper name")

# ---------------------------------------------------------------- manifest pin conventions
ok(pai.audit_manifest_pins() == [], "every MANIFEST pin resolves under a named convention")
with tempfile.TemporaryDirectory() as td:
    src = json.loads((ROOT / "benchmarks/public/MANIFEST.json").read_text(encoding="utf-8"))
    # (J) a checker pin edited to a value no convention gives -> unresolvable
    m = json.loads(json.dumps(src))
    m["benches"]["livecodebench"]["checker_files"]["scripts/pub_bench_lcb.py"] = "0" * 16
    fake = Path(td) / "MANIFEST-J.json"
    fake.write_text(json.dumps(m), encoding="utf-8")
    d = pai.audit_manifest_pins(str(fake))
    ok(any("TOOL PIN UNRESOLVABLE livecodebench" in x for x in d),
       "tamper J: an edited checker pin is reported as unresolvable")

    # (K) the SHA-1/16 checker pin kept, its labelled SHA-256/16 twin deleted -> unlabelled
    m = json.loads(json.dumps(src))
    del m["benches"]["livecodebench"]["checker_files_sha256_16"]
    fake = Path(td) / "MANIFEST-K.json"
    fake.write_text(json.dumps(m), encoding="utf-8")
    d = pai.audit_manifest_pins(str(fake))
    ok(any("UNLABELLED TOOL PIN livecodebench" in x for x in d),
       "tamper K: a SHA-1 checker pin without its labelled twin reddens the audit")

    # (L) a history pin that claims the wrong commit -> the git-bytes check fires
    m = json.loads(json.dumps(src))
    m["benches"]["bfcl"]["checker_history"][0]["pinned_at_commit"] = "91f33c5"
    fake = Path(td) / "MANIFEST-L.json"
    fake.write_text(json.dumps(m), encoding="utf-8")
    d = pai.audit_manifest_pins(str(fake))
    ok(any("HISTORY PIN WRONG bfcl" in x for x in d),
       "tamper L: a history pin checked against the wrong commit reddens the audit")

print("PUB PIN CONTRACT: %d checks passed, %d failed" % (PASSED, len(FAILED)))
sys.exit(1 if FAILED else 0)
