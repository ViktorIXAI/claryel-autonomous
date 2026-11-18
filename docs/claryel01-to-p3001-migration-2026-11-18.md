# Moving the CLARYEL01 workload to P3001 — feasibility, what transfers, what does not

Written 2026-11-18 from the live passport `hardware/inventory/CLARYEL01.md` (claryel01, this
Hermes host) and `hardware/inventory/P3001.md` (HP Z420, Xeon E5-2697 v2, 62 GiB, 240 GB SATA +
1 TB NVMe, K620 + RX 580, **powered off since the 2026-11-12 GPU-drift incident**, did not answer
ICMP on 2026-11-18).

## Verdict

The whole software stack is portable: both boxes run Ubuntu 24.04, Docker + compose, the same
users, the same bind-mount layout under `/srv/claryel`. The blockers are physical, not software:

| # | blocker | why | decision taken |
|---|---|---|---|
| 1 | Capacity | live data **≈1.2 TB** (hot 308 GB, warm 189, backup 410, archive 121, plus 138 GB of `/` including 79 GB of docker images and 27 GB of build cache, `~/.hermes` 9.6, `~/CLARYEL` 6) against P3001's 240 GB SATA (72 % used) + 1 TB NVMe (200 GiB already used by the Strata pack and the accounts' homes) | apps move to P3001; **the 18.2 TB SAS backup array stays on claryel01 and is served to P3001 over NFS** (stage 2). The physical HBA+disk move becomes optional stage 3 |
| 2 | Hot tier cannot be lifted | the 4 × Lexar NM1090 sit behind **Intel VMD (`8086:ad0b`)** on the ASUS Q870M-C; the Z420 has no M.2 and its PCIe lanes are already occupied by the K620 + RX 580 | P3001's hot tier = its own 1 TB FireCuda NVMe (measured 2.50 GB/s by the engine) |
| 3 | SAS array move is a cabling job | the HBA is an OEM **Inspur 12G SAS3008IT** (LSI SAS3008, `1000:0097`, slot `83:00.0`); the two 20 TB drives are **point-to-point** behind it (no expander, no SES enclosure) | needs a free PCIe x8 slot + one SFF-8643 → 4×SATA breakout (2 ports used) + 2× SATA power + drive brackets. `mdadm` reassembles by UUID/LABEL, but md0's on-disk name is `ubuntu-server:0` while md1/md2 are `claryel01:1/2` — the mdadm.conf ARRAY lines must be regenerated on the target, not copied blindly |
| 4 | CPU instruction set | the E5-2697 v2 is Ivy-Bridge-EP: **no AVX2** | API-layer services (LibreChat, LiteLLM, agent-fabric, integrations, ERPNext, Odoo, OpenProject, Postgres, MariaDB, Mongo, Qdrant, Meilisearch, SeaweedFS, Valkey, Mosquitto, HA) are unaffected in principle; anything llama.cpp/Ollama-based will run badly on that CPU — the Hermes brain is remote (P2005/Basalt) so this is acceptable. **Must be proven per image at first start**, because SIMD builds (vector-search engines in particular) can refuse to start on a non-AVX2 CPU — see stage 1 pre-flight |
| 5 | Host identity is baked into jobs and integrations | 40 Hermes cron jobs, several named after this box (`claryel01: сторож…`, `Столы: Chrome…`, `Проверка стола…`), fleet station id `claryel-it-home-001`, NetBird enrollment, cloudflared tunnel tokens (`/etc/claryel/*`, root), xrdp/VNC sessions, SSH host keys, DHCP/MAC reservations, `claryel-control-primary-bind` (the fleet git primary lives in `~/CLARYEL/git-primary`) | stage 0 pauses the source-side crons, stage 1 re-pins identity per service |

## Device move list (the user's list, with the exact contract for each)

