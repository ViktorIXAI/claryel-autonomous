Agent Lab coordinator synthesis

System implemented:
- Hermes project: `claryel-agent-lab`
- Kanban board: `agent-lab`
- Single profile: `default`
- Logical agents implemented as bounded cards, not persistent profiles.

Completed cards:
- Inventory of project and gate state.
- Bounded 33-task smoke plan for new workers.
- Public dated hardware price snapshot schema.
- Security audit of current checkout and planned artifacts.
- Publication summary for roadmap and project rules.

Important decisions:
- Do not create multiple visible Hermes profiles for this lab.
- Keep a compact board with a few task cards.
- Heavy fleet testing starts only after current paired gate work is resolved.
- New workers begin idle/smoke and must not contaminate paired runs.
- No credential-like finding was found; existing history/releases stay under
  maintainer-approved non-critical risk decision.
- Future publications must pass scanner gates.
