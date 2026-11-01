# Agent Lab Roadmap and Hardware Price Intelligence

Status: proposal adopted for the next development cycle, 2026-11-01.

This roadmap is not an attempt to invent another general-purpose agent
framework. Its purpose is to cross-check the complete path:

```text
raw model output
  -> benchmark validator
  -> contour / harness
  -> multi-machine experiment system
  -> agent hierarchy
  -> external AI ecosystem bridge
  -> local-first private-data workflow
  -> budget hardware verdict
```

The published value is the path and measurements, not marketing claims about a
"working agent product".

## 1. Security posture going forward

The completed audit found no critical credential in the public repository,
releases or CI logs. Existing history and old release assets are retained by
maintainer decision.

Future publications follow stricter rules:

1. Browser profile state, cookies, passwords, sessions and caches are never
   packaged.
2. Raw security reports remain outside the public repository.
3. Current-code credential findings block publication.
4. Infrastructure metadata is moved to local untracked configuration.
5. Public dashboards contain only safe identifiers, rules, counts and dates.
6. External actions require an explicit human approval boundary.

## 2. Hardware price intelligence

### What is worth publishing

Yes: current replacement prices are useful for reproducibility and budget AI
research. A public system can track:

- component name, model, MPN/SKU;
- condition: new, refurbished, used;
- country/region, currency, VAT assumption;
- observed price and date;
- stock state;
- offer URL;
- total reconstructed system cost;
- cost per useful accepted benchmark task;
- cost per watt-hour of experiment.

Example output:

```json
{
  "box": "budget-gpu-worker",
  "asof": "2026-11-01",
  "currency": "EUR",
  "total_new_low_eur": 1100,
  "total_used_median_eur": 850,
  "components": [
    {
      "part": "gpu",
      "model": "GeForce RTX 3060 12GB",
      "price_eur": 300,
      "condition": "used",
      "observed_at": "2026-11-01",
      "source": "public-marketplace-listing"
    }
  ]
}
```

### How agents should do it

Use three separate agents:

- `scout`: finds public offers and saves source/date/model identifiers.
- `validator`: removes duplicates, suspicious outliers and affiliate noise.
- `publisher`: builds a dated public price table and changelog.

Safety rules:

- no cookies, marketplace accounts, private accounts or login profiles;
- no affiliate links unless the maintainer explicitly approves monetisation;
- respect `robots.txt`, terms of service and rate limits;
- prefer public APIs or manually approved sources when scraping is fragile;
- never claim a scraped price as an official price;
- publish snapshots with dates so price movement is auditable.

### Is it useful for GitHub?

Yes, but the strong part is not "we found links". The strong part is a
reproducible dataset showing how benchmark hardware and budget configurations
change over time:

```text
hardware generation -> model size -> quality -> tokens/s -> energy -> accepted result -> total cost
```

That turns the repository into an AI-hardware research record rather than a
generic price tracker.

## 3. Fleet expansion over the next hours

Current priority remains completion of the current paired gate experiment. New
machines should be introduced in smoke mode, not by replacing the active paired
series.

Proposed role split:

| Role | Responsibility | Brain or worker? |
|---|---|---|
| Main model engine | Serve the primary local model | brain |
| Paired duplicate | Run the same gate on a second engine | brain |
| CPU controller | Dispatcher, ledger, security scans, publication | no brain |
| GPU worker | Browser/visual or small local model experiments | worker/brain |
| Artifact mirror | Preserve logs/screenshots/package inputs | storage |
| Observer host | HA alerts and lifecycle monitoring | control |

First expansion sequence:

1. Register each machine with safe metadata only: role, CPU, RAM, GPU, VRAM,
   storage class, OS and benchmark class.
2. Run a hardware fingerprint locally; never publish hostname/IP/user.
3. Deploy the gate runner but keep it idle until the active experiment ends.
4. Run a 30–100 task smoke subset to verify SSH, model endpoint, ledger and
   timeout behaviour.
5. Only then expand to paired runs.

## 4. Multi-agent ladder

The experiment should be climbed in levels.

### Level 0 — raw model

Direct prompt, no harness. Measures raw model behaviour.

### Level 1 — validator contour

Gate, repair loop, deterministic checks. This is the current text-gate work.

### Level 2 — task worker agents

Each worker runs:

```text
fetch task -> execute -> validate -> repair -> ledger -> report
```

No autonomous planning yet.

### Level 3 — dispatcher agents

Domain agents queue tasks across machines:

- text-gate agent;
- browser-visual agent;
- hardware benchmark agent;
- price scout agent;
- security audit agent.

Each has a narrow contract and cannot mutate other agents' state.

### Level 4 — two-level hierarchy

A root coordinator supervises domain agents. It does not talk directly to all
machines. It receives compact summaries from domain agents and asks for evidence
when a result is suspicious.

### Level 5 — external ecosystem bridge

Local agents may exchange tasks with external chat/bot ecosystems, but only
through a bridge that:

- redacts private data;
- requires approval before external mutation;
- logs outbound and inbound actions;
- stores raw personal material locally only.

## 5. Final product direction

After the multi-agent ladder is measured, select mature tools instead of
continuing to build everything manually. The target is a local-first assistant
that can work with personal data while still cooperating with external AI
systems.

Selection criteria:

- works on a $1,000–$10,000 hardware budget;
- supports local models and fallback external models;
- has stable tool/task contracts;
- supports logging, auditing and replay;
- supports private-data boundaries;
- supports multi-machine execution;
- is maintainable by one operator.

The benchmark data should decide the tool choice, not hype.
