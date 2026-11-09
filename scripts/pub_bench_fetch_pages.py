#!/usr/bin/env python3
"""Resumable paged fetch of a pinned public-benchmark split.

The shared pub_bench_prep.hf_rows buffers every page in memory and writes the file at the end,
so a killed attempt loses all progress and a 12k-row split does not fit inside a tool timeout.
This driver appends each page to `<key>.jsonl.partial` under benchmarks/public/raw/ and resumes
from the row count already on disk, so a big split can be pulled across as many attempts as the
hub's 5xx rate needs. The partial file is only renamed to its final pinned name when the row
count reaches the expected total, so a partial pull can never be mistaken for the pinned raw
cache. Usage: pub_bench_fetch_pages.py <split-key> (keys in DEFAULTS; prints the raw sha16 that
MANIFEST.json pins).
"""
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request

HF = "https://datasets-server.huggingface.co/rows"
REPO_RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                        "benchmarks", "public", "raw")


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
DEFAULTS = {
    "mmlu-pro-test": ("TIGER-Lab/MMLU-Pro", "default", "test", 12032),
}


def count(path):
    if not os.path.exists(path):
        return 0
    with open(path, "rb") as fh:
        return sum(1 for _ in fh)


def page(off, dataset, config, split):
    u = "%s?dataset=%s&config=%s&split=%s&offset=%d&limit=100" % (
        HF, urllib.parse.quote(dataset), config, split, off)
    last = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(u, timeout=120) as r:
                return json.load(r)
        except Exception as exc:                              # noqa: BLE001
            last = exc
            time.sleep(6 * (attempt + 1))
    raise RuntimeError("page offset %d: %s" % (off, str(last)[:160]))


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else "mmlu-pro-test"
    if key not in DEFAULTS:
        raise SystemExit("unknown split key %r; add it to DEFAULTS" % key)
    dataset, config, split, total = DEFAULTS[key]
    dst = os.path.join(REPO_RAW, key + ".jsonl")
    PART = dst + ".partial"
    n = count(PART)
    print("resuming at %d rows" % n, flush=True)
    while n < total:
        data = page(n, dataset, config, split)
        rows = data.get("rows") or []
        if not rows:
            raise RuntimeError("empty page at offset %d" % n)
        with open(PART, "a", encoding="utf-8") as fh:
            for x in rows:
                row = x.get("row", x) if isinstance(x, dict) else x
                if not isinstance(row, dict) or not row.get("question"):
                    raise RuntimeError("unexpected row shape at offset %d" % n)
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        n += len(rows)
        if n % 2000 < 100:
            print("  %d/%d rows" % (n, total), flush=True)
        time.sleep(0.6)
    os.replace(PART, dst)
    print("DONE rows=%d sha16=%s" % (count(dst), sha16(dst)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
