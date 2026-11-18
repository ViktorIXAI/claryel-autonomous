# Passport CLARYEL01 — the desktop that runs Hermes, the business stack and the storage array

Live-collected 2026-11-18 as an unprivileged user (`viktor`); fields that require root are
marked `not_recorded (needs root)` rather than guessed. Commands used are listed at the bottom.
Collected because the operator asked for a full hardware/software/device passport as the basis
for moving the workload to P3001 (`hardware/inventory/P3001.md`).

| field | value |
|---|---|
| role | the operator's desk machine: Hermes Agent host (gateway, dashboard, 40 cron jobs, 10 profiles), CLARYEL business stack (ERPNext, Odoo, OpenProject, knowledge/agent-fabric, LibreChat, LiteLLM, ActivePieces, SeaweedFS, Qdrant, Mongo, Postgres, Mosquitto, Ollama), Home Assistant, NUT, remote desktop, and the fleet's backup/warm/archive storage tiers |
| station id (fleet) | `claryel-it-home-001` (see `/srv/claryel/src/claryel-fleet`) |
| vendor/model | ASUS **Pro Q870M-C** (DMI `board_name`, sys_vendor `ASUS`), product_name `System Product Name` (unnamed), BIOS 3020 dated 2026-04-28 |
| CPU | Intel **Core Ultra 7 270K Plus**, 24 cores / 24 threads, 0.8–5.5 GHz, AVX2+ (kernel `7.0.0-43-generic`) |
| iGPU | Intel Arrow Lake integrated graphics (`8086:7d67`) — **no discrete GPU on this box** |
| NPU | Intel Arrow Lake NPU (`8086:ad1d`) present on the board, no Linux driver bound — nothing uses it |
| audio | card 0 HDA Intel PCH (`8086:7f50`), card 1 = the webcam's microphone (`snd_usb-audio`) |
| RAM | 30 GiB usable (single-socket DDR5, DIMM parts `not_recorded (needs root: dmidecode)`) |
| swap | 256 GiB LV `claryel-hot-vg/swap` (prio 100, ~6.8 GiB in use) + 32 GiB file `/srv/claryel/archive/.claryel-emergency.swap` |
| OS | Ubuntu **24.04.5 LTS desktop** flavour (noble), x86-64, `graphical.target` + GNOME snap + xrdp, Secure Boot `not_recorded`, clock local (CET) |
| kernel | running **7.0.0-43-generic** (`linux-generic-hwe-24.04` 7.0.0-43.43~24.04.1, HWE stack) while the GA meta `linux-image-generic` 6.8.0-149 is also installed — the target box must be pinned to the same HWE stack, otherwise the `v4l2loopback` DKMS module and the camera/audio plumbing will not build |
| users | `viktor` uid 1000 (groups: sudo, docker, video, lxd, claryel, claryel-rdp, claryel-vnc), `claryel-ai` uid 1001 (browser-desktop services) |
| network | wired `enp128s31f6` Intel `8086:550c` (e1000e) **1 GbE**, carrier up; Wi-Fi chip present (`iwlwifi`) but no wireless interface is exposed; NetBird mesh client active; Docker bridges `172.17/19/22/23/30` |
| boot | UEFI + GRUB (`/boot/grub/grub.cfg`, 15 entries), EFI system partition on `nvme3n1p1` |

## Storage topology

