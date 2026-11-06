# Research Direction and Testing Philosophy

**Claryel Autonomous** is an open engineering research project studying how to obtain reliable, useful and economically justified results from AI in real operating conditions. **Claryel** is the broader brand; this repository is the distinct Claryel Autonomous experimental project.

This is neither an academic research program nor a standalone commercial product. It is practical, evidence-oriented experimentation: hypotheses, reproducible measurements, observed failures, revisions and clearly stated limitations. We do not claim to have solved the problems described here.

## Continuity with the existing work

The project's starting point remains unchanged: measure what a frozen local model can achieve on affordable hardware, and what changes when the software surrounding that model changes. We test task quality, latency, memory, power, cost, validation, retries, repair paths and safety boundaries. Paired experiments must identify the model, prompts, seeds, machine and software versions; accepted and rejected runs both matter.

Our newer questions extend this work rather than replace it. They concern the reliability of the **whole task lifecycle**, the possible synergy between local and cloud AI, economic outcomes and changes over time. Current measured findings must not be confused with future research intentions.

## Real-world tasks are imperfect

In practice, a human can formulate a task incorrectly, provide missing or contradictory data, misunderstand the desired output, or judge the outcome incorrectly. A model can misunderstand the request; an agent can make a poor plan; a tool can malfunction; a validator or benchmark reference can be wrong.

Our question is deliberately difficult: **how reliably can an AI-assisted workflow reach a correct, practically useful outcome when task formulation, execution and even evaluation may be imperfect?**

We want to observe and classify errors at each stage: instructions, inputs, interpretation, planning, tool use, output, automated checks and human acceptance. We preserve original artifacts and failure evidence where practical and safe, examine error propagation and recovery, and distinguish a wrong answer from a wrong checker. An ambiguous or defective benchmark must not silently become proof of model failure or success.

Controlled, frozen and reproducible tests remain essential for causal comparisons. Alongside them, we want realistic stress tests with imperfect inputs and changing conditions. These are complementary tracks, not interchangeable scoreboards. A system must be able to ask for clarification, express uncertainty or stop safely when a verified answer is not possible; it must not invent certainty.

## A testable hypothesis: evaluating one's own work

People sometimes judge their own work differently from others' work. We want to test whether AI agents exhibit a comparable **self-evaluation asymmetry**.

An agent might accept its own mistaken assumptions, repeatedly endorse its own incorrect answer, or incorrectly reject a correct answer. This is a hypothesis, **not an established property of agents**.

We intend to compare self-review with blinded review by another agent instance, a different model, deterministic checks and, where necessary, human adjudication. Independent reviewers can share the same errors; disagreement alone does not establish ground truth. We will study false acceptance, false rejection, confidence, error detection and the cost of recovery.

## From local AI toward Mix AI

Our longer-term interest is **Mix AI**: local and cloud AI working together, not competing as ideological alternatives.

Local systems can offer privacy, offline operation, direct control and predictable use of owned hardware. Cloud services may offer capabilities and tools that are difficult or uneconomic to reproduce locally. We want to investigate whether suitable task routing, cooperation and independent checking produce a **synergistic effect**: more practical value than either approach alone.

Synergy is a question to measure, not a benefit we assume. Additional orchestration can also increase cost, latency, failure modes and security exposure. We will examine when local-only, cloud-only or hybrid execution is justified, with explicit permission boundaries and privacy constraints.

## Research in a rapidly changing environment

Unlike a static laboratory setup, our working environment changes continuously, and AI technology currently changes unusually fast. Models, inference engines, quantization, hardware, agent frameworks, cloud APIs, subscription prices and restrictions may all change during an experiment series.

We intend to combine **controlled snapshots** (fixed conditions for interpretable comparisons) with **longitudinal observation** (tracking how practical outcomes evolve). We will not pretend that results from different versions or conditions are directly comparable.

Historical artifacts should remain available for **repeated retrospective analysis**. Later knowledge may reveal overlooked failure modes, mistaken evaluations or interactions between hardware, software, models and economics. Re-scoring a preserved historical answer is different from re-running an old task on a new system; both must be labeled, and any changed scoring rules disclosed.

We want to discover which improvements persist, which disappear, how quickly once-effective configurations become obsolete, and which apparent patterns survive controlled replication. When multiple variables change together, correlation is not proof of causation.

## From performance to economics

We aim to move from answer correctness and execution speed to the **cost of obtaining a verified useful result**: local equipment, depreciation assumptions, electricity, cloud charges, subscriptions, time, retries, validation, human intervention and maintenance. Where data allow, we want monetary accounting down to the cent, clearly separating measured charges from estimates and assumptions.

A later, more exploratory direction is the effect of accessible AI on small-company productivity, expenses and workflows. Possible macroeconomic implications are a much more distant interest of the founder, not a current deliverable or a claim to economic forecasting expertise.

## Long-term possibility: forecasts and scenarios

If enough comparable evidence accumulates, we would like to **test whether historical observations can support useful forecasts** about changes in the technical environment, performance, economics and future failure modes.

We do not expect to predict specific unknown errors or a single inevitable future. Instead, we may examine conditional scenarios with explicit uncertainty: faster or slower model progress, shifting local/cloud cost ratios, new hardware constraints, new validation failures or changing user needs.

Forecasts would need dated assumptions, testable predictions, out-of-sample checks and subsequent comparison with what actually happened. **Failed forecasts are evidence too.** This is a distant hypothesis, not an existing capability.

## Openness, boundaries and practical relevance

We intend to publish code, methodology, run conditions, failures, limitations and reproducible evidence as openly as security, confidentiality, licensing and provider terms permit. We will not publish secrets, personal data or private reasoning traces. Dangerous or destructive experiments require isolation and appropriate human authorization.

Claryel Autonomous itself is **not being developed as a product to sell**. Separately, the Claryel business is working toward configuring and supplying practical local AI systems and, potentially, hybrid systems for users and small organizations. Research findings may help that business **remove or restrict unsupported features**, set realistic task-complexity limits and avoid promising reliability that testing has not demonstrated. Research and commercial delivery have different purposes.

**Our guiding question:** Under imperfect tasks, imperfect evaluation and continuously changing technology, what combination of local and cloud AI can deliver a reliably verified result, at what cost, and with what limitations?

This document describes a research direction. Only linked experiment artifacts and independently checkable evidence establish what has actually been demonstrated.
