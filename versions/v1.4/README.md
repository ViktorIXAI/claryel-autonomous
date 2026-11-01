# v1.4 — REJECTED

- **Change:** cheap repair without source document + repair retries capped at 1 (BUNDLED - rule violation)
- **Numbers:** Mac A/B: 19/19 -> 3/19 correct; -59% input tokens, -43% time; cause later pinpointed to the retry cap; cheap branch was dead code
- **Code state:** not_recorded (reverted)
- **Adoption:** agent-rejected
- **Provenance:** Agent-proposed/implemented/tested/evaluated (docs/autonomy.md);
  decision entry: history/agent-decisions/gate-versions.log
