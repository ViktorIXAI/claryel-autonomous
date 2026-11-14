# MACSTUDIO configuration change ledger

Every hardware or serving-stack change to this box gets an entry here: date,
what changed, the pinned before/after state, and the benchmark comparison
(when a change touches measurable hardware). This ledger was opened by the
first drift-audit hit on the box; earlier states are documented in
`hardware/inventory/mac-studio-m3u.md` (passport, live-collected 2026-11-01).

## CHG-001 — unannounced hardware change detected (2026-11-14 08:53 UTC, status: detected)

**Trigger:** the hourly fleet drift audit (`hw-fingerprint` probe script)
reported a fingerprint change for MACSTUDIO. No operator-announced change existed.

**Monitor diff (fingerprint, previous → current, verbatim):**

```diff
  274877906944
  (U) Apple M3 Ultra
-    1:                        EFI EFI                     209.7 MB   disk4s1
-    2:                 Apple_APFS Container disk5         2.0 TB     disk4s2
+    1:                        EFI EFI                     209.7 MB   disk6s1
+    2:                 Apple_APFS Container disk7         2.0 TB     disk6s2
```

(RAM line `274877906944` B = 256 GiB and the `Apple M3 Ultra` GPU line are
identical in both fingerprints; only the two external-storage node-name lines moved.)

**Diagnosis (live re-inventory over SSH, 2026-11-14 07:53 UTC): no physical
change — the box power-cycled and macOS renumbered the external disk nodes.**

| item | previous boot | current boot |
|---|---|---|
| boot time | 2026-11-02 05:44 UTC (per `last reboot`) | 2026-11-14 08:50:55 UTC (`kern.boottime`) |
| external 2 TB NVMe | `disk4` (+ APFS container `disk5`) | `disk6` (+ container `disk7`) |
| drive identity | 2 TB NVMe SSD, PCI-Express, SMART Verified | `WD Blue SN5000 2TB`, PCI-Express, SSD, SMART Verified |
| APFS volume | ~2 TB container | `2`, 935.2 GB used, mounted |

- The uptime check at 07:53 UTC showed the box **up 3 minutes**: it rebooted at
  08:50:55 local (07:50:55 UTC), roughly two minutes before the drift probe ran.
  The previous boot went back to 2026-11-02. No reboot was announced.
- macOS assigns `/dev/diskN` node names by enumeration order at attach/boot
  time — the same physical drive gets a new number after a power cycle. Both
  fingerprints describe a 2.0 TB GUID scheme with a 209.7 MB EFI partition and
  one full-size APFS container; capacity is byte-identical.
- The fingerprint probe captures node names, not drive serials, so this class
  of power-cycle renumbering always reads as drift (same failure mode already
  documented for P2005 CHG-001 on 2026-11-13).

**Impact: none detected.**
- Serve on :8080 answered `401` (key-gated) at the 07:53 UTC check — the
  serving endpoint is back after the reboot.
- External volume present and mounted; SMART Verified.

**Benchmark comparison:** not applicable — no measurable hardware moved
(identical RAM total, identical GPU line, identical 2 TB external capacity).
No cold-ladder or contour re-run is required for this entry.

**Open maintainer decision:** the 2026-11-14 07:50:55 UTC reboot was not
announced to the ledger. Nothing on the box was touched beyond read-only
inspection.

**Passport:** `hardware/inventory/mac-studio-m3u.md` gains an external-storage
row (previously absent) and a drift-history note.
