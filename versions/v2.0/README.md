# v2.0 — accepted on Mac; B2003 partial

- **Change:** `post_normalize_answer()` processes only text already produced by
  the model:
  - G: makes an existing two-value contradiction explicit without inventing values.
  - H: deterministically preserves uncertainty and numeric claims while bringing an
    already accepted answer under the 600-character format ceiling.
- **Test:** `harness/gate_v20_post_test.py` — 10/10 after the v2.0/v2.1 port.
- **Mac:** accepted on the full 2513-task subset; paired vs v1.9 n=2416,
  avg content +0.013, perfect share 72.1% → 79.8%, 185 improved / 0 regressed,
  G 0.833 → 1.000.
- **B2003:** partial. 674 rows were collected; paired vs v1.9 n=674, avg +0.0086,
  57 improved / 24 regressed. The operator stopped v2.0 at 14:46 CET to start
  v2.1 earlier; partial artifacts remain published.
- **Provenance:** agent-authored code and evaluation; the run-order stop is a
  human intervention recorded separately.
