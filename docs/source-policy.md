# Source And Citation Policy

This repository is not presented as a scientific paper. It is a working local
AI automation system. Scientific and economics articles are still useful, and
the operator reads them. They are used as **external context, methods and
comparison points**, not as automatic proof that this repository's claims are
true.

## Where sources go

- `docs/source-policy.md` — rules and review status.
- `sources/reading-list.md` — dated source registry by topic.
- `results/evidence-review.md` — short notes when a source changes a design
  decision or a benchmark metric.
- `history/` — immutable history of past source reviews.

## Evidence levels

Every cited source is labelled:

| level | meaning | allowed use |
|---|---|---|
| `method` | provides a measurement or evaluation method | can change our metric or report structure |
| `context` | explains the wider economic or social setting | can explain motivation; cannot prove our result |
| `comparison` | gives external numbers comparable to ours | can be compared if hardware/model/task terms match |
| `warning` | documents a failure mode, bias or limitation | can change safety/evaluation rules |

A source without a level is not used in public claims.

## Citation rules

- Use DOI, arXiv ID or stable URL.
- State access date.
- State what was checked: abstract, full text or PDF.
- Do not copy long quotations into public documentation.
- Do not use a source to hide weak evidence; write the mismatch openly.

## Current topic priorities

1. Economics of local AI and global AI inference.
2. Microeconomics: cost per task, productivity, firm and household decisions.
3. Macroeconomics: AI adoption, labour productivity, GDP effects.
4. Sociology: adoption, trust, inequality, household and labour practices.
5. Hardware efficiency: memory, energy, latency, offloading, 12 GB-class GPUs.
