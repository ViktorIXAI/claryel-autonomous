# Open Engineering And Economic Questions

These are operational questions the repository is trying to answer. They are
not framed as scientific claims; they are concrete decisions that affect
whether a local AI system is useful, safe and affordable.

## Harness questions

- Which contour changes improve real task quality, not only scoring format?
- Which failures are harness wiring bugs rather than model weaknesses?
- Which repair paths are safe enough for finance and operations tasks?
- How much autonomy is useful when the operator keeps the final adoption rule?

## Hardware and resource questions

- How much answer quality can a 12 GB GPU deliver before VRAM headroom becomes
  unsafe?
- Where does context length start to hurt latency or force offloading?
- Which machines are worth running as local workers instead of cloud fallbacks?
- How do unified-memory Macs compare to discrete-GPU boxes for the same task?

## Economic questions

- What does one useful local answer cost after electricity, depreciation,
  maintenance and failed attempts?
- When does a local machine break even against a cloud subscription or API?
- When is a smaller local model plus a contour better than a larger remote
  model?
- Which categories are worth automating, and which still need human judgment?

## Social questions

- How do households and small operators actually use local AI tools?
- What trust, inequality or skill gaps appear around local AI deployment?
- How should privacy boundaries be enforced when local and cloud systems are
  mixed?

These questions are answered one decision at a time through paired runs,
resource telemetry, cost tables and published failures.