| device | model / serial | size | role |
|---|---|---|---|
| `nvme3n1` | Lexar NM1090 PRO 2TB `QG4464R000289P3200` | 1.9 TB | **system**: p1 EFI (1 GB) + p2 `/` (196 GB, 74 % used); its p4 is also an md2 member |
| `nvme1n1` `nvme2n1` `nvme3n1` `nvme4n1` | Lexar NM1090 PRO 2TB ×4 (serials `...036`, `...201`, `...289`, `...843`) | 2.05 TB each | striped/partitioned pool |
| → `md1` | RAID0 over `nvme2n1p1 nvme3n1p3 nvme1n1p1 nvme4n1p1` | 2.4 TB | `LVM2_member` → VG `claryel-hot-vg` → LV `data` mounted `/srv/claryel/hot` (**308 GB used**), LV `swap` |
| → `md2` | RAID10 over `nvme3n1p4 nvme2n1p2 nvme1n1p2 nvme4n1p2` | 2.2 TB | ext4 `/srv/claryel/warm` (**189 GB used**) |
| `nvme0n1` | Samsung 990 PRO 2TB `S7HENL0L306707Z` | 2.0 TB | p3 ext4 → `/srv/claryel/archive` (**121 GB used**) |
| `sda` | WDC **WUH722020BL5204** 20 TB SAS `9BKDPMPL` | 18.2 TiB | md0 member |
| `sdb` | Seagate **ST20000NM007H** 20 TB SAS `ZYD970GN` | 18.2 TiB | md0 member |
| → `md0` | RAID1 (`sda[0] sdb[1]`, super 1.2, bitmap, 146 bitmap pages) | 18.2 TB | ext4 `LABEL=CLARYEL_SAS_BACK` → `/srv/claryel/backup` (**410 GB used**) |
| HBA for `sda`/`sdb` | **Broadcom/LSI SAS3008 Fusion-MPT SAS-3** (`1000:0097`), Inspur 12G SAS3008IT subsystem (`1bd4:000c`), slot `83:00.0`, driver `mpt3sas` | — | the two 20 TB drives are the only devices behind it (`lsscsi` bus `[8:0:0:0]`, `[8:0:1:0]`) |
| Intel VMD | `8086:ad0b` (driver `vmd`) | — | the NVMe pool is behind Intel Volume Management Device — **NVMe enumeration on another board will differ** |

Health: `smartctl -H` for all seven block devices `not_recorded (needs root)`; `smartmontools`,
`mdmonitor`, `multipathd`, `rasdaemon` are enabled and running. Total on-data (df/du, 2026-11-18):
**~1.2 TB** — data tiers hot 308 GB + warm 189 + backup 410 + archive 121; `/` itself 138 GB used
and it holds `/var/lib/docker` (images 79.3 GB, build cache 27.2 GB, containers 14.3 GB, volumes
5.9 GB); `~/.hermes` 9.6 GB, `~/CLARYEL` 6.0 GB, `/srv/claryel/src` 7.0 GB, `~/sah-main` 0.15 GB.

## External / USB devices (what has to be physically re-plugged)

| device | id | device node | who consumes it |
|---|---|---|---|
| UPS | `0463:0001` MGE UPS Systems (Bus 001 Dev 006, HID) | via libusb | **NUT is live**: `nut-server`, `nut-monitor`, `nut-driver@claryel-ups`, driver `usbhid-ups` (vendorid 0463, productid 0001). `upsc claryel-ups` answers: `battery.charge 100`, `battery.runtime 7200`, `battery.type PbAC`. `/etc/nut/*` root-only, contents `not_recorded` |
| Zigbee coordinator | `1a86:7523` QinHeng CH340 (TI CC2652 ZNP stick) | `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 → ttyUSB0` | mounted into the HA container as `/dev/ttyUSB0` by the generated override `/srv/claryel/config/compose.zigbee.yaml` |
| Webcam | `32e6:9251` "USB Camera" (video + audio interfaces) | `/dev/video0` `/dev/video1` `/dev/media0`, ALSA card | `motion-tavern.service` (detection-only tavern light detector); modes MJPEG 1920x1080…640x480@30, YUYV 1280x720@10 / 640x480@30, **no 320x240**; the mic was probed (peak −23.6 dB) but is unused |
| Bluetooth | `8087:0037` Intel (btusb) | hci | unused |
| (no keyboard/mouse) | `/dev/input/by-id` is empty | — | the desk is driven over xrdp/VNC only; the `usbfs` HID claim on Bus 001 Port 002 **is** the UPS (the NUT driver detaches the kernel `hid` driver) |

SAS topology is **point-to-point**: the HBA exposes exactly two targets (`[8:0:0:0]` WDC, `[8:0:1:0]` Seagate) plus their `sg` nodes — there is **no expander and no SES enclosure device**, so the physical move is one card and two cables, not a backplane job.

Array identities and health as read from `/proc/mdstat` and `/dev/disk/by-id` on 2026-11-18:
`md0` name `ubuntu-server:0`, UUID `34c2cc42:2d9329f4:86f627d6:23009f3e`, RAID1 `sda[0] sdb[1]`, `[2/2][UU]`, bitmap 65536KB chunk;
`md1` name `claryel01:1`, UUID `b1ad5b29:a929220f:4716e824:3f58d749`, RAID0 over `nvme3n1p3 nvme2n1p1 nvme1n1p1 nvme4n1p1`, 128k chunks;
`md2` name `claryel01:2`, UUID `beeeb28c:754e6882:31b83537:6d241981`, RAID10 `[4/4][UUUU]`, 128K chunks, near-copies.
No degraded member anywhere. mdadm.conf itself is root-only (`not_recorded`).

