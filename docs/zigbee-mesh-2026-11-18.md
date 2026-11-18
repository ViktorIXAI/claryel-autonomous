# Zigbee mesh: measured topology, the ZBMINIL2 router question, and the re-pair procedure

Measured on claryel01 (Home Assistant 2026.11.2 + ZHA), 2026-11-18 evening.
Sources: `zigbee.db` (tables `devices_v16`, `neighbors_v16`, `relays_v16`, `routes_v16`,
`node_descriptors_v16`) and `.storage/core.{device,entity,area}_registry`, read through a
read-only bind mount and `docker exec`; live states via `GET /api/states`.
IEEE addresses, PAN id and the network key are deliberately not recorded here.

## What the network actually looks like

| Item | Measured |
|---|---|
| Coordinator | Texas Instruments CC2652, `radio_type: znp`, `/dev/ttyUSB0` (CH340 USB serial), on claryel01 in the basement |
| Devices in the network | 11 rows in `devices_v16` (10 joined + coordinator) |
| Routers other than the coordinator | **none** — `relays_v16` holds 0 rows |
| Route table | 1 row |
| Every neighbour entry | `depth=1` — every device talks to the coordinator directly |

So the "mesh" is a **star**: each device reaches the coordinator on its own, nobody repeats
for anybody else. That matches the owner's observation that the coordinator, although pulled
up out of the basement on a USB extension, does not cover the whole flat.

Devices and live link quality (LQI 255 = best):

LQI was readable for six devices only — the ZHA link-quality entities were disabled until this
evening, and they populate as each device reports. `—` = not reported yet at measurement time.

| Device (HA area) | Model | LQI to coordinator | Battery | State |
|---|---|---|---|---|
| TS0201 — Server room | TS0201 | 121 | 60 % | alive |
| SNZB-04PR2 — Door Garden | SNZB-04PR2 | 116 | 100 % | alive |
| SNZB-04PR2 — Door Leo | SNZB-04PR2 | 99 | 100 % | alive |
| SNZB-04PR2 — Door Ksu | SNZB-04PR2 | 54 | 100 % | alive |
| SNZB-04PR2 — DOOR 1 (Open-plan office) | SNZB-04PR2 | **39** | 89 % | alive, weak |
| ZBMINIL2 relay ("Cooler servers room") | ZBMINIL2 | **39** | n/a (mains) | alive, weak |
| TS0201 — Room3 | TS0201 | — | 100 % | alive |
| TS0201 — Open-plan office | TS0201 | — | **1 %** | alive, battery nearly dead |
| TS0201 — Claryel Garden | TS0201 | — | 100 % | alive |
| TS0201 — Terrace | TS0201 | — (no neighbour entry at all) | unknown | **silent 35 days** |

The basement light is **not** part of this network: `switch.taverna_taverna_basicr4_sonoff_...`
is a BASICR4 **Wi-Fi** device on the eWeLink cloud integration (see
`tavern-motion-camera-2026-11-18.md`).

## Why the ZBMINI L2 does not repeat the signal

`node_descriptors_v16` for the relay reads `logical_type = 2` (`EndDevice`) and
`rx_on_when_idle = 0`. That is not a misconfiguration on our side: the ZBMINI **L2** is the
*no-neutral* version and it ships as a Zigbee End Device — the published Zigbee signature for
ZBMINIL2 carries the same `logical_type: 2`, and Sonoff/ITead document the L2 line as an end
device. End devices never route for others, so this relay can never become a repeater,
no matter how often it is paired.

Consequences and related known issue:

- The relay is a *sleepy* device even though it is mains powered, which is why its own link is
  fragile (LQI 39) and why the LQI/RSSI entities for it go `unknown` when it stops polling.
- Firmware on our unit is `0x0000100e`. ZHA offers no newer build (`installed == latest`), and
  this is the exact firmware several HA users report as dropping off the network after
  topology changes, recoverable only by a 5-second re-pair while the local relay keeps working.
  Expect occasional drop-outs of this device and treat them as firmware, not wiring.
- Sonoff's own manual warns the ZBMINI L2 is not meant for inductive loads such as fans.
  Our unit is wired to the "Cooler servers room" fan, which is an inductive load — a plausible
  reason to replace it regardless of the mesh question.

## What would actually extend the network

A **Zigbee 3.0 router** (mains device with a neutral) placed between the basement and the flat:

