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
| RAM | 30 GiB usable (single-socket DDR5, DIMM parts `not_recorded (needs root: dmidecode)`) |
| swap | 256 GiB LV `claryel-hot-vg/swap` (prio 100, ~6.8 GiB in use) + 32 GiB file `/srv/claryel/archive/.claryel-emergency.swap` |
| OS | Ubuntu 24.04 **desktop** flavour (noble), x86-64, `graphical.target` + GNOME snap + xrdp, Secure Boot `not_recorded`, clock local (CET) |
| users | `viktor` uid 1000 (groups: sudo, docker, video, lxd, claryel, claryel-rdp, claryel-vnc), `claryel-ai` uid 1001 (browser-desktop services) |
| network | wired `enp128s31f6` Intel `8086:550c` (e1000e) **1 GbE**, carrier up; Wi-Fi chip present (`iwlwifi`) but no wireless interface is exposed; NetBird mesh client active; Docker bridges `172.17/19/22/23/30` |
| boot | UEFI + GRUB (`/boot/grub/grub.cfg`, 15 entries), EFI system partition on `nvme3n1p1` |

## Storage topology

| device | model / serial | size | role |
|---|---|---|---|
| `nvme3n1` | Lexar NM1090 PRO 2TB `QG4464R000289P3200` | 1.9 TB | **system**: p1 EFI (1 GB) + p2 `/` (196 GB, 74 % used); its p4 is also an md2 member |
| `nvme1n1` `nvme2n1` `nvme3n1` `nvme4n1` | Lexar NM1090 PRO 2TB ×4 (serials `...036`, `...201`, `...289`, `...843`) | 2.05 TB each | striped/partitioned pool |
| → `md1` | RAID0 over `nvme2n1p1 nvme3n1p3 nvme1n1p1 nvme4n1p1` | 2.4 TB | `LVM2_member` → VG `claryel-hot-vg` → LV `data` mounted `/srv/claryel/hot` (**188 GB used**), LV `swap` |
| → `md2` | RAID10 over `nvme3n1p4 nvme2n1p2 nvme1n1p2 nvme4n1p2` | 2.2 TB | ext4 `/srv/claryel/warm` (**188 GB used**) |
| `nvme0n1` | Samsung 990 PRO 2TB `S7HENL0L306707Z` | 2.0 TB | p3 ext4 → `/srv/claryel/archive` (**121 GB used**) |
| `sda` | WDC **WUH722020BL5204** 20 TB SAS `9BKDPMPL` | 18.2 TiB | md0 member |
| `sdb` | Seagate **ST20000NM007H** 20 TB SAS `ZYD970GN` | 18.2 TiB | md0 member |
| → `md0` | RAID1 (`sda[0] sdb[1]`, super 1.2, bitmap, 146 bitmap pages) | 18.2 TB | ext4 `LABEL=CLARYEL_SAS_BACK` → `/srv/claryel/backup` (**298 GB used**) |
| HBA for `sda`/`sdb` | **Broadcom/LSI SAS3008 Fusion-MPT SAS-3** (`1000:0097`), Inspur 12G SAS3008IT subsystem (`1bd4:000c`), slot `83:00.0`, driver `mpt3sas` | — | the two 20 TB drives are the only devices behind it (`lsscsi` bus `[8:0:0:0]`, `[8:0:1:0]`) |
| Intel VMD | `8086:ad0b` (driver `vmd`) | — | the NVMe pool is behind Intel Volume Management Device — **NVMe enumeration on another board will differ** |

Health: `smartctl -H` for all seven block devices `not_recorded (needs root)`; `smartmontools`,
`mdmonitor`, `multipathd`, `rasdaemon` are enabled and running. Total on-data: ~880 GB
(hot 188 + warm 188 + backup 298 + archive 121 + docker 79 images + 27 build cache + 6 volumes
+ `~/.hermes` 9.6 + `~/CLARYEL` 6 + `~/sah-main` 0.15).

## External / USB devices (what has to be physically re-plugged)

| device | id | device node | who consumes it |
|---|---|---|---|
| UPS | `0463:0001` MGE UPS Systems (Bus 001 Dev 006, HID) | via libusb | **NUT is live**: `nut-server`, `nut-monitor`, `nut-driver@claryel-ups`, driver `usbhid-ups` (vendorid 0463, productid 0001). `upsc claryel-ups` answers: `battery.charge 100`, `battery.runtime 7200`, `battery.type PbAC`. `/etc/nut/*` root-only, contents `not_recorded` |
| Zigbee coordinator | `1a86:7523` QinHeng CH340 (TI CC2652 ZNP stick) | `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 → ttyUSB0` | mounted into the HA container as `/dev/ttyUSB0` by the generated override `/srv/claryel/config/compose.zigbee.yaml` |
| Webcam | `32e6:9251` "USB Camera" (video + audio interfaces) | `/dev/video0` `/dev/video1` `/dev/media0`, ALSA card | `motion-tavern.service` (detection-only tavern light detector); modes MJPEG 1920x1080…640x480@30, YUYV 1280x720@10 / 640x480@30, **no 320x240**; the mic was probed (peak −23.6 dB) but is unused |
| Bluetooth | `8087:0037` Intel (btusb) | hci | unused |
| HID | Bus 001 Port 002 (usbfs) | input | keyboard/mouse |

No SAS expander, no tape, no USB storage, no printer attached (`cups` snap runs, no queue seen).

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
