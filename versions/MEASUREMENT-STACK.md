# Measurement stack: what every number in this repo was produced under

Regenerate: `python3 scripts/measurement_stack.py`. Every table in this repo must
name the bank sha16 and the scorer contract version next to its numbers; this file is
where those identities are defined, so a quoted number can be traced to bytes.

## 1. The versioned elements

| element | version | identity (sha16) | pinned by |
|---|---|---|---|
| dev bank (hard) | v6.1 | 9ec86dfca4a6f85f | `benchmarks/hard/MANIFEST.v6.sha256`, `bank-defect-v62-changelog.md` |
| dev bank (hard) | v6.2 | 3c866ea7daae611c | `scripts/verify_bank_v62.py` (fails if v6.1 moves) |
| dev bank (hard) | v6.3 | 73f7a04d57473545 | `scripts/verify_bank_v63.py` (one field vs v6.2; PROVISIONAL) |
| dev bank (hard) | **v6.4** | 85a0cd0dd6fa1fab | `scripts/verify_bank_v64.py` (one field vs v6.3; WORKING hard bank) |
| bank version identity | registry `bank-versions-v1` | names -> version + published sha16 | `benchmarks/hard/BANK-VERSIONS.json` (build-time immutability guard, release 0.0.2.49); the builder stamps `bank-version.json` per workspace, run records write `stack.bank_version` + `bank_version_source` |
| run workspace bank copy | bank v6.2 probe-workspace copy | d1e8d11df5840dcc | run record `stack.bank_sha16` |
| run workspace bank copy | bank v6.3 probe-workspace copy | 42bf2ecf69558dc2 | run record `stack.bank_sha16` |
| run workspace bank copy | bank v6.4 probe-workspace copy (WORKING) | 7788cc288922b9a4 | run record `stack.bank_sha16` |
| run workspace bank copy | generated run-workspace copy (v6.1 content) | f4553aab304f60d7 | run record `stack.bank_sha16` |
| scorer contract | **v6.1** | 91c09e8ca16b8841; modules: e_sandbox.py 424c04126e9b6c1e, parb_check_v6.py 89437d8cfe1fc6c8, parb_loop.py f5f5b78ab46a0f0c | `harness/gate_scorer_contract.py` + `MANIFEST.v6.sha256` |
| scorer contract | **v6.2** | c8c0c7dd114dfc32; modules: e_sandbox.py 424c04126e9b6c1e, parb_check_v6.py 89437d8cfe1fc6c8, parb_loop.py f5f5b78ab46a0f0c | `harness/gate_scorer_contract.py` + `MANIFEST.v6.sha256` |
| strict rule | (part of every contract) | `content == 1.0 and format_ok` | `gate_scorer_contract.STRICT_RULE` |
| seed protocol | sp1 | per-(task,rep) gseed + per-task plan seed | `scripts/plan_reps.py`, `build_hard_v6_ws.py` |
| typed failure codes | registry in contract v6.2 | content / protocol / integrity / marker / infra | `gate_scorer_contract.CODE_CLASS`, gate_v59 tests |
| two published axes | contract v6.2 | answer axis + protocol axis, additive to `strict` | `gate_v59_scorer_contract_v62_test.py` |
| gold audit (derivability) | audit-v1 (frozen) | sha16 0e5e4df63718ee1d; ABK chain 39->38->37 recomputes exactly | `harness/audit_v2_scanner_test.py` ABK-equivalence, `benchmarks/hard/DERIVABILITY-CENSUS.md` |
| gold audit (derivability) | **audit-v2** | sha16 ac4516f263e3e8f2; adds H ask-atom coverage mirroring the contract's own `_token_cover`/`_stem_tok` | `harness/audit_v2_scanner_test.py`, `benchmarks/hard/DERIVABILITY-CENSUS.md` |
| harness | commit 7f630d408e99 | contour stamp 2.51 (behavior 2.51) | git + `gate_versioning.py` |

Scorer contract v6.2 delegates to the v6.1 bytes, so it changes no score; the equality
is asserted cell by cell on published answers (`gate_v59_scorer_contract_v62_test.py`),
and `verify_contract()` fails closed if a frozen scoring byte moves without a new version.

## 2. Contour axes

- stamped revision now: **2.51** (`0.0.2.51`); contour behavior reported: **2.51**;
- did this release change the contour? **True** (a tooling release registers no feature)
- adopted line features: 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.7, 2.9, 2.10, 2.11, 2.12, 2.13, 2.14, 2.15, 2.16, 2.17, 2.18, 2.19, 2.20, 2.21, 2.22, 2.23, 2.24, 2.25, 2.26, 2.27, 2.28, 2.29, 2.35, 2.37, 2.39, 2.40, 2.43, 2.47, 2.48, 2.51
- frozen to their own stamp (never inherited): 2.30 (contract guarantee (shape re-ask/salvage) — MEASURED NEGATIVE), 2.31 (self-consistency vote — MEASURED NEGATIVE), 2.32 (J ranking repair v1 — on target, under the noise floor), 2.33 (A threshold-table arithmetic — zero live fires), 2.34 (B field completeness — zero live fires), 2.36 (group-4 lottery selection — MEASURED NEGATIVE), 2.38 (A threshold-table re-land — UNMEASURED), 2.41 (C rule-grounded membership — UNMEASURED), 2.42 (D-loop policy re-ground — MEASURED NEGATIVE), 2.44 (D-loop best-of-2 on false_completion_claim — UNMEASURED)
- reserved tooling band (behavior pinned forever): 2.3, 2.4, 2.5, 2.6, 2.8

the ADOPTED feature matrix of 0.0.2.45 equals 0.0.2.43; the behavior axis reports the newest REGISTERED stamp (2.44), whose own flag is frozen OFF — name BOTH axes in every table

