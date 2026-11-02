# v2.2 — F diagnostic grounding (targeted acceptance)

- **Change:** `f_diagnostic_normalize()` for F-category answers. It reads the
  visible log, detects OOM/disk-full/NVME/AppArmor classes, preserves the
  model's claim, and appends canonical component/cause/safe-step tokens only
  when visible evidence supports them. It also suppresses unsupported thermal
  claims and decoy blame in the cause/component lines.
- **Guardrail:** no task prompt or scorer change, no invented facts, no
  destructive commands, and no rewriting of an already complete answer's safe
  steps.
- **Test:** `harness/gate_v22_f_test.py` — 8/8.
- **Targeted evidence:** P2005 paired F smoke n=30: 0.7167 → 1.0000; 29
  improved / 1 unchanged / 0 regressed. Mac Studio paired F smoke n=30:
  0.7500 → 1.0000; 30 improved / 0 regressed.
- **Offline replay:** all recorded B2003 v2.1 F answers n=323 become perfect
  after v2.2 normalization.
- **Running status:** full Mac v2.2 suite starts after full Mac v2.1 finishes;
  no full-suite claim until it completes.
