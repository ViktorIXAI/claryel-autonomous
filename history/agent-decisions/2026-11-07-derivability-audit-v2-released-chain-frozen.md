# 2026-11-07 — derivability audit versioned: audit-v2 released, audit-v1 frozen, chain re-verified

Decision: release `scripts/bank_derivability_audit_v2.py` (`audit-v2`, bytes sha16
`ac4516f263e3e8f2`) as the current gold-derivability scanner; keep
`scripts/bank_derivability_audit.py` (`audit-v1`, `0e5e4df63718ee1d`) byte-frozen as
the sole scanner of the published census chain 39 (v6.2) -> 38 (v6.3) -> 37
(v6.4/v6.5/v6.6). Census counts from different scanner versions are never
comparable; `benchmarks/hard/DERIVABILITY-CENSUS.md` is the chain of record.

Why this was the standing job (owner directive 07.11: version every element of the
measurement stack; the queued item was named in the published v6.5/v6.6 changelogs):
audit-v1 printed a "sha-less census" — its numbers had no scanner/bank/contract
identity, and it could not see the H `ask`/`unknown` atom class that produced two
published bank defects (H-ex6-01 was found only after paid arms).

What audit-v2 changes (exactly two things, one substantive capability):
* identity: every run stamps scanner version + own module sha16 + bank sha16 +
  scorer contract version/id (`v6.2 c8c0c7dd114dfc32`), loaded module-path-pinned;
* H coverage (opt-in `PARB_AUDIT_CATS=ABKH`): mirrors the frozen contract's own
  matcher (`_token_cover`/`_stem_tok` imported from the pinned harness module, not
  re-implemented heuristics) — `h_absent` when no token stem of a gold ask/unknown
  atom is copyable from the prompt, `h_script` when only a script bridge could
  reach it. ABK behaviour is byte-equivalent to audit-v1 (test-enforced).

Verification (all green before this commit):
* `harness/audit_v2_scanner_test.py` 27 checks — synthetic direct/absent/script/
  short-literal cases pinned against `CK._token_cover` itself; ABK hit-set equality
  with audit-v1 on ALL SIX published banks; header identity fields; the published
  history — v6.1..v6.4 must carry the H-ex6-01 `h_absent` candidate, v6.5/v6.6 must
  be clean on it. Enrolled in `.github/workflows/scoring-contracts.yml` in the
  same commit (a test that is not in the CI file enrolls nothing).
* chain reproducibility: audit-v1 recomputed on every bank reproduces the published
  counts exactly (also P3 rescore-integrity evidence).

Findings that steer the queue (census = candidates, not verdicts):
* the H-ex6-01 defect class is now mechanically visible on v6.1–v6.4 and zero on
  the working v6.6 — the scanner would have caught it at build time;
* H-ex6-00/02/03/04 ask atoms are all directly nameable on the working bank: the
  remaining claims-fragment concern is a spec-vs-contract contradiction, not a
  derivability gap, so the census does NOT license a bank v6.7. The H-family
  extension stays queued behind answer-byte arm evidence (pair-243 rule).

No harness bytes moved: contour stamp stays 0.0.2.50, behavior 2.48, no
CONTOUR_FEATURES change, no pins move, no workspace rebuild needed. No arms
launched; the P2005 endpoint stays idle for the next candidate pair.
