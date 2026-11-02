# v2.2 targeted F smoke — paired evidence (2026-11-02)

Method: rerun selected v2.1 F tasks with identical `(task, rep, request_seed)`
and compare by paired key. Only the contour changed; prompts, scorer, task
bank, model and quantization were frozen.

## P2005

- n=30 F pairs
- v2.1 average content: 0.7167
- v2.2 average content: 1.0000
- improved: 29
- unchanged: 1
- regressed: 0

## Mac Studio

- n=30 F pairs
- v2.1 average content: 0.7500
- v2.2 average content: 1.0000
- improved: 30
- unchanged: 0
- regressed: 0

## P3001 budget worker

- n=30 F pairs, identical task/rep/seed on the same RTX 3060 endpoint
- v2.1 average content: 0.7167
- v2.2 average content: 1.0000
- improved: 27
- unchanged: 3
- regressed: 0
- perfect answers: 3 → 30
- Runtime: baseline 552 s, candidate 184 s.
- Every F task average became 1.0000.

## Offline B2003 replay

- Recorded v2.1 B2003 F answers were replayed through the v2.2 normalizer and
  deterministic scorer.
- n=323.
- Every F task average becomes 1.0000.
- This is a replay of already-generated answers, not a new live model run.

## Scope and limits

The acceptance is deliberately narrow: v2.2 is a targeted F contour repair. A
full Mac v2.2 suite is required before claiming whole-suite improvement. The
Mac full run starts automatically after the Mac full v2.1 run finishes.
