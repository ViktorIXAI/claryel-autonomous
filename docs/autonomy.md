<!-- TEMPORAL-SCOPE-2026-11-06 -->
> **Historical scope note (added 2026-11-06; exact UTC time not recorded).** This ledger concerns the original agent-development sequence. Its autonomy and no-cloud statements are not global claims. See [preservation policy](EVIDENCE-PRESERVATION.md) and [project direction](TESTING-PHILOSOPHY.md). Original text is retained below.

# Autonomy ledger — who did what

Classifications (from the project brief):
**Human-directed** · **Agent-proposed** · **Agent-implemented** ·
**Agent-tested** · **Agent-evaluated** · **Human-approved** ·
**Autonomously-adopted/rejected**.
Anything not recoverable from the record is `unknown` / `not_recorded`.

## Standing rules (the human's actual role)

The operator's recorded instructions (paraphrase, verbatim RU originals stay
in the operator's own notes): (1) benchmark this local model; (2) never stop
when idle — continue measure→diagnose→version→compare cycles autonomously;
(3) reports to a human are verdict-first; (4) don't reboot hosts, don't touch
credentials, keep dangerous ops isolated. **The operator never wrote contour
code and never edited a contour change** (session attribution; per-line
cryptographic attribution does not exist for v1.0–v1.8 — see limitations).
Adoption by the agent on pre-agreed paired-evidence rules was the authorized
default; the human veto existed but was never exercised because the agent
rejected its own three weak versions first.

## Per-version ledger

| ver | goal origin | proposal | code | tests | evaluation | adoption decision |
|---|---|---|---|---|---|---|
| benchmark suite (bank, plan, scorers) | Human-directed ("measure this model") | Agent-proposed design | Agent-implemented | Agent-tested (verify passes on refs) | Agent-evaluated | Human-approved (used as the substrate) |
| v1.0–v1.2 | unknown (pre-log era) | Agent (inferred; log starts at v1.2) | Agent | Agent | Agent | **not_recorded** how adopted |
| v1.3 | Agent-proposed | Agent | Agent-implemented | Agent-tested | Agent-evaluated | Autonomously-adopted (paired +35% cost noted; log says "accepted, at a cost") |
| v1.4 | Agent-proposed (cost idea) | Agent | Agent-implemented | Agent-tested (A/B) | Agent-evaluated | **Autonomously-rejected** (3/19 vs 19/19) |
| v1.5 | Agent-proposed (guard) | Agent | Agent-implemented | Agent-tested | Agent-evaluated | **Autonomously marked no-op** (guard fired 0×) |
| v1.6 | Agent-proposed (make cheap path real) | Agent | Agent-implemented | Agent-tested | Agent-evaluated | **Autonomously-rejected** (−3 correct) |
| v1.7 | Agent-proposed after v1.4–1.6 failures | Agent | Agent-implemented | Agent-tested (12-case suite) | Agent-evaluated | Autonomously-adopted; human informed next morning (standing rule 2) |
| v1.8 | Agent-proposed | Agent | Agent-implemented | Agent-tested + smoke | Agent-evaluated (weak-cat rule) | Autonomously-adopted (scope-limited) |
| v1.9 | Agent-proposed (CHRONIC classification) | Agent | Agent-implemented (test-first) | Agent-tested (unit + smoke) | Agent-evaluated (paired, cross-box) | Autonomously-adopted; this is the RELEASED contour |
| v2.0 | Agent-proposed | Agent | Agent-implemented | Agent-tested (18 probe rows) | Agent-evaluated: insufficient | **not adopted** — published as experimental |

Every operator instruction — including each “continue improving” cycle —
reached the lab through the Hermes agent (its task queue, cron and terminal);
there was no side channel around it. Hermes also runs its own documented
learning loop (skills created from experience, improved during use): that
loop learned *during* this experiment — a third improvement axis (agent
procedural memory), deliberately kept separate from model weights and from
the contour in every claim in this repo.

Cloud models: none participated in the published chain (fully local agent).
Cloud-collaboration ledgers become possible only after the
`privacy-boundary` stage — and they will be recorded with the same labels.

## Evidence anchors

- `history/agent-decisions/gate-versions.en.md` — decision entries written by
  the agent *during* the runs, including self-rejections with numbers.
- File timestamps + A/B artifacts in `logs/INDEX.md` — sequence matches the
  log (test written before fix: `gate_v19_d_test.py` 02:46 < v1.9 snapshot 07:43).
- `logs/agent-actions/` — see `scripts/` + this ledger; raw agent session
  transcripts are *not* published (privacy decision, documented in
  `docs/limitations.md`).
