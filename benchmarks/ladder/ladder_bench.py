#!/usr/bin/env python3
# Cold/warm benchmark ladder for any Strata serve endpoint.
# Usage: python3 ladder_bench.py <host:port> <model-name> <keyfile> [outfile]
# Rows: cold 2k/8k/16k-token prompts (fresh conversation each), warm 8k x2.
# Engine prompt_tps is meaningless on warm rows (99.9% cached) — use wall_s+decode.
import json, sys, time, urllib.request

HOST, MODEL, KEYFILE = sys.argv[1], sys.argv[2], sys.argv[3]
OUT = sys.argv[4] if len(sys.argv) > 4 else "ladder.jsonl"
KEY = "Bearer " + open(KEYFILE).read().strip()

def wait_loaded(timeout_s=2400):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(
                "http://%s/v1/models" % HOST, headers={"Authorization": KEY})))
            if r["data"][0]["status"]["value"] == "loaded":
                return True
        except Exception:
            pass
        time.sleep(10)
    return False

def filler(words):
    unit = ("the quick brown fox jumps over the lazy dog while sensors record "
            "clocks temperatures and throughput numbers for the benchmark ledger ")
    return " ".join((unit * (words // 17 + 1)).split()[:words])

def ask(words, tag):
    prompt = filler(words) + "\nQuestion: reply with a two-sentence summary of what this text is."
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": 128, "temperature": 0.0}).encode()
    t0 = time.time()
    r = json.load(urllib.request.urlopen(urllib.request.Request(
        "http://%s/v1/chat/completions" % HOST, data=body,
        headers={"Authorization": KEY, "Content-Type": "application/json"}), timeout=3600))
    t = r.get("timings", {})
    cached = r["usage"]["prompt_tokens_details"].get("cached_tokens", 0)
    row = {"tag": tag, "wall_s": round(time.time() - t0, 1),
           "prompt_tokens": r["usage"]["prompt_tokens"],
           "completion_tokens": r["usage"]["completion_tokens"],
           "prompt_tps": round(t.get("prompt_per_second", 0), 1),
           "decode_tps": round(1000 / t["predicted_per_token_ms"], 1) if t.get("predicted_per_token_ms") else None,
           "cached": cached}
    if cached > 0.5 * row["prompt_tokens"]:
        row["prompt_tps_note"] = "cached>50pct; ratio meaningless"
    with open(OUT, "a") as f:
        f.write(json.dumps(row) + "\n")
    print(json.dumps(row), flush=True)

if __name__ == "__main__":
    if not wait_loaded():
        sys.exit("MODEL_NOT_LOADED")
    print("loaded, starting ladder", flush=True)
    ask(1500, "cold-2k"); ask(6100, "cold-8k"); ask(12200, "cold-16k")
    ask(6100, "warm-8k-a"); ask(6100, "warm-8k-b")
    print("LADDER_DONE", flush=True)
