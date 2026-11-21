# MikroTik CCR5009UG+S+IN — status and access verdict (2026-11-15)

Box: CCR5009UG+S+IN, serial `HJW0AR6ECVJ`, RouterOS 7.18.2 stable (build 2025-03-11).
It sits inside the house LAN: `ether1` is a slave of `bridge1`, it sends RSTP BPDUs every ~2 s
(bridge-id priority 32768, flags Proposal/Learn/Forward, no TCN churn) and answers LLDP/CDP as
`MikroTik`, Port-ID `bridge1/ether1`. Our monitoring host sees it on its wired NIC.

## What we can see, and how (root-free)
- RouterOS 7.1x has **MNDP off by default** — an MNDP/CDP multicast capture proves nothing about presence.
- Presence probe that needs no root and no IP: the box's own **IPv6 link-local address derived from its label
  MAC** (modified EUI-64), pinged with `ping6`. Steady 3/3 replies at ~0.5 ms.
- No IPv4: the box has no address in our LAN's ARP table, and it never answers on the factory-default
  management network (address masked `<LAN_IP>/24` here; the literal lives in the campaign notes)
  (probed from a throwaway macvlan container, cleaned up afterwards).

## Why we cannot configure it (measured, not assumed)
- Full TCP sweep of the box's link-local address — ports 1–1024 plus `8291 8728 8729 2000 2323 80 443 8080
  8443 12321` — returns **zero open ports**.
- Netinstall (UDP 5678) is silent, so the box is not in netinstall mode.
- Conclusion: RouterOS input is blocked on the bridge or the management services are disabled. There is no
  software path to the box from the LAN, and no trusted open-source IP-less Winbox client — the PyPI package
  `PyWinBox` is an X11 window-geometry library, not a RouterOS client. No router setting has been changed.

## Decision
1. Cable test (2 min, no config change): a laptop with a static address inside the factory-default
   management network (masked; the literal lives in the campaign notes) plugged into a free port of
   the box, then try the factory-default gateway address (masked). This only works if the box is still
   factory-defaulted.
2. If that fails, hardware reset: **unplug the cable carrying the box into the house LAN first** (a
   factory-defaulted box re-joins the LAN as a bridge and can loop it), hold RESET ~10 s until the ACT LED
   blinks, then reach the factory-default gateway address (masked) directly. This wipes whatever config existed; the evidence that nothing
   valuable is on it is that it has no IPv4, no listening service and does nothing but participate in RSTP.
3. First action after access: read-only `/export verbose` snapshot into the campaign `configs/` directory,
   then rotate the admin password, only then start dual-WAN work.

## Watchdog (cron, every 30 min, silent unless an edge happens)
`scripts/`-level watchdog probes both label MACs over IPv6 link-local: 3 pings per MAC, 2 replies = present;
LOST requires two consecutive missing samples; recovery is reported immediately. State and log live under
`~/.hermes/mikrotik-campaign/findings/` so the watchdog survives profile changes. Delivery: Bot Chat plus
Home Assistant push (`deliver=...,homeassistant`) — the scheduler, not a hand-rolled REST call, because the
`HASS_TOKEN` in `.env` is rejected by this HA instance with 401 (the Hermes HA plugin works).

## Incident: one false LOST
At 18:24 the watchdog reported the box gone. It was alive (link-local ping 3/3, RSTP still flowing, our own
uplink healthy). Cause: the old probe used a single `ping6 -c1` plus an `ip neigh` grep, and in that one sample
the neighbour entry had just been garbage-collected and one ICMPv6 echo was lost. Fixed by the 3-ping/2-reply
rule plus the two-sample loss rule. A second event at 19:04 was a self-inflicted test fire of the alert path,
not a network event.

## Credential hygiene
The one-time password printed on the product label now lives in exactly one place: a `chmod 600` `.env` in the
campaign directory. A filesystem audit (search for the value read back from that file, report only the paths that
matched) found two incidental copies — inside a subagent's live delegation transcript and in an automatic scratch
snapshot — and both were scrubbed; the session databases never held the literal, because agent transcript output is
redacted on the way to disk. Earlier a helper script embedded a SHA-256 of it, which is forbidden practice but is
not exposure of the password itself.

Rotation is still recommended before configuration starts (factory password is one-time, per device), and the
replacement is collected under a separate key and only replaces the old one after it has really been applied on the
router — overwriting early locks us out of the only box we are trying to reach. Standing rules: helper scripts never
embed credentials or derivatives of them; secrets live only in a `chmod 600` `.env`; campaign artifacts live outside
any agent profile home, because a profile delete is destructive and there is no restore command. No secret, MAC or
LAN address in this repository.

## Both router-class boxes went dark, 2026-11-21 05:05-08:40

| Time (CET) | Observation |
|---|---|
| 05:05 | CCR5009 still answering `ping6` on its derived link-local address, 3/3 replies |
| 05:36 | `ping6` returns 0/3, but the watchdog reported *present* anyway - it fell back to a leftover `STALE` neighbour entry |
| 06:08 | the house default gateway stops answering: DNS fails, `HA` logs the cloud WebSocket DNS error, the tavern relay goes `unavailable` |
| 06:38 | still reporting *present* from the same cached entry |
| 07:09 | first honest `absent` sample (miss=1) |
| 07:40 | miss=2, state becomes `absent` |
| 08:40 | the `LOST` line finally reaches the chat - about three hours after the box actually went quiet |
| 08:41 | measured now: both link-local addresses 0/3, the gateway 0/2, ARP down from 43 to 23 entries with 9 `FAILED` (the Wi-Fi clients are gone), while the wired hosts still reach each other and Home Assistant answers |

Reading: the wired segment and the switch are alive, so this is not a patch cord on one host - the router and the
CCR5009 both stopped being reachable on the wire within an hour of each other, which points at power or an
uplink on the shelf. Nothing on either box was changed by any agent; the watchdog is read-only.

Watchdog defect found by this incident: the `ip neigh` fallback counted `STALE` entries as presence. A cached
neighbour entry is not proof of life - it kept the alert quiet for three hours. Now only `REACHABLE`/`DELAY`
count (`FAILED`, `INCOMPLETE`, `STALE`, `PERMANENT` are rejected). The `LOST` line also probes the default
gateway and states which case it looks like, so "one box off" and "the whole shelf is off" no longer read the
same: tested in a scratch copy with seeded state - first sample silent, second prints
`... the house router does not answer either - check power/switch on the shelf before the cable ...`, third silent.

## The box is back and now answers on management ports, 2026-11-21 11:46

The watchdog reported `FOUND`: ether1 answers its derived IPv6 link-local address 3/3 at 0.7 ms, and the
state file went from `absent` to `present`. What changed since the 2026-11-15 lockdown:

| Probe | 2026-11-15 | 2026-11-21 11:48 |
|---|---|---|
| `ping6` on ether1 link-local | 3/3, 0.5 ms (box was up then too) | 3/3, 0.7 ms |
| SSH / telnet / WebConfig / Winbox / API | all closed or filtered | **22, 23, 80, 8291, 8728 open** |
| IPv4 entry in ARP for either MAC | none | none |
| House router (default gateway) | alive | **silent since 06:08**, no egress for 5 h 40 min |

So somebody reconfigured or reset the CCR5009 between the two measurements - services that were previously not
reachable on this interface are now listening - but it still holds no IPv4 address, is not the gateway and does
not serve DHCP: it is not carrying the house traffic yet, and the house is therefore offline with the old
router unplugged or off.

The standing campaign step ("snapshot `/export verbose` before any change") was attempted and is blocked: the
RouterOS API on the link-local address answers the factory empty-password login with `not logged in`, so a
password is set. Stopped there - no password guessing, nothing else tried, no other port touched. The read-only
client used for the attempt is `~/.hermes/cache/scratch/ros-api.py` (stdlib only; it refuses any command path
that is not a `print`/`export`-class path, and it would have written the raw export to a local `0600` file with
password lines masked before anything reached stdout, because RouterOS prints user passwords in clear text).
To unblock the snapshot the login has to be placed in `~/.hermes/.env` by the operator himself
(`MIKROTIK_ROS_LOGIN`, `MIKROTIK_ROS_PASSWORD`) - credentials must not pass through chat.
