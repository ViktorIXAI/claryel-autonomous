# Raw upstream copies behind the public task files

`benchmarks/public/<bench>.tasks.jsonl` is the pinned, sanitized scoring input (id, bench, prompt,
gold, checker, source). This directory holds the upstream copies those task files were built from,
so an outsider can re-derive the pin instead of trusting it.

| file | lines | sha16 | upstream |
|---|---|---|---|
| `HumanEval.jsonl.gz` | 180 | `b796127e635a67f9` | openai-humaneval (upstream-cased copy of the same bytes) |
| `arc-challenge.jsonl` | 1172 | `03227c30fd557ad1` | https://huggingface.co/datasets/allenai/ARC-Challenge (test split) |
| `arc-easy.jsonl` | 2376 | `874354cf37266753` | https://huggingface.co/datasets/allenai/ARC-Easy (test split) |
| `gpqa-diamond.jsonl` | 198 | `71991ea576f83033` | https://huggingface.co/datasets/Idavidrein/gpqa (gpqa_diamond, mirror; one prompt carries a literal U+2028 inside its JSON string — legal, and it is why the JSONL validator splits on "\n" only) |
| `gsm8k-test.jsonl` | 1319 | `3730d312f6e34405` | https://github.com/openai/grade-school-math (test.jsonl) |
| `humaneval.jsonl.gz` | 180 | `b796127e635a67f9` | openai-humaneval (OpenAI split) |

Removed 2026-11-08: `arceasy-test.jsonl`, `ifeval-input.jsonl` and `x.bin` — each 14 bytes whose
entire content is `404: Not Found`, i.e. three fetches that failed and were committed anyway. They
were referenced by no task file, no arm and no doc; their sha256 before removal:

```
ifeval-input.jsonl   d5558cd419c8d46b  (14 bytes, '404: Not Found')
arceasy-test.jsonl   d5558cd419c8d46b  (identical content)
x.bin                d5558cd419c8d46b  (identical content)
```

The JSON-schema QA job flagged them as invalid JSONL; that flag is what surfaced the deletion
decision, and the gate is green without them.
