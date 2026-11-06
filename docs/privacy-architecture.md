<!-- TEMPORAL-SCOPE-2026-11-06 -->
> **Historical scope note (added 2026-11-06; exact UTC time not recorded).** Synthetic-test prototype only; not demonstrated deployment privacy or secure cloud cooperation. See [preservation policy](EVIDENCE-PRESERVATION.md) and [project direction](TESTING-PHILOSOPHY.md). Original text is retained below.

# Privacy architecture (design + working prototype)

**Status: design implemented as a research prototype.** `benchmarks/privacy-boundary/gateway.py` (default-deny, 12 deny-pattern categories, per-lane policy, `redact()` for synthetic-safe payloads) ships with 18 synthetic tests run in CI. No real user data has ever passed through any cloud lane: the lanes exist in code, none are enabled in policy. Nothing in this repository claims measured privacy
guarantees. The published experiment ran with no cloud participant at all.
This document defines the architecture scheduled as roadmap stage 10, and
the tests that must pass before any local+cloud cooperation result is
allowed to appear in `results/`.

## Layers
**Local layer (sovereign):** user data, documents, journals, local tools,
access policy, local models, audit log. Only the local layer touches raw
data.
**Cloud layer (helper):** hard analysis, code help, diagnosis — receives
*only* what the gateway releases. No direct storage access, ever.
**Gateway (deterministic, not a model):**
1. deny-by-default; explicit allow-listed *categories* of payload;
2. content checks before send (fields, not vibes);
3. identifier scrubbing (names, ids, paths, addresses) with redaction log;
4. attachment + metadata inspection;
5. **error/exception text is scanned too** — secrets leak through stack
   traces and tool logs more often than through prompts;
6. tool allow-list for any cloud-facing agent (no raw network from its side);
7. every release/deny is an append-only audit event;
8. one-switch global cloud-off.

Language models are never the last line of the filter: policies, allow-lists
and field checks are; a model classifier may only *tighten* a release.

## Bypass surfaces we must actively test
direct network calls from the cloud-side tools; secrets riding inside
diagnostic text; intermediate files written before send; local model
misclassifying data ("is it already public?"); logs replayed into prompts;
and over-blocking (false locks of already-public data are failures too).

## Privacy Boundary Tests (planned, synthetic data only)
Canary secret sets with planted PII variants; categories: direct PII, PII
inside documents, PII inside logs, injection attempts to extract, tool-side
bypass attempts, secret-in-error, intermediate-file leakage, misclassification,
false locks. Published metrics: blocks, misses, false locks — never a blanket
"secure" claim.

## Honest note on this repo's own publication
The 2026-11-01 publication pass used: secret scans of every published file,
LAN identifiers and personal paths removed or replaced with placeholders,
API keys and engine configs sanitized (`PUBLICATION-NOTES.md`), raw agent
transcripts withheld with the reason recorded (`docs/limitations.md`). That
is the manual ancestor of the pipeline this stage automates.
