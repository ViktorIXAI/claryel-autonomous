# Passport MAC-STUDIO — high-memory comparison workstation
Live-collected 2026-11-01.

| field | value |
|---|---|
| role | mandatory paired duplicate for every adopted contour version (label `m`-suffixed files, `PARB_BOX=mac-studio`) |
| vendor/model | Apple Mac Studio, model id Mac15,14 |
| CPU | Apple M3 Ultra, 28 logical cores |
| memory | 274,877,906,944 B = 256 GiB unified |
| GPU | integrated (Metal); no discrete GPU |
| OS / kernel | macOS 27.2 (build 26B123), **desktop**, Darwin kernel 27.2.0; live check 2026-11-03 |
| serving engine | [Strata](https://github.com/Niko1221/Strata) repo v0.2.10, prebuilt Metal engine 0.1.56; text-only serve on :8080 (checked 2026-11-03) |
| model build | same IQ3_S GGUF build family; on-box copy path differs |
| external storage | WD Blue SN5000 2 TB NVMe SSD (PCI-Express, External, SMART Verified), one APFS volume (`2`, 935.2 GB used), mounted; briefly detached 2026-11-20 morning (~0.5–1.5 h, CHG-004) and re-attached hot the same day (CHG-005) — live check 2026-11-20 |

**Sensors:** temperature/power/VRAM-per-component ✖ `not_available` (Apple
silicon does not expose via the sampler) · memory via sysctl ✔. Cross-box
*quality* comparisons use this box; *speed/power* comparisons do not (sensor matrix differs).

**Drift history:** the drift-audit fingerprint tracks the external disk's
`/dev/diskN` node names, which macOS reassigns on every boot/power cycle —
boot 2026-11-02 exposed the drive as `disk4`/`disk5`, boot 2026-11-14 as
`disk6`/`disk7`, boot 2026-11-16 back to `disk4`/`disk5`, boot 2026-11-18 kept
`disk4`/`disk5` (no drift fired), boot 2026-11-20 again as `disk6`/`disk7`,
always the same WD Blue SN5000 2 TB drive (PCI-Express, External, SMART
Verified, live check 2026-11-20) and the same 2.0 TB layout with one APFS
volume. Unannounced power cycles also recorded 2026-11-15 (no numbering
change). Boot timestamps on this box are local Europe/Rome (CET). See
`hardware/changes/MACSTUDIO.md` CHG-001 (2026-11-14), CHG-002 (2026-11-16) and
CHG-003 (2026-11-20 early) — unannounced reboots with node renumbering, no
physical change. **2026-11-20 11:16/11:29 local boots (CHG-004): the external
disk lines left the fingerprint entirely — the drive stopped appearing on any
Thunderbolt/USB bus or in `diskutil list`, i.e. a real detach, not
renumbering.** **2026-11-20 ~11:44–12:48 local (CHG-005): the same WD Blue
SN5000 came back hot-plugged within the unchanged 11:29 boot, re-enumerated as
`disk4`/`disk5`, volume `2` intact at 935.2 GB used — the detach was reversed
without a reboot; whether it was operator action or an intermittent
interconnect remains an open maintainer question.**
