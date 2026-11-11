#!/usr/bin/env python3
# Real-text (non-synthetic) decode sample for a Strata serve endpoint.
# Usage: python3 realtext_bench.py <host:port> <model-name> <keyfile> [outfile] [reps]
# The prompt is a genuine engineering request (code + tests), not filler text,
# so decode runs on realistic entropy. temperature 0, 512 completion tokens.
import json, sys, time, urllib.request

HOST, MODEL, KEYFILE = sys.argv[1], sys.argv[2], sys.argv[3]
OUT = sys.argv[4] if len(sys.argv) > 4 else "realtext.jsonl"
REPS = int(sys.argv[5]) if len(sys.argv) > 5 else 3

PROMPT = (
    "Review this Python service and write a module `rate_limiter.py` that implements a "
    "token-bucket rate limiter: monotonic clock, thread-safe acquire(tokens) -> bool, "
    "configurable capacity and refill rate, and a snapshot() method reporting available "
    "tokens and next-refill time. Then write pytest tests covering: initial burst up to "
    "capacity, refill after sleep, rejection over capacity, concurrent acquires from eight "
    "threads never exceeding the budget, clock-skew immunity, and a zero-capacity edge case. "
    "Return only code, no prose.\n"
)

KEY = "Bearer " + open(KEYFILE).read().strip()

for rep in range(1, REPS + 1):
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": PROMPT}],
                       "max_tokens": 512, "temperature": 0.0}).encode()
    t0 = time.time()
    r = json.load(urllib.request.urlopen(urllib.request.Request(
        "http://%s/v1/chat/completions" % HOST, data=body,
        headers={"Authorization": KEY, "Content-Type": "application/json"}), timeout=3600))
    wall = time.time() - t0
    t = r.get("timings", {})
    usage = r["usage"]
    msg = r["choices"][0]["message"]
    text = msg.get("content") or msg.get("reasoning_content") or ""
    reasoning = bool(msg.get("reasoning_content")) and not msg.get("content")
    row = {"tag": f"realtext-{rep}", "wall_s": round(wall, 1),
           "prompt_tokens": usage["prompt_tokens"],
           "completion_tokens": usage["completion_tokens"],
           "cached": (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0),
           "prompt_tps": round(t.get("prompt_per_second", 0), 1) if t else None,
           "decode_tps": round(1000.0 / t["predicted_per_token_ms"], 1) if t.get("predicted_per_token_ms") else None,
           "reply_chars": len(text), "reply_lines": text.count("\n") + 1,
           "reasoning_only_reply": reasoning,
           "reply_sha256_16": __import__("hashlib").sha256(text.encode()).hexdigest()[:16],
           "finish": r["choices"][0].get("finish_reason")}
    with open(OUT, "a") as f:
        f.write(json.dumps(row) + "\n")
    print(json.dumps(row), flush=True)
print("REALTEXT_DONE", flush=True)
