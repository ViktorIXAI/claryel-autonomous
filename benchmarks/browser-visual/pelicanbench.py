#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pelican benchmark on B2003: Simon Willison's prompt, sent VERBATIM, one request,
no tools, no repair. Only markdown-fence stripping is allowed before rendering.

Prompt (8 words, unchanged since Oct 2024):
    Generate an SVG of a pelican riding a bicycle.

Everything below mirrors the balls benchmark so the two series are comparable:
same engine, same sampling, fresh context per attempt, raw response kept as-is,
metrics written per attempt. Logs are in English (per operator rule).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

OUT = sys.argv[1]
PROMPT_FILE = os.path.expanduser(os.environ.get("PEL_PROMPT_FILE", "~/visbench/pelican_prompt.txt"))
CFG = os.path.expanduser("~/Strata/strata-iq3_s-3060.json")
MAXTOK = int(os.environ.get("VIS_MAXTOK", "8192"))
TEMP = float(os.environ.get("VIS_TEMP", "0.7"))
SEED = int(os.environ.get("VIS_SEED", "12345"))
ATT = os.environ.get("VIS_ATTEMPT", "1")

os.makedirs(OUT, exist_ok=True)
cfg = json.load(open(CFG, encoding="utf-8"))
key = cfg.get("api_key") or ""
api = "http://127.0.0.1:%s/v1/chat/completions" % cfg.get("port", 8080)
model = cfg.get("model_name", "qwen")
prompt = open(PROMPT_FILE, encoding="utf-8").read()


def sh(c):
    try:
        return subprocess.run(c, capture_output=True, text=True, timeout=15).stdout.strip()
    except Exception as e:
        return "n/a (%s)" % type(e).__name__


