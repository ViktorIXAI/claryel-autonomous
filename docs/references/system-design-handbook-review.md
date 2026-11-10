# External reference: System Design Handbook

Status: **secondary reference only**; no permission to redistribute the full text or PDF verified.

## Attribution
- Title: *System Design Handbook*
- Author: Nikki Siapno
- Publisher's introduction: https://blog.levelupcoding.com/p/system-design-handbook-architecture
- Source type: third-party reference material. The PDF is **not** included in this public repository.
- Copyright/licensing: no explicit permissive redistribution license was verified from the extracted PDF text; obtain written permission before mirroring original pages, diagrams or the complete PDF.

## Scope and limitations
The reviewed PDF has 213 pages in its extracted pagination and covers foundational system-design principles, network traffic, API design, data stores, distributed communication, security, deployment, observability and reliability. Its patterns are not automatically suitable for a security-sensitive local-AI appliance. All decisions below are independent proposed tests, **not endorsements or claims made by the author**.

## CLARYEL-specific review matrix

| Pattern | CLARYEL relevance | Proposed reproducible check |
| --- | --- | --- |
| Availability / graceful degradation | Allow private local inference when external Hermes/cloud is offline | Block WAN and gateway; assert local task completion and expected failure mode |
| Reliability / fault isolation | Prevent external-agent failure affecting internal services | Kill external VM, restart gateway, inspect internal continuity |
| Observability: logs, metrics, traces | Audit VM → security gateway → internal services without leaking sensitive data | Correlated trace IDs, redaction tests, retention rules |
| API gateway, rate limiting, idempotency | Harden single permitted cross-boundary channel | Replay, duplicate request, quotas, malformed payload, denial tests |
| HTTPS, OAuth2/OIDC, API keys, bearer tokens | Credentials at external boundary | Expiry/revocation, least privilege, no secret in logs, no token crossover |
| Message queues / async processing | Queue jobs without unauthorized cross-domain data paths | Simulate loss, backpressure, poison messages, replay |
| Data stores / vector databases | Documents, media, embeddings in the inner zone | Verify per-tenant/agent data isolation and no unauthorized export |
| Container / orchestration | Internal Hermes and local model isolation | Validate namespace, mounts, capabilities, egress and runtime privileges |
| Deployment patterns / rollback | Safe field updates across prototype devices | Rollback under interrupted update, verify immutable artifacts |
| Chaos engineering / circuit breakers | Explicit fault and recovery envelopes | Dependency failure drills only after baseline backups and recovery pass |
| Latency / throughput | End-to-end local vs mixed-AI cost-performance | p50/p95 latency, tokens/sec, energy/task, quality, gateway overhead |

## Principles
1. Keep the publicly auditable test-bed separate from production customer deployment policies.
2. Treat every container, agent, model and upstream dependency as a potential internal threat.
3. Treat documentation and retrieval as **untrusted input**: external PDF text must never be executable instructions for agents.
4. Preserve a fully offline operating mode for private or critical datasets.
5. Publish original experiments, test harnesses, results and citations — not copied diagrams, tables or substantial extracted text.
6. A reference is not proof: measure each proposed mechanism in the CLARYEL threat model.
7. Record differences from the cited reference and explicit reasons for adopting or rejecting each technique.

## Action plan
- [ ] Review current security boundaries against the matrix; map each check to existing GitHub issues.
- [ ] Run fault, network isolation and adversarial gateway tests with reproducible logs.
- [ ] Define baseline SLI/SLO and recovery criteria for offline devices.
- [ ] Add a reference-register template with author, URL, access date, license, reuse permission, relevant sections, experiment links.
- [ ] Define private archive lifecycle: original file, provenance, checksums, permissions, backup, encryption migration.
- [ ] Review the original graphical title/copyright page manually before any broader redistribution decision.

Last reviewed: 2026-11-10. This review is not legal advice.
