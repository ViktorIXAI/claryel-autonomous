# v1.9 — RELEASED (this repo's contour)

- **Change:** d_order_steps(): mechanical normalization of the model's ordered tool list into scorer-required agent_steps + summary answer; no prompt/reference edits
- **Numbers:** paired vs v1.8: B2003 +0.047 (229:79, n=2127), Mac +0.051 (183:0, n=2416); D 0.42->1.00 (B2003), D-ea 0.34->1.00 both boxes
- **Code state:** PUBLISHED BYTE-EXACT: harness/gate_run.py == snapshot gate_run.v19.bak-0745 (pre-portability-edits; edits itemized in PUBLICATION-NOTES.md); test-first: gate_v19_d_test.py
- **Adoption:** agent (paired + cross-box), human standing-rule authorized
- **Provenance:** Agent-proposed/implemented/tested/evaluated (docs/autonomy.md);
  decision entry: history/agent-decisions/gate-versions.en.md (Russian original archived in the ru-source-records release asset)