env = {
    "benchmark": "pelican-riding-a-bicycle (Simon Willison, verbatim prompt)",
    "prompt_verbatim": prompt.strip(),
    "model": model,
    "engine_exe": cfg.get("exe"),
    "engine_args": cfg.get("args"),
    "box": "B2003",
    "gpu": sh(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"]),
    "cpu": sh(["bash", "-c", "grep -m1 'model name' /proc/cpuinfo | cut -d: -f2-"]),
    "ram_total_mib": sh(["bash", "-c", "grep MemTotal /proc/meminfo | awk '{print $2}'"]),
    "os": sh(["bash", "-c", ". /etc/os-release; echo $PRETTY_NAME; uname -mrs"]),
    "temperature": TEMP,
    "seed": SEED,
    "max_tokens": MAXTOK,
    "thinking": False,
    "fresh_context": True,
    "tools_available_to_model": False,
    "repair_allowed": False,
    "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
    "prompt_words": len(prompt.split()),
    "attempt": int(ATT),
}
json.dump(env, open(os.path.join(OUT, "model_config.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
open(os.path.join(OUT, "prompt.txt"), "w", encoding="utf-8").write(prompt)

body = {"model": model, "messages": ([{"role": "system", "content": os.environ["VIS_SYSTEM"]}] if os.environ.get("VIS_SYSTEM") else []) + [{"role": "user", "content": prompt}],
        "temperature": TEMP, "max_tokens": MAXTOK, "stream": True, "seed": SEED,
        "reasoning_effort": "none", "chat_template_kwargs": {"enable_thinking": False}}
req = urllib.request.Request(api, data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json",
                                      "Authorization": chr(66) + "earer " + key})
txt = ""
ptok = ctok = None
ttft = None
finish = err = None
t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=900) as r:
        for ln in r:
            s = ln.decode("utf-8", "ignore").strip()
            if not s.startswith("data:"):
                continue
            s = s[5:].strip()
            if s == "[DONE]":
                break
            try:
                d = json.loads(s)
            except Exception:
                continue
            u = d.get("usage") or {}
            if u.get("prompt_tokens"):
                ptok = u["prompt_tokens"]
            if u.get("completion_tokens"):
                ctok = u["completion_tokens"]
            ch = (d.get("choices") or [{}])[0]
            if ch.get("finish_reason"):
                finish = ch["finish_reason"]
            piece = (ch.get("delta") or {}).get("content")
            if piece:
                if ttft is None:
                    ttft = time.time() - t0
                txt += piece
except Exception as e:
    err = "%s: %s" % (type(e).__name__, e)
wall = time.time() - t0

open(os.path.join(OUT, "raw_response.txt"), "w", encoding="utf-8").write(txt)

# ---- extraction: fence strip or <svg>..</svg> span; nothing else is touched ----
raw = txt
fences = re.findall(r"```(?:svg|xml|html)?\s*\n(.*?)```", raw, re.S)
cands = [f for f in fences if "<svg" in f.lower()]
spans = re.findall(r"<svg\b.*?</svg\s*>", raw, re.S | re.I)
svg = None
how = None
if cands:
    svg = max(cands, key=len)
    how = "markdown_fence_stripped"
elif spans:
    svg = max(spans, key=len)
    how = "svg_span_taken"
elif "<svg" in raw.lower():
    i = raw.lower().find("<svg")
    svg = raw[i:]
    how = "svg_to_end_of_response"

page = None
doc = None
if not svg:
    fdocs = [f for f in fences if "<!doctype" in f.lower() or "<html" in f.lower()]
    if fdocs:
        doc = max(fdocs, key=len); how = "html_document_fence_stripped"
    else:
        low = raw.lower(); i = low.find("<!doctype html")
        if i < 0: i = low.find("<html")
        if i >= 0:
            doc = raw[i:]; how = "html_document_taken_to_end"
    if doc:
        open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(doc)

if svg:
    page = ("<!doctype html><html><head><meta charset=\"utf-8\">"
            "<style>html,body{margin:0;height:100%;background:#101418;"
            "display:flex;align-items:center;justify-content:center}"
            "svg{width:1200px;height:700px;max-width:96vw;max-height:96vh}</style></head>"
            "<body>" + svg + "</body></html>")
    open(os.path.join(OUT, "art.svg"), "w", encoding="utf-8").write(svg)
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page)

# ---- structural inventory of the SVG itself (no rendering, no judgement) ----
inv = {}
if svg:
    tags = re.findall(r"<([A-Za-z][A-Za-z0-9:-]*)", svg)
    for t in tags:
        inv[t] = inv.get(t, 0) + 1
    inv = dict(sorted(inv.items(), key=lambda kv: -kv[1]))
    vb = re.search(r'viewBox\s*=\s*"([^"]+)"', svg)
    inv["_viewBox"] = vb.group(1) if vb else None
    inv["_root_attrs_present"] = bool(re.search(r"\b(width|height)\b", svg[:svg.find(">")]))
    try:
        import xml.etree.ElementTree as ET
        ET.fromstring(re.sub(r"<!DOCTYPE[^>]*>", "", svg, flags=re.I))
        inv["_xml_well_formed"] = True
    except Exception as e:
        inv["_xml_well_formed"] = False
        inv["_xml_error"] = str(e)

dec_s = wall - (ttft or 0.0)
metrics = {
    "single_request": True,
    "model_tools_used": False,
    "repair_applied": False,
    "extraction": how,
    "svg_found": bool(svg),
    "svg_bytes": len(svg) if svg else 0,
    "raw_bytes": len(raw),
    "wall_s": round(wall, 1),
    "ttft_s": round(ttft, 1) if ttft else None,
    "decode_tps": round((ctok or 0) / dec_s, 1) if dec_s > 0 else None,
    "prompt_tokens": ptok,
    "output_tokens": ctok,
    "finish_reason": finish,
    "error": err,
    "svg_inventory": inv,
}
json.dump(metrics, open(os.path.join(OUT, "metrics.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(json.dumps({k: metrics[k] for k in
                  ("extraction", "svg_found", "svg_bytes", "wall_s", "output_tokens",
                   "finish_reason", "error")}, ensure_ascii=False))