- Sonoff sells the router version of the same in-wall module as **ZBMINIR2** ("Mini Relay
  Extreme", EFR32MG21, explicitly advertised as a repeater for up to 64 end devices). It
  **requires a neutral wire** in the installation box — that is the only blocker for a drop-in
  swap of the L2 that is in the middle-of-the-flat socket now.
- Any plug-in Zigbee 3.0 repeater works equally well; before buying, check the device class on
  `zigbee.blakadder.com` and look for "Router", not "EndDevice".
- One router is enough to break the star: end devices then join through it and the two weak
  links (DOOR 1 at 39, the relay at 39) get a short hop instead of reaching the basement.

## Re-pairing procedure (fixes a stuck session, does not change the device class)

1. In HA: Settings → Devices & Services → **Home Assistant Zigbee (ZHA)** → *Add devices*
   (opens the join window; re-open it if it times out).
2. On the module: hold its button **5 seconds** until the green LED flashes slowly. The pairing
   window on the device lasts 3–10 minutes. While it is in pairing mode the relay cannot be
   switched by its own button or the external wall switch — if that relay runs the server-room
   fan, the fan stops for the duration.
3. Factory-reset variants documented by Sonoff if the 5-second hold does not start pairing:
   10 quick ON/OFF cycles of the external switch, or delete the device in the hub first.
4. ZHA finds it by the same IEEE address, so the HA device and all its entities and
   automations are kept — no need to delete the device in HA beforehand.
5. Verify afterwards (either command needs no root):

   ```bash
   docker exec -i homeassistant python3 - <<'PY'
   import sqlite3
   db = sqlite3.connect("file:/config/zigbee.db?mode=ro", uri=True)
   for row in db.execute("select ieee, logical_type, rx_on_when_idle from node_descriptors_v16"):
       print(row[0], "logical_type=", row[1], "rx_on_when_idle=", row[2])
   print("relays:", db.execute("select count(*) from relays_v16").fetchone()[0])
   PY
   ```

   `logical_type = 2` means End Device (what the L2 will stay), `245` means Router.
   A real router also makes `relays_v16` stop being empty and produces `depth=2` rows in
   `neighbors_v16` for the devices behind it.

## What I changed on 2026-11-18 evening

- Enabled all 20 ZHA link-quality entities (`sensor.*_lqi`, `sensor.*_rssi`) — they ship
  disabled, which is why link quality was invisible in HA until now.
- Removed 4 orphan entities left by the deleted "Sonoff LAN" integration
  (`..._rssi`, `..._connection`, `..._led`, `..._detach` of the basement BASICR4). Verified that
  no automation, script, dashboard or storage file referenced them first.
- Added the radio watchdog `scripts/radio-health/radio-health-watch.py` (cron
  `e671b3f908dc`, 08:00 and 20:00): alerts on a Zigbee device going offline, LQI below 40,
  RSSI below −92 dBm and battery below 25 %, deduplicated so a permanently dead sensor is
  reported once a day, and shouts `HA UNREADABLE` if it cannot reach Home Assistant at all.
  First run already found two things: the Terrace TS0201 offline, and the **Open-plan office
  TS0201 at 1 % battery** — an earlier manual audit had reported "89–100 %" because it only
  sampled one battery entity per device-name prefix.

## Owner's list

1. Battery in the Open-plan office TS0201 (1 %) — do this first, it is the cheapest save.
2. Battery / placement of the Terrace TS0201 (silent 35 days, 12 drop-outs in the week before).
3. Replace the middle-of-the-flat ZBMINI **L2** with a router-class module (ZBMINIR2 if that box
   has a neutral, otherwise any plug-in Zigbee 3.0 repeater) — this is the only real fix for the
   star topology, and it also removes a module that is driving an inductive fan load against
   its rating.
4. Physical: the coordinator sits on a USB extension out of the basement; if a router is added
   on the flat side, DOOR 1 and the fan relay both improve without moving it.

## Second pass the same night: batteries, temperatures, names

Battery values were re-checked against 60 days of recorder history instead of one snapshot:

| device | now | 60-day min | note |
|---|---|---|---|
| Room3 TS0201 | 100 % | 100 % | |
| Open-plan office TS0201 | 100 % | **1 %** | four distinct battery values in ten days, 1 % then back to 100 % - the channel is unreliable |
| Server room TS0201 | 60 % | **50 %** | the only genuinely mid-range battery in the set; plan a replacement this season |
| Claryel Garden TS0201 | 100 % | 100 % | |
| Terrace TS0201 | no data | - | silent for 35 days |
| Door DOOR 1 (SNZB-04PR2) | 89 % | 89 % | |
| Door garden side / Ksu / Leo (SNZB-04PR2) | 100 % | 100 % | |
| Fan relay (ZBMINIL2) | n/a | - | mains powered; ZHA exposes a phantom battery entity that stays `unknown` |

The 1 % alert I sent earlier was therefore a **sensor glitch, not a dying battery**. The watchdog now
requires **two consecutive low readings** before alerting (`batt_low` is kept in its state file); a real
dying battery is still reported within twelve hours, a one-sample artefact never is.

Temperatures cross-checked over thirty days - the spread between sensors is real, not a reporting bug:
garden 5.6 °C (outdoor, range 3.1-17.6), Open-plan office 20.9 (18.2-23.6), Server room 18.7
(18.1-22.2), Room3 17.5 (15.5-19.0) at 78 % humidity. Room3 is the coolest and most humid indoor room;
if it stays at 17-18 °C, the exterior wall is the place to watch for condensation.
(The `samples` column counts state *changes* and `max_gap` is the longest stretch with an unchanged
value - 55 h in Room3 means the temperature sat still, not that the radio was silent.)

Link quality from the device side (the newly enabled `sensor.*_lqi`) tells a sharper story than the
coordinator's neighbour table: **Claryel Garden 7**, Room3 **21**, fan relay **40**. The garden sensor
has the worst link in the house and still reports - it is the first candidate to go quiet, and the
strongest argument for a router between it and the coordinator.

Names: every Zigbee device is now named by location, so HA composes the entity names itself
("Room3 Температура", "Дверь DOOR 1 Батарея"). Five identical `Wing TS0201` devices became Room3 /
Open-plan office / Terrace / Server room / Claryel Garden; four identical `SONOFF SNZB-04PR2` became
Дверь DOOR 1 / Дверь garden side / Дверь Ksu / Дверь Leo; `SONOFF ZBMINIL2` became "Вентилятор серверов
(модуль в розетке)" with labels `zigbee_end_device` and `no_neutral`. The Open-plan temperature sensor
carried a per-entity display override that showed it as "Room0" - cleared. `entity_id`s were not
touched, so automations, scripts and dashboards are unaffected.

Measured cost of the cloud path for the basement relay (Wi-Fi, eWeLink): the HA service call reached
state `on` in **467 ms** and `off` in **416 ms**. A Zigbee relay in the basement would answer in single-digit
milliseconds - worth knowing if the flicker ever matters.