md metadata names as written on disk: `md-name-ubuntu-server:0` (= md0, the 18.2 TB backup),
`md-name-claryel01:1` (md1 hot RAID0), `md-name-claryel01:2` (md2 warm RAID10) — mdadm must be
told about the old `ubuntu-server:0` name when the array is re-assembled on another host.

No tape, no USB storage, no printer queue; the 8 ATA ports of `80:17.0` carry no disks.

## Logical peripherals (paired over the network, not cabled to this box)

Home Assistant on this host owns the radio and the integrations, so a cabled inventory is not
enough: the HA instance carries **149 entity states** (sensor 67, automation 15, binary_sensor 13,
switch 2, `input_boolean` 3, timer 2, device_tracker 2, notify 2 — REST `/api/states`, 2026-11-18),
22 devices and 8 zones per the 2026-11-18 upgrade record. The Zigbee side of that inventory
(read live from `/api/states` on 2026-11-18): `switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1`
(SONOFF BASICR4, the tavern light) and `switch.sonoff_zbminil2` (SONOFF MINI L2) — both are radios
on the coordinator stick, so they move with it; `binary_sensor.taverna_motion` and
`input_boolean.tavern_motion_now` are the camera chain (both `off`), and the stale
`input_boolean.tavern_light_blind` still sits in the entity registry as `unavailable` — delete it
from the HA UI before the move so it is not carried into the new host's `.storage`.
LAN-side consumers that are not attached hardware and must be re-pointed, not unplugged:
the TIMVISION TV (`media_player.timvision_box_2`), the MikroTik CCR5009 (management blocked, L2
only), the other fleet nodes reached over SSH/NetBird (P2005 brain, Mac Studio, Mac mini, B2003,
P1004/P1006/P3032), and the ERPNext/Odoo/OpenProject web UIs that clients open by host name.

## Software stack (host level)

* Container engine: `docker-ce` + `docker-ce-cli` + `docker-compose-plugin` + `containerd`
  (apt manual packages, 179 total). Docker object counts: 47 containers, 118 images (79.3 GB),
  131 volumes (5.9 GB), 348 build-cache entries (27.2 GB).
* Snaps: `chromium`, `cups`, `lxd`, `gnome-46-2404`, `mesa-2404`, `gtk-common-themes`, runtimes.
* Notable apt manual packages: `docker-ce*`, `nut`/`nut-server`/`nut-client`, `netbird`,
  `mdadm`, `smartmontools`, `lm-sensors`, `motion`, `xrdp`/`xorgxrdp`,
  `tigervnc-standalone-server`, `nodejs`, `python3-venv`.
* Custom system services (all `enabled`): `claryel-node-agent` (`/usr/local/bin/claryel-node-agent
  serve --listen 127.0.0.1:8091`), `claryel-amazon-business-connect-tunnel` (`cloudflared`, token
  file `/etc/claryel/...` root-only), `claryel-browser-desktop` (VNC `:20` under `claryel-ai`),
  `claryel-local-cicd-test-v1` + `-worker`, `claryel-control-primary-bind` (bind-mount of
  `~/CLARYEL/git-primary/claryel-fleet.git` into `/var/lib/claryel/control-gateway/`),
  `claryel-storage-fallback` (`/usr/local/sbin/claryel01-storage-fallback`), `motion-tavern`,
  NUT trio, `mdmonitor`, `multipathd`, `smartmontools`, `thermald`, `rasdaemon`, `avahi`,
  `netbird`, `xrdp` + `xrdp-sesman`, unattended-upgrades.
* User (linger) services: `hermes-gateway`, `hermes-dashboard`, `openbot-app` (`:3010`),
  `openbot-qoder-shim`, `claryel-integrations-mcp`, `claryel-paid-ingest`,
  `claryel-paid-stripe-poll`, `op-mcp-uds-bridge`, `openproject-ce-mcp-http`,
  `openproject-ce-mcp-cf-named` (cloudflared tunnels).
* TCP listeners observed: 22 53 631 1883 3010 3080 3350 3389 3493 4000 4010 4200 6333 8069 8070
  8080 8081 8082 8088 8090 8091 8092 8093 8095 8098 8099 8123 8333 8787 8888 9119 9188 9333
  11434 18069 18554 18555 20241-20243 35539 54619.
