# Acknowledgments

This lab stands on four open projects. None of them made this experiment;
all of them made it possible.

## The model — Qwen team, Alibaba

The measured model is **Qwen3.8-Flash-Next**, the first open-weight release
of the Qwen4-preview architecture (hybrid attention with QSA, 512-expert
MoE) from the [Qwen team](https://github.com/QwenLM) at Alibaba Group:

- Base model: [Qwen/Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next) · [github.com/QwenLM/Qwen3.8](https://github.com/QwenLM/Qwen3.8) · [qwen.ai](https://qwen.ai)
- The GGUF build we ran is the recommended **IQ3_S** operating point from
  **[ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF)**
  (Institute of Science and Technology Austria, DASLab) — non-uniform
  per-tensor quantization produced with their GSQ and RCO methods; file
  sizes match byte-exact against our [model passport](hardware/inventory/model-iq3s.md),
  and their release is Apache-2.0 over the base model's Qwen community license.
- The quantization formats themselves (GGUF, i-quants) descend from the
  [llama.cpp](https://github.com/ggml-org/llama.cpp) / ik_llama.cpp ecosystem.

No weights are redistributed here — identifiers, sizes and SHA-256 only.

## The engine — Strata

Every benchmark series was served by **[Strata](https://github.com/Niko1221/Strata)**
by Niko1221 and the Strata contributors (MIT): “Run powerful AI on your own
computer.” Engine **0.1.52** served B2003 and P2005 throughout (build
`a42cc3d7df70+cuda13.0`, verified via `strata --version` and
`engine-component.json` on 2026-11-01); the Mac Studio runs the Strata macOS
line. Strata's OpenAI-compatible serve endpoint is what `harness/` talks to;
Strata itself is not part of this repository and any compatible endpoint
works. Their documentation (docs/INSTALL.md, docs/DETAILS.md, …) solved
more of our hardware puzzles than we deserve to claim.
Support their work: [releases](https://github.com/Niko1221/Strata/releases) ·
[buymeacoffee.com/strataengine](https://buymeacoffee.com/strataengine).

## The agent — Hermes by Nous Research

Every command, instruction and standing rule in this experiment — including
every “improve the harness”, every “continue”, every “publish” — was issued
to and carried by **[Hermes Agent](https://github.com/NousResearch/hermes-agent)**
(Nous Research, MIT; [docs](https://hermes-agent.nousresearch.com/docs)).
The contour code, validators, A/B tooling and decision logs in this repo
were written and exercised by that agent.

And — because Nous describes it accurately and we watched it happen —
Hermes carries **its own learning loop**: “it creates skills from experience,
improves them during use, nudges itself to persist knowledge, searches its
own past conversations.” That loop ran during this very experiment: the
agent's skill library and persistent memory absorbed procedures and
pitfalls mid-experiment (launch protocols, telemetry gotchas, publication
hygiene). That is a *second, distinct* improvement axis — the agent's
procedural memory, not model weights and not the contour — and this project
labels the three axes separately, per [`docs/autonomy.md`](docs/autonomy.md).

## And the humans who make open research possible

The Qwen, ISTA-DASLab, Strata and llama.cpp communities publish models,
quants, engines and formats under open licenses. Reproducible AI research
is built on that generosity; this repository tries to return one small
piece of it: the failures, fully documented.