## 3. Per-artifact stack

`stack` = the block written into `run-record-*.json` from release 0.0.2.45 onward.
Earlier directories are attributed by construction: their rows carry
`contour_version`/`contour_behavior`, and the only bank/contract bytes that could have
produced them are the pinned ones named below.

| directory | arms | rows | contour stamp / behavior | bank | scorer | stack in record |
|---|---|---|---|---|---|---|
| `bank-probe-634` | 9 | 9 | 0.0.2.48 / 2.48 | recorded | recorded | yes |
| `bank-probe-65` | 12 | 12 | 0.0.2.50 / 2.48 | recorded | recorded | yes |
| `bank-probe-66` | 3 | 3 | 0.0.2.50 / 2.48 | recorded | recorded | yes |
| `cadence-240` | 3 | 231 | 0.0.2.40 / 2.40 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `cadence-246` | 3 | 231 | 0.0.2.45 / 2.44 | recorded | recorded | yes |
| `cadence-249` | 3 | 231 | 0.0.2.49 / 2.48 | recorded | recorded | yes |
| `four-arm-v61` | 1 | 77 | 0.0.2.28 / 2.28 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `full-216` | 1 | 77 | 0.0.2.16 / 2.16 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `full-217` | 1 | 77 | 0.0.2.17 / 2.17 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `full-218` | 1 | 77 | 0.0.2.18 / 2.18 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `full-219` | 1 | 77 | 0.0.2.19 / 2.19 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `full-220` | 1 | 77 | 0.0.2.20 / 2.20 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `full-221` | 1 | 77 | 0.0.2.21 / 2.21 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `full-222` | 1 | 77 | 0.0.2.22 / 2.22 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `full-223` | 1 | 77 | 0.0.2.23 / 2.23 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `full-225` | 1 | 77 | 0.0.2.25 / 2.25 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `full-228` | 1 | 77 | 0.0.2.28 / 2.28 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `full-229` | 1 | 77 | 0.0.2.29 / 2.28 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `j-probe-218` | 1 | 12 | 0.0.2.18 / 2.18 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `k-218` | 2 | 8 | 0.0.2.17 + 0.0.2.18 / 2.17 + 2.18 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `loopd-216` | 1 | 12 | 0.0.2.15 + 0.0.2.16 / 2.15 + 2.16 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `pair-230` | 6 | 462 | 0.0.2.29 + 0.0.2.30 / 2.28 + 2.30 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `pair-231` | 6 | 462 | 0.0.2.29 + 0.0.2.31 / 2.29 + 2.31 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `pair-232` | 6 | 462 | 0.0.2.29 + 0.0.2.32 / 2.29 + 2.32 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `pair-233` | 6 | 462 | 0.0.2.29 + 0.0.2.33 / 2.29 + 2.33 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `pair-234` | 6 | 462 | 0.0.2.29 + 0.0.2.34 / 2.29 + 2.34 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `pair-235` | 6 | 462 | 0.0.2.29 + 0.0.2.35 / 2.29 + 2.35 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `pair-236` | 6 | 462 | 0.0.2.29 + 0.0.2.36 / 2.29 + 2.36 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `pair-237` | 6 | 462 | 0.0.2.29 + 0.0.2.37 / 2.29 + 2.37 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `pair-238` | 6 | 462 | 0.0.2.37 + 0.0.2.38 / 2.37 + 2.38 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `pair-239` | 6 | 462 | 0.0.2.37 + 0.0.2.39 / 2.37 + 2.39 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `pair-240` | 6 | 462 | 0.0.2.39 + 0.0.2.40 / 2.39 + 2.40 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `pair-242` | 6 | 462 | 0.0.2.40 + 0.0.2.41 / 2.40 + 2.41 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `pair-243` | 6 | 462 | 0.0.2.40 + 0.0.2.42 / 2.40 + 2.42 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `pair-244` | 6 | 462 | 0.0.2.40 + 0.0.2.43 / 2.40 + 2.43 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `pair-245` | 6 | 462 | 0.0.2.43 + 0.0.2.44 / 2.43 + 2.44 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `pair-246` | 6 | 462 | 0.0.2.46 + 0.0.2.47 / 2.44 + 2.47 | recorded | recorded | yes |
| `pair-247` | 6 | 464 | 0.0.2.47 + 0.0.2.48 / 2.47 + 2.48 | recorded | recorded | yes |
| `pair-248` | 6 | 462 | 0.0.2.48 + 0.0.2.51 / 2.48 + 2.51 | recorded | recorded | yes |
| `pair-249` | 6 | 462 | 0.0.2.51 + 0.0.2.52 / 2.51 + 2.52 | recorded | recorded | yes |
| `raw-reps-v61` | 0 | 0 | - / - | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |
| `reps-229` | 3 | 385 | 0.0.2.29 / 2.28 | 9ec86dfca4a6f85f | v6.1 | no (pre-0.0.2.45) |

## 4. Rules for new runs

1. `gate_run.py` stamps `scorer_contract`, `contract_sha16`, typed `codes` and the two
   axes into every results row and `scorer_contract`+`codes` into every ledger row.
2. `run-record-<rid>.json` carries `stack`: bank sha16 + task count, scorer contract +
   contract hash, strict rule, seed protocol, contour stamp + behavior, harness sha.
3. Before the endpoint is reserved the runner calls `verify_contract()` and dies with
   `SCORER CONTRACT DRIFT` if the workspace's scoring bytes are not the pinned ones.
4. A results directory published without a `stack` block is refused by the publisher;
   a table that cannot name its bank sha16 and contract version is invalid by definition.
5. A correction to any scoring byte is a NEW contract version plus a re-score of every
   published arm; published numbers are never re-labelled in place.

