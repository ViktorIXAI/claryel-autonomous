# How the video-card results are computed

(English translation; adopted as the working language of this note. The
original Russian note is preserved verbatim in the release asset
`ru-source-records-2026-11-01.tar.zst`, indexed in `logs/INDEX.md`.)

## Method
The `Runtime.evaluate` probe reads live page variables (`balls`, `angle`,
`HEX_RADIUS`, `CX`, `CY`, `fps`) every 0.8 s for 20 s. Checking whether a
ball is inside the hexagon uses half-plane intersection over the 6 edges in
the hexagon's local coordinate system (rotation by `-angle`); the normal sign
is calibrated at the hexagon center, so the vertex traversal order in
generated code cannot affect the verdict. The "center is inside" self-check
is mandatory: if it fails, the probe geometry is wrong and the verdict must
not be trusted.

## Spin constancy
We take `angle` from every snapshot, unwrap it modulo 2π, and compute
Δangle/Δt. That is the direct answer to the "constant angular velocity"
requirement — no trust in code comments.

## What counts as failure
- the animation does not change (canvas hash identical);
- there are not 12 balls;
- any ball is outside the hexagon in any snapshot;
- any console error or uncaught exception;
- any network request outside `file://`.

## No fixes are applied
Generated code is never edited. "Cheat" mechanisms found (clamping, ball
teleportation) are reported as part of the first-shot result.
