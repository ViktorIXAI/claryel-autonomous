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

## CHG-002 — unannounced hardware change detected (2026-11-16 09:43 UTC, status: detected)

**Trigger:** the hourly fleet drift audit (`hw-fingerprint` probe script)
reported a fingerprint change for MACSTUDIO. No operator-announced change existed.

**Monitor diff (fingerprint, previous → current, verbatim):**

```diff
  3,4c3,4
  <    1:                        EFI EFI                     209.7 MB   disk6s1
  <    2:                 Apple_APFS Container disk7         2.0 TB     disk6s2
  ---
  >    1:                        EFI EFI                     209.7 MB   disk4s1
  >    2:                 Apple_APFS Container disk5         2.0 TB     disk4s2
```

(RAM line `274877906944` B = 256 GiB and the `Apple M3 Ultra` GPU line are
identical in both fingerprints; only the two external-storage node-name lines
moved — exactly the inverse of the CHG-001 shift.)

**Diagnosis (live re-inventory over SSH, 2026-11-16 09:44 UTC): no physical
change — the box power-cycled again and macOS renumbered the external disk
nodes back to their pre-2026-11-14 numbering.**

| item | previous fingerprint | current fingerprint |
|---|---|---|
| boot producing it | boot chain 2026-11-14 08:50 → 2026-11-15 08:09 local | 2026-11-16 08:59:15 UTC (`kern.boottime`) |
| external 2 TB NVMe node | `disk6` (+ APFS container `disk7`) | `disk4` (+ container `disk5`) |
| drive identity | WD Blue SN5000 2TB, PCI-Express, SMART Verified (CHG-001 read) | WD Blue SN5000 2TB, PCI-Express, External, SMART Verified — identical |
| layout | 2.0 TB GUID, 209.7 MB EFI, one full-size APFS container | byte-identical |

- `last reboot` shows two further unannounced power cycles since CHG-001:
  2026-11-15 08:09 and 2026-11-16 09:59 local (08:59:15 UTC). The 2026-11-15
  boot kept the `disk6`/`disk7` enumeration (no drift fired that day); the
  2026-11-16 boot re-enumerated the same drive as `disk4`/`disk5`.
- Same failure mode as CHG-001 and P2005 CHG-001: the fingerprint probe
  captures `/dev/diskN` node names, not drive serials, so every power cycle
  that changes attach order reads as drift.
- Serve on :8080 answered HTTP 200 at the 09:44 UTC check — the serving
  endpoint is up after the reboot.

**Impact: none detected.** No measurable hardware moved (identical RAM total,
identical GPU line, identical drive identity and 2 TB layout). Benchmark
comparison not applicable; no cold-ladder or contour re-run required.

**Open maintainer decision:** the 2026-11-15 and 2026-11-16 reboots were not
announced to the ledger. Nothing on the box was touched beyond read-only
inspection.

**Passport:** drift-history note in `hardware/inventory/mac-studio-m3u.md`
extended with the 2026-11-16 boot.

## CHG-003 — unannounced hardware change detected (2026-11-20 03:13 UTC, status: detected)

**Trigger:** the hourly fleet drift audit (`hw-fingerprint` probe script)
reported a fingerprint change for MACSTUDIO. No operator-announced change existed.

**Monitor diff (fingerprint, previous → current, verbatim):**

```diff
  3,4c3,4
  <    1:                        EFI EFI                     209.7 MB   disk4s1
  <    2:                 Apple_APFS Container disk5         2.0 TB     disk4s2
  ---
  >    1:                        EFI EFI                     209.7 MB   disk6s1
  >    2:                 Apple_APFS Container disk7         2.0 TB     disk6s2
```

(RAM line `274877906944` B = 256 GiB and the `Apple M3 Ultra` GPU line are
identical in both fingerprints; only the two external-storage node-name lines
moved — the same shift CHG-001 recorded, i.e. back to the 2026-11-14 numbering.)

**Diagnosis (live re-inventory over SSH, 2026-11-20 03:29 UTC): no physical
change — the box power-cycled again and macOS renumbered the external disk
nodes.**

| item | previous fingerprint | current fingerprint |
|---|---|---|
| boot producing it | 2026-11-16 09:59 local (= 08:59 UTC, per CHG-002) | 2026-11-20 03:55:43 local CET (`kern.boottime`; `last reboot` line `Nov 20 03:55`) |
| external 2 TB NVMe node | `disk4` (+ APFS container `disk5`) | `disk6` (+ container `disk7`) |
| drive identity | WD Blue SN5000 2TB, PCI-Express, External, SMART Verified | `WD Blue SN5000 2TB`, PCI-Express, Solid State: Yes, External, SMART Verified — identical |
| layout | 2.0 TB GUID, 209.7 MB EFI, one full-size APFS container | byte-identical (`disk7s1`, volume `2`, mounted) |

