# Issue #25 evidence addendum — tavern camera and relay (2026-11-21 UTC)

**Scope:** documentation-only provenance clarification at repository HEAD `02b4dca7106f018da7942095d9a4307f36976886`. This is an audit of repository-reported observations, **not** an independent Home Assistant replay, hardware diagnosis, or permission to modify automation. Preserve the original [2026-11-20/21 field note](../docs/taverna-camera-and-ghost-on-2026-11-20.md) and its Git history.

## Observations versus interpretations

| Evidence / version | What is supported | What is not established |
|---|---|---|
| [85c7ec0](https://github.com/ViktorIXAI/claryel-autonomous/commit/85c7ec095d59a432adb491711c66800ee08340a0) | Reported dark-frame YAVG 32.4–34.9 and lamp-on YAVG 133–145 under tested framing/conditions | Universal night-vision failure threshold or performance in other lighting |
| [32deb47](https://github.com/ViktorIXAI/claryel-autonomous/commit/32deb47ea31cc0a9f3e78f3f1a7e82dd365c972a) | Corrected attribution: a person was present in the illuminated scene | The 03:51 motion event was triggered solely by the light transition; the earlier causal reading is superseded |
| [44a4b02](https://github.com/ViktorIXAI/claryel-autonomous/commit/44a4b0212e2f81ed38a32141d324a29c62495e6b) | Reported recovery after a relay-unavailable interval, with RSSI and connection state on recovery | A single confirmed root cause for the outage or proof that no LAN mode could ever work |
| [02b4dca](https://github.com/ViktorIXAI/claryel-autonomous/commit/02b4dca7106f018da7942095d9a4307f36976886) | Four reported unavailable transitions within the observation window, including transitions with relatively strong reported RSSI | The categorical inference that radio conditions are *not* a cause; RSSI samples alone do not exclude intermittent interference, packet loss, device faults, cloud/API or integration failures |

## Provenance and next verification

The above commits are **successive revisions to one dated field note**, not four independently reproduced experiments. The field note's earlier causal statements remain accessible through the linked commits. Treat the revised explanation as a later interpretation, not a silent correction to the underlying historical observation. A controlled follow-up should preserve event timestamps with timezone, source (HA state history vs physical observation), relay RSSI/connection timestamps, cloud/API errors, integration reload times, camera illumination state, and a clear distinction between observation and hypothesis. Sanitize device identifiers, credentials, URLs with tokens and private local paths before publication.

This addendum does not modify production scripts, Home Assistant, security policies, frozen benchmarks, or the original field note. Issue #25 remains **OPEN**: full inventory, independent QA, current GitHub metadata verification, and final-HEAD docs/link/security CI evidence are still missing. The available commit-workflow lookup only covers PR-triggered runs; empty results cannot certify push CI.