* Git working trees on disk: `claryel-fleet`, `claryel-box`, `claryel-boxcore`, `claryel-platform`,
  `claryel-integrations`, `claryel-accounting`, `claryel-agent-fabric`, `claryel-archive-intelligence`,
  `claryel-autoinstall`, `claryel-installer`, `claryel-node-agent`, `claryel-operations`,
  `claryel-remote-infrastructure`, `claryel-remote-ops`, `claryel-servicehub`, `claryel-space`,
  `claryel-funding`, `claryel-innovation` (under `/srv/claryel/src`, 7.0 GB) plus `~/sah-main`
  (0.15 GB) and `~/CLARYEL` (6.0 GB, includes the git-primary bare mirrors).

## Container inventory (3 projects)

| project | compose source | services up |
|---|---|---|
| `claryel-box` (18) | `/srv/claryel/platform/releases/openproject-adapter-fcd1be8cc2fb/compose*.yaml` + `/srv/claryel/config/compose.station.yaml` + `compose.zigbee.yaml` + state overlays under `/srv/claryel/runtime/state/*` | `homeassistant` (2026.11.2, host network, privileged), agent-fabric, integrations, knowledge-api, funding-monitor, next-steps-tracker, librechat `:3080`, litellm `:4000`, activepieces `:8090`, ollama, clamd, meilisearch, mongodb, mosquitto `:1883`, postgres, qdrant `:6333`, seaweedfs `:8333/:8888`, valkey, `claryel-home-assistant-bridge`, `claryel-cooling-ingest` |
| `erpnext-np` (9) | `/home/viktor/CLARYEL/var/erpnext-np/compose.yml` | ERPNext v16.32.3 frontend `:8095`, backend, scheduler, 2 queues, websocket, MariaDB, 2 redis |
| `odoo` (2) | `/srv/claryel/src/claryel-accounting/deploy/odoo/compose.yaml` | `odoo:18.0-20260723` `:8069`, postgres |
| standalone / stopped | — | `claryel-fileshare` (ERPNext v16.52.1 image, `:8098`), `claryel-openproject` (`:8099`), `claryel-local-service-directory`, `openbot-*` (mostly exited), `claryel-servicehub*` (exited) |

## Hermes on this box

Hermes Agent v0.23.2+11 (upstream `458a0046`), install dir `~/.hermes/hermes-agent`
(9.6 GB total for `~/.hermes`). 10 profiles (`bedrock`, `claryel-ops`, `claude-fable`,
`claude-sonnet`, `codex`, `cursor`, `fast`, `grok`, `industry-kb`, `mikrotik`, + the agent-maker
profile), 49 skills, **40 cron jobs** (fleet watchdogs, HA backups, benchmark loops, storage and
power guards). The conversational brain is **not local**: it is served from P2005
(Basalt / `qwen3.8-flash-next-iq3_s-basalt`), with mac → codex → grok → sonnet fallbacks, so the
model files are not on this machine.

## Migration-relevant facts about the destination (from P3001's passport, box currently powered off)

HP Z420: Xeon E5-2697 v2 (12c/24t, **AVX1 only, no AVX2**), 62 GiB DDR3 ECC, Quadro K620 (console)
+ Radeon RX 580 2048SP (the CUDA-only Strata engine therefore serves nothing there), 240 GB SATA
system SSD + 1 TB FireCuda NVMe, 1 GbE, Ubuntu 24.04.4, clock UTC, no M.2 slots for the Lexar pool.
P3001 did not answer ICMP on 2026-11-18 03:10 (de-energised since the GPU-drift incident).

## Verify commands

`lscpu`, `free -h`, `lsblk -d -o NAME,SIZE,MODEL,SERIAL,ROTA,TRAN,WWN`, `nvme list`, `lsscsi -g`,
`cat /proc/mdstat`, `blkid /dev/md0`, `ls /dev/mapper`, `findmnt`, `df -h`, `lspci -nnk`, `lsusb -t`,
`ls /dev/serial/by-id`, `upsc claryel-ups`, `docker ps -a`, `docker compose ls`, `docker system df`,
`systemctl list-units --state=running`, `systemctl --user list-units`, `apt-mark showmanual`,
`snap list`, `ss -ltnp`, `ip -br addr/link`, `swapon --show`, `id`, `du -sh`.
Still missing and requiring root: `dmidecode -t memory` (DIMM parts), `smartctl -H` per disk,
`dmsetup ls`/`vgs`, `/etc/nut/*`, `/srv/claryel/config/compose.station.yaml`, `/etc/claryel/*`.