- The box was **up 34 minutes** at the 03:29 UTC check, matching a
  2026-11-20 03:55:43 local (Europe/Rome) boot — an unannounced power cycle.
- `last reboot` shows one further unannounced power cycle since CHG-002:
  2026-11-18 13:12 local. That boot kept the `disk4`/`disk5` enumeration
  (identical fingerprint, no drift fired), and the drift probe is silent while
  the box is offline, so the 2026-11-18/19 power state produced no record —
  only the 2026-11-20 re-enumeration reached the ledger.
- Same failure mode as CHG-001, CHG-002 and P2005 CHG-001: the probe captures
  `/dev/diskN` node names, not drive serials, so a power cycle that changes
  attach order always reads as drift. This is the third such hit on the same
  physical drive.
- Timezone note for the ledger: MACSTUDIO's `last reboot` / boot timestamps are
  local Europe/Rome (CET); only values converted on purpose are UTC.

**Impact: none detected.**
- Serve on :8080 answered HTTP 200 at the 03:29 UTC check — the serving
  endpoint is up after the reboot.
- External volume present and mounted (`disk7s1`, 2.0 TB container,
  1.1 TB free); SMART Verified.

**Benchmark comparison:** not applicable — no measurable hardware moved
(identical RAM total, identical GPU line, identical drive identity and 2 TB
layout). No cold-ladder or contour re-run required for this entry.

**Open maintainer decision:** the 2026-11-18 13:12 local and 2026-11-20 03:55
local reboots were not announced to the ledger. Nothing on the box was touched
beyond read-only inspection.

**Passport:** drift-history note in `hardware/inventory/mac-studio-m3u.md`
extended with the 2026-11-18 and 2026-11-20 boots.

## CHG-004 — unannounced hardware change detected (2026-11-20 10:42 UTC, status: detected)

**Trigger:** the hourly fleet drift audit (`hw-fingerprint` probe script)
reported a fingerprint change for MACSTUDIO. No operator-announced change existed.

**Monitor diff (fingerprint, previous → current, verbatim):**

```diff
  3,4d2
  <    1:                        EFI EFI                     209.7 MB   disk6s1
  <    2:                 Apple_APFS Container disk7         2.0 TB     disk6s2
```

(RAM line `274877906944` B = 256 GiB and the `Apple M3 Ultra` GPU line are
identical in both fingerprints; both external-storage lines are **gone** from
the current fingerprint — unlike CHG-001/002/003 this is not a node renaming:
the external disk is no longer enumerated at all.)

**Diagnosis (live re-inventory over SSH, 2026-11-20 10:44 UTC): the external
2 TB NVMe drive has been physically detached — this is the first MACSTUDIO
drift with a real hardware delta.**

| item | previous fingerprint (ack 2026-11-20 03:13 UTC) | current fingerprint |
|---|---|---|
| external disk lines | present: `disk6s1` EFI 209.7 MB + `disk7` APFS container 2.0 TB | absent — `diskutil list` shows only the internal 2.0 TB disk |
| drive bus visibility | WD Blue SN5000 2TB enumerated (External, SMART Verified) | not on Thunderbolt (all 5 ports `Status: No device connected`), not on USB (no mass-storage driver instances; only a "USB Receiver" HID dongle on the bus) |
| boot producing each state | 2026-11-20 03:55 local (drive present) | 2026-11-20 11:29:31 local (`kern.boottime`; `last reboot` also shows an 11:16 local boot) — both CET |
| RAM / GPU lines | 256 GiB / Apple M3 Ultra | identical |

- The drive was last seen enumerated at the 03:55 local boot (CHG-003
  confirmed its identity and layout). Two further unannounced power cycles
  followed (2026-11-20 11:16 and 11:29 local); the 11:29 boot came up with the
  drive absent from every bus, so the detach happened between 04:13 and
  11:42 local on 2026-11-20 — announced to no ledger.
- `/Volumes` now contains only the system volume; the external APFS volume
  (previously mounted, 1.1 TB free of 2.0 TB) is not present.
- The detach cause (operator unplug vs. enclosure/cable/drive failure) is not
  distinguishable remotely — the bus reports nothing attached.

**Impact:**
- 2 TB of external storage (~0.9 TB previously used) is offline; what was on
  that volume and where its consumers now read from is an open maintainer
  question.