| device | on claryel01 today | what has to happen on P3001 |
|---|---|---|
| Zigbee coordinator (CH340 `1a86:7523`, TI CC2652 ZNP) | `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` → mounted as `/dev/ttyUSB0` by the generated `/srv/claryel/config/compose.zigbee.yaml` | same stick → same by-id string on any Linux host, so the generated override transfers unchanged; **no device re-pairing, ZHA network and `zigbee.db` keep working**. Re-run the reconciler so it regenerates the override on the new host |
| Webcam (`32e6:9251`) | `/dev/video0`, used exclusively by `motion-tavern.service` | plug into a USB 2/3 port, install the unit + hook + config from `scripts/tavern-motion/`, give the service `video` access, regenerate the HA token; the same MJPEG/YUYV mode table applies (no 320x240) |
| UPS (MGE `0463:0001`, USB HID) | `nut-server` + `nut-monitor` + `nut-driver@claryel-ups`, live and healthy (`battery.charge 100`, `battery.runtime 7200`) | only one box may own the USB cable. If claryel01 stays as the storage node, **keep the UPS there** and make P3001 a `upsmon` slave of `upsd` on claryel01; if everything moves, copy `/etc/nut/{ups,upsd,upsmon}.conf` (root-only today) and re-enrol the driver. NUT port 3493 must be reachable between the two boxes |
| SAS HBA + 2 × 20 TB | `83:00.0` SAS3008, `md0` RAID1 (on-disk name `ubuntu-server:0`, UUID `34c2cc42:2d9329f4:86f627d6:23009f3e`, LABEL `CLARYEL_SAS_BACK`) → `/srv/claryel/backup` | stage 3 only. Cold move of **both** members + the card; then `mdadm --assemble --scan` and mount by LABEL; verify `cat /proc/mdstat`, `smartctl -H`, and re-point the HA/ERPNext backup crons. Never move one member |
| NVMe pool (4 × Lexar) | md1 RAID0 (hot, 308 GB) + md2 RAID10 (warm, 189 GB) + OS on `nvme3n1` | stays on claryel01 (VMD-bound). Its hot and warm payloads are **copied** to P3001's NVMe (308 + 189 GB fits the 1 TB FireCuda), not moved |
| Bluetooth, keyboard/mouse | `8087:0037`, HID | stay or be replaced; nothing depends on them |

## Stage plan

**Stage 0 — prerequisites (blocks everything): power P3001 back on.** It has been de-energised
since 2026-11-12; until it answers SSH, no measured plan exists. Then re-inventory it live
(`lspci -nnk`, free PCIe slots, `nvme list`, `ethtool eno1`, `dmidecode -t memory`) and update
its passport. Also fix the GPU situation there or accept a display-only box.

**Stage 1 — move the software, no hardware moves.**
1. Pre-flight on P3001: `docker run --rm` each of the 38 active images and record which ones start
   on a non-AVX2 CPU; anything that refuses gets pinned to a compatible tag *before* the cutover.
2. Backups are already current: HA nightly to `/srv/claryel/backup/homeassistant` (cron
   `1543ceb6ca6d`), plus fresh dumps of MariaDB (ERPNext), Postgres (Odoo, claryel-box, openbot),
   Mongo, Qdrant/Meilisearch snapshots, SeaweedFS volume list.
3. Copy in this order: `/etc/docker`, `/srv/claryel/{config,src,platform,runtime}`,
   `/home/viktor/CLARYEL`, `/home/viktor/.hermes` (9.6 GB: profiles, skills, cron `jobs.json`,
   `.env` secrets — permissions 700, never through a shared repo), then `~/sah-main`.
   ~1.2 TB at 1 GbE ≈ 6–9 h; use `rsync -aHAX --info=progress2` and do it twice (the second pass
   is the diff).
4. Bring the compose projects up one at a time (`claryel-box`, `erpnext-np`, `odoo`), then
   `homeassistant` **without** the Zigbee stick attached, restore the HA backup, then attach the
   stick and let ZHA take over. Watch `docker logs` for the SIMD/AVX refusals from step 1.
5. Hermes: `~/.hermes` moves wholesale; start `hermes-gateway` + `hermes-dashboard` user services,
   re-login NetBird, re-issue SSH keys, then re-enable the cron jobs one by one and rewrite the
   ones whose text names the old machine.
6. Move the webcam (motion unit), then decide the UPS ownership (see the table).

**Stage 2 — storage without unplugging the array.** Export `/srv/claryel/backup` from claryel01
over NFS (root-squash, LAN-only, hosts allow P3001 only) and mount it on P3001 at the same path.
Backup jobs then write to the same label through the network. Add the inverse for the hot tier if
anything still needs it, but do **not** run a hot/database tier over 1 GbE.

**Stage 3 — optional physical move** (only when claryel01 is being retired): cold, both disks +
the card, one bracket/cable order first, `mdadm --assemble --scan`, `fsck`, SMART re-check, then
move the NFS export role to P3001 and demote claryel01 to spare.

## Rollback

claryel01 is never wiped during stages 1–2: crons are paused (not deleted), its compose projects
are stopped but kept, and the array never leaves it. Cutover is a name/DHCP swap; rolling back is
starting the same projects again on claryel01.

## Root-only gaps still open in the passport

`dmidecode -t memory` (DIMM parts), `smartctl -H` on all 7 disks, `vgs`/`dmsetup`,
`/etc/nut/*`, `/srv/claryel/config/compose.station.yaml`, `/etc/claryel/*` (tunnel tokens),
`journalctl -b` boot warnings. To close them in one paste, run
`sudo bash -c 'dmidecode -t memory -t baseboard; smartctl -H /dev/{sda,sdb,nvme0n1,nvme1n1,nvme2n1,nvme3n1,nvme4n1}; cat /proc/mdstat; vgs; cat /etc/nut/ups.conf /etc/nut/upsmon.conf; grep -h TOKEN /etc/claryel/* 2>/dev/null >/dev/null; echo done'`
and the output can be appended to the passport (secrets stay out of the repo).
