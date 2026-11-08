# seed protocol (sp1) — probe67 legs and raw arms

Every leg/arm uses the published sp1 rule: `gseed = int(sha256(f"{task}|{rep}")[:8], 16) % 999983`
with reps 64/65/66. The published `plan-repNN-<side>.json` files carry the per-row gseed, so an
auditor can re-derive every seed and confirm control/candidate cells share identical seeds per
(task, rep). Plans: 77 rows; the SUBSET env var restricts execution to the six fixed task ids
without changing seeds.
