# Privacy Boundary — implemented prototype (partial)

Status: **prototype implemented** as of 2026-11-01. `gateway.py` is a
default-deny publish gateway; `test_gateway.py` carries 18 synthetic cases
(PII patterns + canary secrets) and runs in CI (`18 passed, 0 failed`).

What is real: the gateway code, its test contract, and the fact that the
publication pipeline runs every artifact through a secret/PII scan before it
can reach a release (see `scripts/publish/pipeline.py`, stage
`privacy`).

What is **not** claimed: the gateway has never processed real personal data
under a live cloud lane — no cloud lanes are enabled — so its resistance to
novel leaks is unproven. Measured counts on live traffic (blocks / misses /
false-locks) will land here only when real lanes are turned on.

Architecture: `docs/privacy-architecture.md`. Roadmap: `docs/roadmap.md`.
Adoption of any lane follows the same paired-evidence discipline as the text
contour.
