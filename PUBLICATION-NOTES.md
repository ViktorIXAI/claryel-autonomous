# Publication edits vs. the original run snapshots

Every published code file is a snapshot taken from the live rig. The edits below
are the ONLY differences from the exact bytes that produced the archived results
(the raw snapshots stay on the rig; `logs/INDEX.md` pins the result artifacts
they produced).

| file | edit | why |
|---|---|---|
| `harness/gate_run.py` | snapshot = `gate_run.v19.bak-0745` (released v1.9 contour) | v1.9 is the version the README numbers refer to; the live file already contained unvalidated v2.0 edits and was NOT released |
| `harness/gate_run.py` | `PARB_KEY_FILE` default emptied; key file lookup simplified; plain `Bearer` header | portability: vanilla OpenAI-compatible endpoints need no key file; the old header-spelling trick was a workaround for the rig's own log-scrubber, meaningless here |
| `harness/parb_run.py` | `API`/`MODEL` moved to `PARB_API`/`PARB_MODEL` env | portability |
| `harness/parb_check.py` | one regex made a raw string (`"\s…"` → `r"\s…"`) | Python 3.12 SyntaxWarning; byte-level change, **semantics identical** ("\s" is not a recognized escape, Python keeps it literally); verified by re-running all scorer behavior checks — the rig's original bytes remain archived on the rigs |
| `harness/make_plan.py` | new | publication convenience; reproduces the frozen plan from `tests/bank.json` (in the original runs the plan was prepared once by `parb_prep.py` and frozen — the freeze discipline itself is unchanged) |
| `experiments/ab/analyze-0130.py` | rig-local absolute paths → relative | privacy/portability |
| launcher shell scripts | LAN hosts/users dropped, placeholders instead | privacy |

No file had logic, prompts, scorers or thresholds altered. `PARB_GATE_VERSION`
selects the contour generation at runtime (`v1.2` … `v1.9` gates are all inside
`gate_run.py`), so the published runner can reproduce every published comparison.