- Serve on :8080 answered HTTP 200 at the 10:44 UTC check (user-space python
  listener) — the serving endpoint does not depend on the detached volume.
- The internal data volume measured 1.6 TiB used of 1.8 TiB (88 %) at the same
  check — capacity is a maintainer call, flagged not acted on.

**Benchmark comparison:** not applicable — the change removes a storage device
that carries no benchmark fixtures or serving artifacts recorded in this repo;
no suite baseline is affected by the detach itself. Re-run only if a suite is
found to read from that volume.

**Open maintainer decision:** why the external drive left the box (unplugged,
enclosure failure or drive failure) and whether its ~0.9 TB of content is
recoverable; the 11:16 and 11:29 local power cycles were likewise unannounced.
Nothing on the box was touched beyond read-only inspection.

**Passport:** `hardware/inventory/mac-studio-m3u.md` external-storage row and
drift-history note updated to the detached state.

## CHG-005 — unannounced hardware change detected (2026-11-20 11:48 UTC, status: detected)

**Trigger:** the hourly fleet drift audit (`hw-fingerprint` probe script)
reported a fingerprint change for MACSTUDIO. No operator-announced change existed.

**Monitor diff (fingerprint, previous → current, verbatim):**

```diff
  2a3,4
  >    1:                        EFI EFI                     209.7 MB   disk4s1
  >    2:                 Apple_APFS Container disk5         2.0 TB     disk4s2
```

(RAM line `274877906944` B = 256 GiB and the `Apple M3 Ultra` GPU line are
identical in both fingerprints; both external-storage lines are **back** in
the fingerprint — the inverse delta of CHG-004, where they left.)

**Diagnosis (live re-inventory over SSH, 2026-11-20 11:50 UTC): the detached
external 2 TB NVMe has been re-attached — the CHG-004 detach is reversed and
the drive is present again on the bus.**

| item | previous fingerprint (ack 2026-11-20 11:42 UTC, CHG-004) | current fingerprint |
|---|---|---|
| external disk lines | absent — drive not enumerated on any bus | present: `disk4s1` EFI 209.7 MB + `disk5` APFS container 2.0 TB |
| drive identity | not visible (detached) | `WD Blue SN5000 2TB`, PCI-Express, External, Solid State: Yes, SMART Verified — same physical drive as CHG-001..004 |
| layout / content | n/a | 2.0 TB GUID, one APFS container, volume `2` **935.2 GB used** — byte-for-byte the volume-usage figure read at CHG-001, contents intact and mounted |
| boot producing it | 2026-11-20 11:29:31 local | **unchanged** — `kern.boottime` still 2026-11-20 11:29:31 local, `uptime` 1h21m at the 11:50 UTC check |

- The re-attach is a **hot-plug within the same boot**: no new reboot appears
  in `last reboot` after the 11:29 local boot that CHG-004 recorded. The
  attach window is bounded by CHG-004's live check (10:44 UTC, drive absent)
  and this probe (11:48 UTC, drive present) — i.e. between 11:44 and 12:48
  local on 2026-11-20.
- The drive came back with the `disk4`/`disk5` enumeration (the numbering
  this box shows on most boots; CHG-001/002 recorded it) — node naming, not
  a second drive.
- Cause of the original detach is still not determinable remotely: an
  operator unplug-then-replug and an intermittent cable/enclosure/port
  failure produce the same fingerprint trail. If it was intermittent, the
  volume can drop again on the next power cycle — open maintainer question.

**Impact: none remaining.**
- Serve on :8080 answered HTTP 200 at the 11:50 UTC check — unchanged.
- External volume mounted again at `/Volumes/2` (935.2 GB used of 2.0 TB);
  the CHG-004 storage outage window was ~0.5–1.5 h with no recorded consumer
  of that volume in this repo.
- Internal data volume measured 1.6 TiB used of 1.8 TiB (88 %) again — same
  figure as CHG-004, still a maintainer call, not acted on.

**Benchmark comparison:** not applicable — re-attaching a storage device that
carries no benchmark fixtures or serving artifacts changes no suite baseline;
no cold-ladder or contour re-run required for this entry.

**Open maintainer decision:** whether the 2026-11-20 detach→re-attach was
intentional (operator responding to the drift alert) or an intermittent
interconnect; if the latter, the cable/enclosure should be checked before the
next power cycle. Nothing on the box was touched beyond read-only inspection.

**Passport:** `hardware/inventory/mac-studio-m3u.md` external-storage row and
drift-history note updated to the re-attached state.
