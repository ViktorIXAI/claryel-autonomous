# audit-census-v2 — verbatim audit-v2 census outputs, 2026-11-07

One file per published bank (`<bank>.out`), produced by:

    PARB_AUDIT_CATS=ABKH python3 scripts/bank_derivability_audit_v2.py benchmarks/hard/<bank>.json

Each file's `SCAN-ID` header names the scanner version + its own module sha16
(`audit-v2 ac4516f263e3e8f2`), the bank sha16, and the scorer contract
(`v6.2 c8c0c7dd114dfc32`) whose matcher the H coverage mirrors. Chain table and
interpretation: `../../DERIVABILITY-CENSUS.md`. audit-v1 ABK outputs are not
stored here: the v1 tool is frozen and its counts recompute exactly
(asserted in `harness/audit_v2_scanner_test.py`).
