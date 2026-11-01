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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def jrel(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return json.load(f)


summary = jrel("results/summary.json")
full = jrel("results/summary-full.json")
second = jrel("results/second-opinion-v18-v19-b2003.json")
tel = jrel("telemetry/runs/smoke-tel-4.join.json")

data = {
    "generated_utc": __import__("time").strftime("%FT%TZ", __import__("time").gmtime()),
    "model": "Qwen3.8-Flash-Next GGUF IQ3_S (ISTA-DASLab build), frozen",
    "harness": "contour v1.9 (released); v2.0-dev unreleased",
    "summary": summary,
    "full": full,
    "second_opinion": second,
    "telemetry_run": tel,
    "releases": {
        "contour-v1.9": "https://github.com/ViktorIXAI/strata-autonomous-harness/releases/tag/contour-v1.9",
        "data-full-2026-11-01": "https://github.com/ViktorIXAI/strata-autonomous-harness/releases/tag/data-full-2026-11-01",
    },
}

out = "window.SAH_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n"
os.makedirs(os.path.join(ROOT, "dashboard"), exist_ok=True)
open(os.path.join(ROOT, "dashboard", "data.js"), "w", encoding="utf-8").write(out)
print("dashboard/data.js", len(out), "bytes")
