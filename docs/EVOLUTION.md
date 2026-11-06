<!-- TEMPORAL-SCOPE-2026-11-06 -->
> **Historical scope note (added 2026-11-06; exact UTC time not recorded).** This early protocol does not override current least-privilege and owner-approval requirements. See [preservation policy](EVIDENCE-PRESERVATION.md) and [project direction](TESTING-PHILOSOPHY.md). Original text is retained below.

# Autonomous Evolution Mode — the protocol

This is the loop that produced v1.0→v1.9 (and rejected v1.4/v1.6 and the
no-op v1.5). It is deliberately boring and auditable: an agent may change
the harness, but only inside these rails.

```
 ┌──────────────────────────────────────────────────────────────────┐
 │ measure → diagnose → ONE hypothesis → implement → unit-test      │
 │  → smoke subset → PAIRED A/B (same task,rep keys) → second box   │
 │  → verdict appended to the decision log → next cycle             │
 └──────────────────────────────────────────────────────────────────┘
```

## Rails

1. **Evidence-driven start.** A new version starts from the previous
   version's *final results + ledger*, never from intuition. Failure causes
   are machine-readable (`notes[]` strings), counts come from code.
2. **Exactly one substantive change per version.** Bundled changes were
   punished with a mis-diagnosed v1.4 (the log names the author of that
   mistake: the agent itself).
3. **Classify before patching.** CHRONIC failures get structural changes;
   LOTTERY failures get retry/selection; never a nudge for a wiring bug
   (v1.9 was found this way: the model was right, the contour was wrong).
4. **Unit-test the fixer first** (`gate_fixers_test.py`, `gate_v19_d_test.py`
   must stay green) — mechanical fixers are allowed to normalize form but
   must *refuse* whenever data would be invented; refusal paths are tested.
5. **Smoke before overnight launches**: a subset run with fresh state files,
   grepping the new contour events.
6. **Paired A/B is the only adoption metric**: same frozen plan positions,
   per-`(task, rep)` deltas; means over differently-mixed plans are rejected
   as evidence. Judge on weak categories, watch regressions elsewhere.
7. **Cross-box replication**: adopted versions must reproduce on physically
   different hardware with identical seeds.
8. **Cost accounting next to quality**: model calls, tokens, seconds per
   attempt; rejected savings: v1.6 (−45% tokens, −3 correct answers).
9. **The decision log is append-only and adversarial to its author**:
   rejected versions get full post-mortems with the numbers that killed them
   (`history/agent-decisions/gate-versions.en.md`).
10. **Nightly cadence via one-shot scheduled diagnostics**: scheduled jobs
    pull artifacts, aggregate, classify, propose exactly one hypothesis;
    only the main agent session builds and launches versions. Morning report
    to the operator, verdict-first ("fine / middling / bad"), numbers only
    where not fine.

## Where the human sits

The operator (a) sets the standing rule "never stop when idle", (b) owns
hardware power-cycling and scope, (c) reads morning reports, (d) can veto
any version. The agent self-rejected v1.4/v1.5/v1.6 on its own numbers —
the human never had to overrule a bad adoption; that asymmetry (hard to
adopt, easy to reject) is the safety property.

## Reproducing the loop without an operator present

Everything above is implementable with cron + this repo (`docs/reproduction-guide.md`
for the mechanics). Two non-negotiables if you automate it fully: the
decision log stays append-only, and adoption requires the paired
cross-box gate — a loop that can adopt on vibes is not an evolution loop,
it is a drift generator.
