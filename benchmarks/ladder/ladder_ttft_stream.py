#!/usr/bin/env python3
# Supplemental ladder pass with client-side TTFT (first streamed delta) recorded.
# Usage: python3 ladder_ttft.py <host:port> <model-name> <keyfile> [outfile]
# Same prompt construction as skills/strata-older-cpu-build/scripts/ladder_bench.py,
# but stream=true so time-to-first-token is measured at the client, not derived.
import json, sys, time, urllib.request

HOST, MODEL, KEYFILE = sys.argv[1], sys.argv[2], sys.argv[3]
OUT = sys.argv[4] if len(sys.argv) > 4 else "ladder-ttft.jsonl"
KEY = "Bearer " + open(KEYFILE).read().strip()


def filler(words, nonce):
    unit = ("the quick brown fox jumps over the lazy dog while sensors record "
            "clocks temperatures and throughput numbers for the benchmark ledger ")
    words = words + (nonce % 7)
    return " ".join((unit * (words // 17 + 1)).split()[:words])


def ask(words, tag, nonce):
    prompt = filler(words, nonce) + "\nQuestion: reply with a two-sentence summary of what this text is."
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": 128, "temperature": 0.0,
                       "stream": True, "stream_options": {"include_usage": True}}).encode()
    t0 = time.time()
    resp = urllib.request.urlopen(urllib.request.Request(
        "http://%s/v1/chat/completions" % HOST, data=body,
        headers={"Authorization": KEY, "Content-Type": "application/json"}), timeout=3600)
    ttft = None
    usage = {}
    timings = {}
    gen_tokens = 0
    for raw in resp:
        line = raw.decode("utf-8", "replace").strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            break
        try:
            ev = json.loads(payload)
        except Exception:
            continue
        if ev.get("usage"):
            usage = ev["usage"]
        if ev.get("timings"):
            timings = ev["timings"]
        for ch in ev.get("choices", []):
            delta = (ch.get("delta") or {}).get("content")
            if delta and ttft is None:
                ttft = time.time() - t0
            if delta:
                gen_tokens += 1
    wall = time.time() - t0
    pt = usage.get("prompt_tokens")
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
    ct = usage.get("completion_tokens")
    decode_tps = round(1000.0 / timings["predicted_per_token_ms"], 1) if timings.get("predicted_per_token_ms") else None
    row = {"tag": tag, "ttft_s": round(ttft, 3) if ttft else None,
           "wall_s": round(wall, 1),
           "prompt_tokens": pt, "completion_tokens": ct, "cached": cached,
           "decode_tps": decode_tps,
           "prefill_ms_engine": round(pt * timings["ms_per_prompt_token"]) if timings.get("ms_per_prompt_token") and pt else None,
           "gen_deltas_counted": gen_tokens}
    if cached and pt and cached > 0.5 * pt:
        row["note"] = "cached>50pct of prompt"
    with open(OUT, "a") as f:
        f.write(json.dumps(row) + "\n")
    print(json.dumps(row), flush=True)


if __name__ == "__main__":
    ask(1500, "ttft-cold-2k", 11)
    ask(6100, "ttft-cold-8k", 12)
    ask(12200, "ttft-cold-16k", 13)
    ask(6100, "ttft-warm-8k-a", 12)
    ask(6100, "ttft-warm-8k-b", 12)
    print("TTFT_LADDER_DONE", flush=True)
