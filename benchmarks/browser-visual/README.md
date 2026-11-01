# Browser-visual contour series (second harness family)

Model writes HTML/JS/WebGL/SVG scenes from **frozen prompts**; a separate
contour (run → validate in real Chrome → deterministic JS fixers → targeted
regeneration) repairs the *program*, not the prompt.

Results (render gate: RENDERS_AND_SPINS with 0 errors; per-series n=5):

| series | single-shot | contour1 (fixers) | contour2 (fixers + static nudge) |
|---|---|---|---|
| balls (three.js) | — | 5/5 render-gate | 4/5 |
| pelican (SVG/SMIL) | 0/5 motion (standard prompt) | 5/5 | 5/5 |
| pagoda (WebGL, detail-heavy) | 1/5 file, renders 1/5 | 2/5 | **5/5** |

Two separate verdicts, always (never merged into one "PASS"):
render gate **and** visual-compliance proxy (HSV blob counting: contour1 balls
passed the render gate 5/5 while blob counts showed only ~2/5 drew the
required 12 balls — the render gate cannot see under-drawing).

Key deterministic fixer classes (visible in `vis_fixers.py`): missing
three.js addon imports, `obj.position = new THREE.Vector3(...)` →
`.set(...)`, `.merge()` → `mergeGeometries([...])`, pinned importmap.
Regeneration classes (no patching): garbled SyntaxError, undeclared vars.
Prompt-framing finding (frozen-prompt science, not contour): one animated
word in the pelican prompt → 5/5 scenes move; prohibitions without framing → 0/5.

Method notes in `NOTES-method.md`; run logs `contour1.log`, `contour2.log`.
Full visual artifacts (screenshots, videos, per-run HTML): attached to GitHub
Releases as `visual-artifacts-release-2026-11-01.tar.zst` (~7.4 MB, sanitized contour1/contour2 run dirs).
