# v1.7 — ACCEPTED (working baseline of the day)

- **Change:** mechanical form repair by code, zero model calls for form; refusal rules; PARB_CHEAP default 0
- **Numbers:** A/B vs v1.3: 19/19 vs 19/19; input -31%, generation -24%, wall -19%, form model-calls -45%. Full series Mac: ptok/attempt 1211 (v1.2)->889; mixed arm (v1.7+cheap) 16/19 isolates the poison
- **Code state:** gate_fixers.py as published (unchanged v1.7->v1.9) + gate_fixers_test.py 12/12; runner snapshot not retained
- **Adoption:** agent (paired A/B), human informed at morning report
- **Provenance:** Agent-proposed/implemented/tested/evaluated (docs/autonomy.md);
  decision entry: history/agent-decisions/gate-versions.en.md (Russian original archived in the ru-source-records release asset)
