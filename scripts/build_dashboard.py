#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build dashboard/data.js from published machine-readable artifacts only.

Every number rendered by dashboard/index.html comes from files in this repo
(results/summary.json, results/summary-full.json, telemetry joins) — the
dashboard never contains hand-written figures. Re-run after each pipeline
publish:  python3 scripts/build_dashboard.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _rem():
    import subprocess
    u = subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT,
                       capture_output=True, text=True).stdout.strip()
    m = re.search(r"github\.com[:/]([^/]+/[^/.]+)", u)
    return "https://github.com/" + (m.group(1) if m else "ViktorIXAI/claryel-autonomous")


def jrel(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return json.load(f)


summary = jrel("results/summary.json")
full = jrel("results/summary-full.json")
second = jrel("results/second-opinion-v18-v19-b2003.json")
second2 = jrel("results/independent-scorer-v2.json")
baselines = jrel("results/baselines.json")
tel = jrel("telemetry/runs/smoke-tel-4.join.json")

# holdout pilot category stats (computed from the published sample rows)
from collections import defaultdict
def _holdout(dirname, fname):
    _h = defaultdict(list)
    for line in open(os.path.join(ROOT, "logs", "samples", dirname, fname),
                     encoding="utf-8"):
        r = json.loads(line)
        _h[r["task"][0]].append(float(r.get("content") or 0))
    return {c: {"n": len(v), "mean": round(sum(v) / len(v), 3)} for c, v in sorted(_h.items())}


holdout = _holdout("holdout-p2005-mini2", "results-holdout-mini2.jsonl")
holdout_v1_broken_g = _holdout("holdout-p2005-mini", "results-holdout-mini.jsonl")

data = {
    "generated_utc": __import__("time").strftime("%FT%TZ", __import__("time").gmtime()),
    "model": "Qwen3.8-Flash-Next GGUF IQ3_S (ISTA-DASLab build), frozen",
    "harness": "contour v1.9 (released); v2.0-dev unreleased",
    "summary": summary,
    "full": full,
    "second_opinion": second,
    "second_opinion_v2": second2,
    "baselines": baselines,
    "telemetry_run": tel,
    "holdout_mini": holdout,
    "holdout_mini_v1_broken_g": holdout_v1_broken_g,
    "releases": {
        "contour-v1.9": _rem() + "/releases/tag/contour-v1.9",
        "external review + our response": _rem() + "/blob/main/results/external-review-2026-11-01.md",
        "data-full-2026-11-01": _rem() + "/releases/tag/data-full-2026-11-01",
    },
}

out = "window.SAH_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n"
os.makedirs(os.path.join(ROOT, "dashboard"), exist_ok=True)
open(os.path.join(ROOT, "dashboard", "data.js"), "w", encoding="utf-8").write(out)
print("dashboard/data.js", len(out), "bytes")
