# Issue #25 source verification addendum — 2026-11-21

## Scope

This dated addendum records a bounded verification of the four external arXiv URLs introduced by `sources/daily/2026-11-21-self-evolution.md`. It does not validate the papers' experiments, reproduce their results, or convert their claims into evidence for this repository.

Verification date: 2026-11-21 (UTC). Verification method: opened each canonical arXiv abstract page and checked that the page resolved, the title matched the repository summary, and the page exposed a versioned citation identifier.

## Source-to-claim ledger

| Repository source | Canonical URL | Page result | Stable identifier | Claim boundary |
|---|---|---|---|---|
| `sources/daily/2026-11-21-self-evolution.md` §1 | https://arxiv.org/abs/2611.25429 | Resolved; title matched “Evolve Where It Matters: Coverage-Guided Self-Evolution of Agent Skills”; v1 listed | arXiv:2611.25429v1 | The percentages and ablation numbers remain reported by the paper; no repository reproduction or independent audit is implied. |
| same §2 | https://arxiv.org/abs/2611.25380 | Resolved; title matched “Beyond Weight Updates: Evolving Agent Harnesses for Domain Specialization”; v1 listed | arXiv:2611.25380v1 | The reported benchmark pattern remains source-reported; no local harness-adapter experiment is claimed. |
| same §3 | https://arxiv.org/abs/2611.21056 | Resolved; title matched “Evaluation-Free Recursive Self-Improvement for Coding Agents”; v1 listed | arXiv:2611.21056v1 | The ELITE results and speedups remain source-reported; no local implementation or reproduction is claimed. |
| same §4 | https://arxiv.org/abs/2611.23068 | Resolved; title matched “The Resolution Hypothesis: Agent Evolution’s Key Is Identifying Improvements”; v1 listed | arXiv:2611.23068v1 | The multi-method/noisy-selection findings remain source-reported; no repository conclusion about our own evolution loop is claimed. |

## Evidence-preserving conclusion

The four URLs are live and resolve to matching arXiv records with explicit v1 identifiers. This closes only the narrow URL/title/version check for the new source surface. It does **not** establish:

- independent validation of any numerical result;
- transfer of the reported methods to Claryel Autonomous;
- successful documentation/link CI for the current HEAD;
- exhaustive repository-wide path coverage;
- resolution of the existing secret-scan failure or owner decisions.

No historical file, frozen result, production setting, security policy, or benchmark score was changed.
