# Independent validation — how to distrust us properly

Everything published here is recomputable without trusting a single table
in a README.

## Step 1 — verify the raw record
Download `artifacts-release-2026-11-01.tar.zst` from GitHub Releases, unpack:

```bash
tar --zstd -xf artifacts-release-2026-11-01.tar.zst
mv release-2026-11-01 artifacts
```

Check every file against `logs/INDEX.md` (SHA-256 first-16 column):

```bash
(cd artifacts && sha256sum $(find . -name '*.jsonl' | sort)) | head
```

## Step 2 — recompute the published aggregates

```bash
PARB_ARTIFACTS=./artifacts python3 analytics/aggregate.py > /tmp/summary.json
diff <(python3 -m json.tool results/summary.json) <(python3 -m json.tool /tmp/summary.json)
```

`results/summary.json` in this repo was produced by exactly that command on
exactly those bytes (verified byte-identical at publication time). It
contains: per-version n / avg content / perfect / format / category means /
ledger economics / top events; all paired deltas with improved:regressed
counts; and the D-ea subset that drove v1.9.

## Step 3 — audit the yardstick itself
Scorers are code + data references, not vibes:
`harness/parb_check.py` (current), `versions/v1.2/parb_check.py.v12orig`
(the v1.2-era scorer original) — diff them to see whether any grading rule
moved. All published version deltas start at v1.2 so the scorer you audit is
the scorer that produced the numbers. Task refs are in
`benchmarks/text-gates/bank.json`; regenerate the whole bank yourself with
`harness/parb_bank.py` (`bank_seed=20261031`) and diff.

## Known limits of this validation story (stated, not hidden)
- Same scorer across compared versions is a *strength* (fixed yardstick) but
  means a systematic scorer bias survives our checks — a second-opinion
  independent validator is roadmap stage 7b.
- Dedup rule `(task, rep)`-best is ours; recompute with "last-wins" or
  "first-wins" and the means shift slightly — the paired counts are robust,
  means are not, and we only lean on paired counts for verdicts.
- Raw agent transcripts are not published (privacy), so *code authorship*
  provenance is log-level, not transcript-level (`docs/limitations.md`).
