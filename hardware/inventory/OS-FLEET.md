# Fleet OS records

Checked: 2026-11-03, 13:16 CET.  
Source: `hardware/os-snapshots/2026-11-03.json`, collected by
`scripts/fleet/os_fleet_audit.py`.

The machine image must be recorded as `Ubuntu <version> <flavor> (<codename>)`
where flavor is **desktop** or **server**. Kernel alone is not sufficient:
Ubuntu Desktop and Ubuntu Server can report the same `24.04` version and
kernel while having different installed packages and network defaults.

| Machine | OS | Codename | Flavor | Kernel | Status |
|---|---|---|---|---|---|
| P2005 | Ubuntu 24.04.5 LTS | noble | **Desktop** | 7.0.0-38-generic | live |
| Mac Studio | macOS 27.2 | 26B123 | desktop | Darwin 27.2.0 | live |
| MacBook | macOS 27.2 | 26B123 | desktop | Darwin 27.2.0 | live |
| Mac mini | macOS 27.2 | 26B123 | desktop | Darwin 27.2.0 | live, no active Strata serve |
| P1005 | Ubuntu 24.04.5 LTS | noble | **Server** | 6.8.0-147-generic | last confirmed server earlier today; host currently unreachable |
| P3001 | Ubuntu 24.04.x LTS | noble | recheck required | 6.8.0-147-generic last recorded | offline |
| B2003 | Ubuntu 24.04.5 LTS | noble | **Desktop** | 7.0.0-38-generic | live |
| P3032 | Ubuntu 24.04.x LTS | noble | recheck required | 6.8 last recorded | offline |
| Hermes host (`claryel01`) | Ubuntu 24.04.5 LTS | noble | **Server** | 7.0.0-38-generic | live; xrdp present but GNOME is not installed |

## Classification rule

- `desktop`: Ubuntu Desktop metapackage is installed, or GNOME/desktop session
  and display manager are active.
- `server`: Ubuntu Server metapackage is installed and no Ubuntu Desktop
  metapackage is installed.
- `xrdp` alone does **not** make a Server installation into a Desktop
  installation.
- A machine is not recorded as Desktop/Server from hostname or physical
  location alone.

## Kernel policy

The kernel must be recorded because benchmark behavior changes across
Ubuntu 24.04 kernels. For the current fleet:

- P2005 and B2003 run the HWE-style `7.0.0-38-generic` kernel.
- P1005 runs `6.8.0-147-generic`.
- P3001/P3032 require live recheck after power-on before a new benchmark claim.

Do not infer kernel upgrades from a reboot. Re-run
`scripts/fleet/os_fleet_audit.py`, then compare the date-stamped JSON snapshot.

## Required fields in logs

Gate results and gate ledgers contain an `os` object. Telemetry headers contain
the same object. Every machine record must include:

```text
os.id
os.pretty
os.version
os.codename
os.flavor
os.flavor_evidence
os.kernel
os.architecture
os.hostname
```

These fields are mandatory for benchmark reproducibility and for tracking the
planned Ubuntu Desktop → Server migration and a future Ubuntu 26.04 migration.
