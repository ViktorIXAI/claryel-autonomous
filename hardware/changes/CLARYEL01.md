# Change ledger CLARYEL01 (the Hermes desk host)

## CHG-000 — passport opened, migration to P3001 proposed (2026-11-18)

Status: **proposed / not applied**. No hardware was moved, no service was stopped.

Collected the first full passport of this node: `hardware/inventory/CLARYEL01.md`
(hardware, storage topology with md0/md1/md2 + the LSI SAS3008 HBA, USB devices with their
stable names, host services, 3 compose projects and 38 running services, Hermes footprint).

Planned migration of the workload to P3001: `docs/claryel01-to-p3001-migration-2026-11-18.md`.
Decision recorded there: apps move first (stage 1), the 18.2 TB SAS backup array stays on this
box and is served over NFS (stage 2), the physical HBA + 2x20 TB move is optional stage 3 and
requires a PCIe x8 slot, an SFF-8643 breakout cable and drive brackets.

Blocker for every stage: P3001 is de-energised (no ICMP on 2026-11-18); it must be powered on and
re-inventoried before any copy starts.

Open root-only fields in the passport (DIMM parts, SMART health, `/etc/nut/*`, station compose,
tunnel tokens) are listed at the bottom of the passport for one owner-side paste.
