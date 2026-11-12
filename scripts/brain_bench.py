#!/usr/bin/env python3
"""Baseline/after benchmark for the fleet brains: decode tok/s and TTFT over SSE."""
import json, os, re, subprocess, sys, time, urllib.request

def key_for(base_url, cfg_path=os.path.expanduser("~/.hermes/config.yaml")):
    if os.environ.get("BRAIN_KEY"):
        return os.environ["BRAIN_KEY"]
    try:
        txt = open(cfg_path).read()
    except OSError:
        return os.environ.get("STRATA_API_KEY", "")
    m = re.search(r"base_url:\s*%s[\s\S]{0,400}?api_key:\s*['\"]?([^\s'\"]+)" % re.escape(base_url), txt)
    if m:
        return m.group(1)
    m = re.search(r"api_key:\s*['\"]?([^\s'\"]+)", txt)
    return m.group(1) if m else os.environ.get("STRATA_API_KEY", "")

def bench(base_url, prompt_tokens=600, gen_tokens=256, runs=2, model=None, timeout=240):
    prompt = ("Explain briefly how a data center cools its racks. " * (prompt_tokens // 8)) or "Hello."
    key = key_for(base_url)
    out = []
    for r in range(runs):
        body = json.dumps({"model": model or "default",
                           "messages": [{"role": "user", "content": prompt}],
                           "max_tokens": gen_tokens, "temperature": 0,
                           "seed": 424242, "stream": True}).encode()
        req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions", data=body,
                                     headers={"Content-Type": "application/json",
                                              "Authorization": "***" + key,
                                              "X-API-Key": key})
        t0 = time.time(); ttft = None; tok = 0; n = 0
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                for raw in resp:
                    line = raw.decode("utf-8", "replace").strip()
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        d = json.loads(payload)
                    except Exception:
                        continue
                    ch = (d.get("choices") or [{}])[0]
                    piece = ch.get("text") or (ch.get("delta") or {}).get("content") or \
                        (ch.get("message") or {}).get("content") or ""
                    if piece:
                        if ttft is None:
                            ttft = time.time() - t0
                        n += 1
                        tok += len(piece)
        except Exception as exc:
            out.append({"run": r, "error": str(exc)[:120]}); continue
        el = time.time() - t0
        out.append({"run": r, "ttft_s": round(ttft, 2) if ttft else None,
                    "sse_chunks": n, "chars": tok,
                    "chunk_rate": round((n - 1) / (el - (ttft or 0)), 1) if n > 1 and el > (ttft or 0) else None,
                    "wall_s": round(el, 1)})
    return out

if __name__ == "__main__":
    url = sys.argv[1]
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    model = sys.argv[3] if len(sys.argv) > 3 else None
    ptok = int(sys.argv[4]) if len(sys.argv) > 4 else 600
    print(json.dumps({"url": url, "prompt_tokens": ptok,
                      "runs": bench(url, runs=runs, model=model, prompt_tokens=ptok)}, indent=1))
