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

## The owner re-paired the fan relay at 21:59 — and the network refused it for ten minutes

Log trail (HA container, local time): `21:59:06 Device 0xe25a left the network`, then it joined three
times in twenty seconds (`0x94a9`, `0xc413`, final `0x580b`), ZHA re-interviewed it
(`zhaquirks.sonoff.zbminil2`, `pairing_status: CONFIGURED -> INITIALIZED`). Between **22:02 and 22:07**
every command from HA failed with `Status.NWK_NO_ROUTE: 205` or `Status.MAC_NO_ACK: 233` — **34 failed
sends in 12 h** — and the `vytyazhka servernoy` automation errorred on every run. Meanwhile the module
kept reporting: pressing its physical button still changed the fan state and HA showed it correctly.
That asymmetry is the signature: reports (device -> coordinator) got through, commands (coordinator ->
device) did not.

By 22:13 it healed on its own. Measured after that: `turn_on` confirmed in **244 ms**, `turn_off` in
**233 ms**, zero further delivery errors, and its link improved from LQI **39 to 58**.

What the re-pair did *not* change — the interview is explicit:
`logical_type=EndDevice`, `is_mains_powered=False`, `is_receiver_on_when_idle=False`, `is_router=False`,
`relays_v16` still empty. The module tells the network it is a battery device that switches its receiver
off when idle; that is exactly why it can go "visible but uncommandable", and it will never repeat for
anyone else.

The label photo confirms the other argument: `ZBMINI L2`, **"No Neutral Required"**, `6A MAX Resistive
Load`, `LED: 150 W @ 100 V / 300 W @ 240 V`. Resistive and lamp loads only — the fan motor is outside
that rating, so the unit is a replacement candidate regardless of the radio story. Sonoff's OTA endpoint
offers only `0x100E` (the version already installed, listed as a downgrade), so no firmware fix exists.

Watchdog additions from this incident (`scripts/radio-health/`): it now scans
`docker logs --since 12h homeassistant` for `MAC_NO_ACK` / `NWK_NO_ROUTE` and alerts when more than five
sends failed, naming the automations involved — a device that cannot be commanded looks healthy in
`/api/states`. Dedup keys now replace digits (`LQI=#`), so a sensor bouncing between LQI 7 and 0 stays
one problem instead of a new alert every tick.

## The exhaust fan: manual control without losing the child lock (2026-11-18, 23:00)

The operator reported: pressing the wall button switches the fan on and it immediately drops out
(that part is the child lock working), but **switching it on from HA also dropped out** — he wants
manual on/off from HA to just work, and the 3x/day schedule to stay.

Cause, in `/config/configuration.yaml`: automation `vent_servers_room_guard` triggers every 10 min
**and instantly on `switch.sonoff_zbminil2 -> on`**, and turns the fan off whenever the clock is
outside 07:00-07:20 / 14:00-14:20 / 21:00-21:15. It cannot tell a person from a child, so it killed
every manual switch-on the same way.

Fix — distinguish who flipped it. A state change made through HA carries a `user_id` in its context;
a change reported by the relay itself (wall button) carries none:

```yaml
input_boolean:
  fan_servers_manual:      # "Вытяжка серверной: вручную (страж не тушит)"
timer:
  fan_servers_manual:      # duration 02:00:00

automation:
  - id: vent_servers_room_manual_permission   # user switched it on -> 2 h permission
    triggers:  [{trigger: state, entity_id: switch.sonoff_zbminil2, to: "on"}]
    conditions: [{{ trigger.to_state.context.user_id is not none }}]
    actions:   input_boolean.turn_on + timer.start
  - id: vent_servers_room_manual_release      # user switched it off -> drop the permission
  - id: vent_servers_room_manual_expiry       # timer.finished -> drop the permission
```

and in the guard, before the time-window test:

```yaml
      - condition: state
        entity_id: input_boolean.fan_servers_manual
        state: "off"
      - condition: template
        value_template: >-
          {{ trigger.platform != 'state' or trigger.to_state.context.user_id is none }}
```

Result: a person in the app gets the fan and keeps it (permission auto-expires after 2 h so a
forgotten fan cannot run all night); a wall-button press is still cancelled outside the schedule;
the three schedule automations were not touched.

Verified against the live system:

- manual `switch.turn_on` -> fan on, `input_boolean.fan_servers_manual` on, timer active, **still on
  after 90 s** (the guard stood down);
- manual `switch.turn_off` -> flag cleared, timer back to `idle`;
- the non-user path (automation-triggered switch-on, which is what the wall button looks like to HA)
  -> flag stayed off and the guard killed it again in **about 1 second** (guard `last_triggered` moved
  from 21:37:24Z to 21:45:59.018Z, one second after the trigger), so it is the instant state trigger
  doing the work, not the 10-minute sweep. The recorder shows the same shape: every non-user `on` is
  followed by a guard `off`.

Two HA 2026 gotchas found while doing this:

- an automation with `mode: restarted` loaded as **`unavailable` with no error in the log** (the other
  automations in the same file were fine). With `mode: single` it works; the entity carries no
  `current`/`last_triggered` attributes while it is unavailable, which is how to spot it.
- the recorder schema changed: `states.last_changed` is now NULL and `states.context_user_id` is empty
  — use `last_changed_ts` and `context_user_id_bin`, and join `states_meta` for `entity_id`.

Backup of the config before the edit: `/config/configuration.yaml.bak-fan-manual-20261118`.

## Room naming corrected: the servers room is in the basement, the fan is in the storage room

The room that held the exhaust fan was always the **кладовка**, not the servers room; the servers room
(itself, the UPS, the Zigbee coordinator and its temperature sensor) moved down to the **basement**.
Areas now say so:

- new area **Storage room** (`storage_room`) -> the Sonoff ZBMINI L2 module, renamed
  **Вентилятор кладовки (модуль в розетке)**;
- area **Server room** (`servers`) -> the TS0201 temperature sensor, `Claryel-UPS`, and the
  CC2652 Zigbee coordinator (it had no area before);
- entity ids were not touched, so `switch.sonoff_zbminil2` and every automation still works.

The automation aliases still read "Вытяжка серверной" — renaming them would change their entity ids and
drop their history, so they stay; the fan they control lives in the storage room.

### Wording correction after the operator pushed back

I described the two paths as "a person in HA" vs "a child at the button", which is wrong and confusing:
**children are people too**. The distinction is the **path the command took**, nothing else:

- `context.user_id` is set when the command came **through HA** (app, dashboard, voice, API) and HA knows
  which account issued it;
- it is empty when the state change was **reported by the relay itself**, i.e. someone pressed the physical
  button on the module.

So the child lock works on the wall button, and a manual switch from HA is honoured for 2 h regardless of who
was holding the phone. If the operator ever wants the app path restricted too, the condition is one line —
compare `trigger.to_state.context.user_id` against a specific account id — but that would also block the rest
of the family (HA has `person.viktor` plus two Samsung phone trackers), so it is not on by default.
Renamed UI labels for this reason: `input_boolean.fan_servers_manual` is now "Вытяжка кладовки: включено из HA
— страж не трогает 2 ч" and the three automations read "включено/выключено из HA"; entity ids did not change.
