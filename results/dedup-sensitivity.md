# Deduplication-rule sensitivity

`analytics/dedup_sensitivity.py` recomputes the headline paired deltas under
three repeat-collapsing rules: **best** (published rule: per `(task, rep)`
keep max content), **first** (first occurrence), **worst** (min content).

Result (machine-readable: `dedup-sensitivity.json`):

| comparison | best | first | worst | rule-sensitive? |
|---|---|---|---|---|
| v1.8→v1.9 B2003 | +0.0472 (229↑/79↓) | +0.0472 (229↑/79↓) | +0.0472 (229↑/79↓) | **no** |
| v1.8→v1.9 Mac | +0.0505 (183↑/0↓) | +0.0505 (183↑/0↓) | +0.0505 (183↑/0↓) | **no** |

The `v18-final/`/`v19-final/` series files contain exactly one record per
`(task, rep)` — the runner's own state prevents duplicates before
aggregation — so all three rules are identical on the published finals.
Rule choice matters only when raw (pre-final) files are aggregated; the
`aggregate_auto.py` pipeline path applies the best-rule explicitly for
those. Conclusion: the published deltas are **dedup-rule-insensitive**.
