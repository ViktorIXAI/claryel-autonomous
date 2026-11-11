# Ladder runners (context ladder + streaming control + real-text sample)

Small single-file runners used for the machine-side speed ladders
(`results/p3001-initial-benchmarks.md`, `results/p3001-rtx3050-iq3s-ladder-2026-11-11.md`,
`results/p3032-iq3s-context-ladder.md`). No secrets, no rig-only paths: the host,
model name and API-key file are command-line arguments.

| file | what it measures |
|---|---|
| `ladder_bench.py` | cold-2k/8k/16k + warm-8k×2 ladder, non-streaming; decode from `usage.completion_tokens` / wall time |
| `ladder_ttft_stream.py` | same ladder with `stream=true` + `stream_options.include_usage`, client-side first-content-delta stamp |
| `realtext_bench.py` | one real engineering request (write a token-bucket rate limiter + pytest tests), N repetitions |

```
python3 ladder_bench.py        <host:port> <model-name> <keyfile> [out.jsonl]
python3 ladder_ttft_stream.py  <host:port> <model-name> <keyfile> [out.jsonl]
python3 realtext_bench.py      <host:port> <model-name> <keyfile> [out.jsonl] [reps=3]
```

Method notes that matter when reading the published rows:

* **Cold ≠ cold cache.** The engine's prompt-cache tail/spread reuses the common
  1,024-token filler prefix; the serve log row (`= N reused + M read`) is the
  source of truth and is published next to every cold row.
* **On non-streaming rows TTFT is not in the client data.** Quote the engine's
  prompt-read accounting instead; `ladder_ttft_stream.py` exists exactly to test
  that, and it showed this serve emits the completion as a single content delta
  (client first-delta = total wall time).
* `realtext_bench.py` treats both `content` and `reasoning_content` as the reply
  and records `reply_sha256_16` so a repetition can be checked for equality.
* A `TypeError` in the runner does not invalidate the engine-side row: the serve
  log keeps its own accounting (`prompt N tokens = … , M generated in T ms,
  drafts accepted X of Y`) and that is what the results files quote.
