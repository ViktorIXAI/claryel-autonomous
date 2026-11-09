# CLARYEL architecture isolation reassessment — 2026-11-09

**Status:** RESEARCH / DESIGN ONLY. **Owner-mandated deployment freeze:** from 2026-11-09 10:10 CET to 2026-11-10 10:10 CET, with resumption **only after explicit owner go/no-go**, not automatically. Issue #43 governs. No service stops, configuration changes, benchmark freezes or firewall changes are authorized by this document. Notify agents/operators; verify separately that any active deployment automation actually honors the hold.

## Executive finding
This is an *assurance and commercialization* decision, not evidence that CLARYEL was compromised, nor that Docker is categorically unsafe. Conventional Linux containers share the host kernel; VMs add a separate guest kernel and hypervisor boundary. NIST SP 800-190 states container segmentation is less clear than VM isolation. But VMs still expose attack surfaces through shared filesystems, hypervisor services, devices, guest agents, secrets and networks. Security must be demonstrated for each trust boundary and each customer threat model.

## Proposed design principles (NOT approved deployment)
1. Assign independent VMs to **mutually untrusted security domains**, rather than equating one Docker container with one trust boundary. Possible zones: public/cloud-connected Hermes, strictly local Hermes + private data, gateway/policy, inference, Home Assistant, backup/management. Determine whether gateway and management demand dedicated physical separation or VM separation. Avoid automatic direct external-to-internal VM connectivity.
2. Keep Docker/Podman where useful *inside a trust domain* for packaging, using rootless, least privilege, capabilities minimized, non-writable root, MAC/seccomp and tight mounts. This is defense in depth, not replacement for a boundary.
3. Compare three candidate isolation runtimes on disposable hosts: KVM full VMs, Kata Containers (lightweight guest VM per pod), gVisor (userspace kernel and syscall interception). gVisor is **not** equivalent to a full VM; Kata's practical GPU/volume integration needs testing. Compare with hardened rootless containers as a baseline, not a foregone loser.
4. Treat LLM output, prompt-injected actions, tools, plugins, model artifacts, dependency updates and local process compromise as **untrusted**. Separate authorization, authentication, allowlisted operations, replay protection, action-specific approvals, immutable event logging and default-deny egress from the model's decision process.
5. Inference GPU is a major unverified boundary: evaluate PCIe IOMMU groups, VFIO/PCI passthrough limitations, DMA isolation and driver/firmware attack surface; never expose host GPU or Docker socket by blanket privileged mount. Prefer an inference-service API with minimal methods if it can satisfy throughput and confidentiality.
6. No shared writable host directories between trust domains by default. Treat virtio-fs, vsock, guest agents, backups, snapshots, hypervisor management and credential vaults as explicit interfaces requiring security review.
7. Fail closed for unexpected broker failure; verify that local/private services cannot use transitive routes through the internet-facing agent. Hold outbound privileged operations pending policy checks.
8. Preserve test reproducibility: versioned threat model and boundary matrix, synthetic-secret negative tests, clean restore drills, documented residual risks, signed evidence, separated author/assessor responsibilities and security regression tests.
9. **Commercial evidence:** make concrete, scoped claims ('under defined attack model, these negative tests passed on specified build') instead of 'secure', 'unhackable', 'certified' or 'Docker unsafe'. Independent assessment requires a defined scope; do not imply external auditors will reject Docker by default.

## Evidence and comparison questions
| Approach | Kernel boundary | Positive case | Open technical questions |
|---|---|---|---|
| Hardened rootless Docker/Podman | Shared host kernel | Low overhead, compatible runtimes | Kernel escape, dangerous mounts, host APIs, policy drift |
| Full KVM VM per trust domain | Separate guest kernel; host hypervisor | Clearer independent trust boundary | RAM/storage cost, host/guest management, GPU passthrough, backup lifecycle |
| Kata Containers | Guest kernel per sandbox/pod | OCI workflows plus virtualization | GPU, virtio-fs, vsock, operations and measurement |
| gVisor | Userspace application kernel | Reduced direct host syscall exposure | Syscall coverage, drivers/GPU access, inference compatibility, relative assurance |
| Separate physical servers | Hardware segmentation | Reduces shared-hypervisor blast radius | Cost, network trust, management credentials, synchronization |

## Required owner review gates
- [ ] Inventory **actual**, not merely proposed, components and their boundaries; confirm every guest/container, mount and route from sanitized evidence.
- [ ] Classify confidentiality and trust of each Hermes, model/runtime, Home Assistant, broker, backup and management workload.
- [ ] Measure on disposable testbed: startup/RAM/CPU/GPU token throughput, cold prefill, cross-VM communication, failure/recovery, shared resource leakage.
- [ ] Produce threat model with attacker capabilities and explicit limitations, including hypervisor/host and compromised-admin scenarios.
- [ ] Define minimal allowed cross-boundary API and test unauthorized calls, credential reads, egress paths and snapshot rollback.
- [ ] Obtain independent security review *after* implementation and reproducible internal test evidence, with customer-specific scope.
- [ ] Obtain owner's explicit approval before any live deployment or migration after the freeze deadline.

## Primary and authoritative references
1. NIST SP 800-190, **Application Container Security Guide** (2017): https://csrc.nist.gov/pubs/sp/800/190/final
2. NIST SP 800-125, **Guide to Security for Full Virtualization Technologies** (2011): https://csrc.nist.gov/pubs/sp/800/125/final
3. NIST SP 800-207, **Zero Trust Architecture** (2020): https://csrc.nist.gov/pubs/sp/800/207/final
4. NSA/CISA, **Kubernetes Hardening Guidance** (2022): https://www.nsa.gov/Press-Room/News-Highlights/Article/Article/2716980/nsa-cisa-release-kubernetes-hardening-guidance/
5. Docker official Engine security: https://docs.docker.com/engine/security/
6. gVisor, security model and design limitations: https://gvisor.dev/docs/architecture_guide/security/
7. Kata Containers, current virtualization architecture: https://kata-containers.github.io/kata-containers/design/virtualization/
8. Linux kernel, VFIO/IOMMU device isolation: https://docs.kernel.org/driver-api/vfio.html
9. CISA, Secure-by-Design principles: https://www.cisa.gov/securebydesign

**Interpretation notes:** NIST sources above are foundational guidance, not assessments of our deployment. Project documentation supplies mechanism descriptions, not independent certificates. CISA Kubernetes guidance does not prove that adopting Kubernetes creates a VM boundary. None of these references certifies CLARYEL.

## Relations
- #43: owner pause / authorization gate
- #32: detailed trust-boundary investigation
- #34: comparative platform study
- #29–31: recovery and evidence-related work

**Operational safety:** Public repo must not include private IPs, private repo contents, credentials, customer-specific topology, internal hostnames, or exploitable configuration details.
