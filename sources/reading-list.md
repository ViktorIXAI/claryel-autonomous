# Reading And Evidence List

Checked on `2026-11-02`. These sources are external inputs. They are not
automatically treated as proof of this repository's results.

## Local AI and global AI economics

| source | level | why it matters here | status |
|---|---|---|---|
| [Intelligence per Watt: Measuring Intelligence Efficiency of Local AI](https://arxiv.org/abs/2511.07885), arXiv:2511.07885, accessed 2026-11-02 | `method` + `comparison` | Measures accuracy per energy unit for local models and local-cloud routing; supports adding energy/power alongside answer quality. | reviewed from abstract/search snippets; full-text comparison pending |
| [Sometimes Painful but Certainly Promising: Feasibility and Trade-offs of Language Model Inference at the Edge](https://arxiv.org/abs/2503.09114), arXiv:2503.09114, accessed 2026-11-02 | `warning` + `comparison` | Directly measures memory, speed and energy for edge inference; relevant to 8–12 GB hardware limits. | reviewed from abstract/search snippets; full-text comparison pending |
| [Scaling Laws for Energy Efficiency of Local LLMs](https://arxiv.org/abs/2512.16531), arXiv:2512.16531, accessed 2026-11-02 | `method` | Uses continuous sampling and area-under-curve energy integration; useful for our power/energy join design. | reviewed from abstract/search snippets; full-text comparison pending |
| [Beyond Benchmarks: The Economics of AI Inference](https://arxiv.org/abs/2510.26136), arXiv:2510.26136, accessed 2026-11-02 | `method` + `context` | Frames inference as production with marginal cost, scale and quality trade-offs. | reviewed from abstract/search snippets; full-text comparison pending |
| [Inference economics of language models](https://arxiv.org/abs/2506.04645), arXiv:2506.04645, accessed 2026-11-02 | `method` | Explicit model of cost per token versus serial token speed; relevant to batch and context-length decisions. | reviewed from abstract/search snippets |
| [The Price of Progress: Algorithmic Efficiency and the Falling Cost of AI Inference](https://arxiv.org/abs/2511.23455), arXiv:2511.23455, accessed 2026-11-02 | `context` | Separates hardware cost decline from algorithmic efficiency progress; useful for interpreting benchmark cost changes over time. | reviewed from search snippets |
| [A Cost-Benefit Analysis of On-Premise Large Language Model Deployment: Breaking Even with Commercial LLM Services](https://arxiv.org/abs/2509.18101), arXiv:2509.18101, accessed 2026-11-02 | `method` + `comparison` | Directly relevant to break-even between local deployment and subscriptions. | reviewed from abstract |
| [Introducing LCOAI: A Standardized Economic Metric for Evaluating AI Deployment Costs](https://arxiv.org/abs/2509.02596), arXiv:2509.02596, accessed 2026-11-02 | `method` | Suggests a levelized cost metric for AI deployments; may become a later reporting column. | reviewed from abstract |

## Micro and macro economics

| source | level | why it matters here | status |
|---|---|---|---|
| [The Simple Macroeconomics of AI](https://economics.mit.edu/sites/default/files/2024-04/The%20Simple%20Macroeconomics%20of%20AI.pdf), Daron Acemoglu, MIT, accessed 2026-11-02 | `method` + `context` | Task-based framework: micro cost savings do not automatically scale into large macro productivity gains. | reviewed from PDF snippet/search result |
| Artificial Intelligence and Productivity in Europe, IMF Working Paper WP/25/67, April 2025, IMF document id `wpiea2025067`, accessed 2026-11-02 | `context` | Connects micro productivity estimates to modest medium-term macro estimates. | reviewed from search/PDF snippet |
| AI Adoption and Inequality, IMF Working Paper WP/25/68, April 2025, IMF document id `wpiea2025068`, accessed 2026-11-02 | `warning` + `context` | Wage and wealth inequality effects of AI adoption; relevant to social framing, not harness benchmarks. | reviewed from search/PDF snippet |

## Sociology, households and labour

| source | level | why it matters here | status |
|---|---|---|---|
| [The Household Impact of Generative AI: Evidence from Internet Browsing Behavior](https://arxiv.org/abs/2603.03144), Blank/Schubert/Zhang, arXiv:2603.03144, accessed 2026-11-03 | `context` | Household adoption and time-use effects; useful for why home-local AI may matter outside work tasks. | reviewed from search snippet |
| [Adoption and Expected Impact of Generative AI: Evidence from Italian Households](https://www.bancaditalia.it/pubblicazioni/qef/2025-0929/QEF_929_25.pdf), Bank of Italy QEF 929/25, accessed 2026-11-02 | `context` | Survey-based adoption, trust and job expectations in households. | reviewed from search/PDF snippet |
| [Socioeconomic Status Influences the Usage of Language Technologies](https://arxiv.org/abs/2505.12158), arXiv:2505.12158, accessed 2026-11-02 | `warning` | Shows socioeconomic differences in prompts and interaction styles; useful for user-facing task design and fairness limits. | reviewed from abstract/search snippet |
| [Advancing AI Capabilities and Evolving Labor Outcomes](https://arxiv.org/abs/2507.08244), arXiv:2507.08244, accessed 2026-11-02 | `context` | Links occupational AI exposure to near-real-time labour outcomes. | reviewed from abstract/search snippet |

## What this list does not do

It does not make this repository into a scientific paper. It does not replace
our own paired A/B evidence. It does not transfer external benchmark numbers
onto our hardware unless the model, workload, context length, quantization,
power measurement and task definition are compatible enough for comparison.
