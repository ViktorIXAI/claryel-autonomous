# MikroTik CCR5009UG+S+IN — status and access verdict (2026-11-15)

Box: CCR5009UG+S+IN, serial `HJW0AR6ECVJ`, RouterOS 7.18.2 stable (build 2025-03-11).
It sits inside the house LAN: `ether1` is a slave of `bridge1`, it sends RSTP BPDUs every ~2 s
(bridge-id priority 32768, flags Proposal/Learn/Forward, no TCN churn) and answers LLDP/CDP as
`MikroTik`, Port-ID `bridge1/ether1`. Our monitoring host sees it on its wired NIC.

## What we can see, and how (root-free)
- RouterOS 7.1x has **MNDP off by default** — an MNDP/CDP multicast capture proves nothing about presence.
- Presence probe that needs no root and no IP: the box's own **IPv6 link-local address derived from its label
  MAC** (modified EUI-64), pinged with `ping6`. Steady 3/3 replies at ~0.5 ms.
- No IPv4: the box has no address in our LAN's ARP table, and it never answers on the factory `192.168.88.0/24`
  (probed from a throwaway macvlan container, cleaned up afterwards).

## Why we cannot configure it (measured, not assumed)
- Full TCP sweep of the box's link-local address — ports 1–1024 plus `8291 8728 8729 2000 2323 80 443 8080
  8443 12321` — returns **zero open ports**.
- Netinstall (UDP 5678) is silent, so the box is not in netinstall mode.
- Conclusion: RouterOS input is blocked on the bridge or the management services are disabled. There is no
  software path to the box from the LAN, and no trusted open-source IP-less Winbox client — the PyPI package
  `PyWinBox` is an X11 window-geometry library, not a RouterOS client. No router setting has been changed.

## Decision
1. Cable test (2 min, no config change): a laptop with a static `192.168.88.10/24` plugged into a free port of
   the box, then try `192.168.88.1`. This only works if the box is still factory-defaulted.
2. If that fails, hardware reset: **unplug the cable carrying the box into the house LAN first** (a
   factory-defaulted box re-joins the LAN as a bridge and can loop it), hold RESET ~10 s until the ACT LED
   blinks, then reach `192.168.88.1` directly. This wipes whatever config existed; the evidence that nothing
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
The one-time password printed on the product label must be treated as **burned**: it appeared in agent
transcript databases and a helper script embedded a hash of it. Rules now enforced: helper scripts never embed
credentials or derivatives of them; secrets live only in a `chmod 600` `.env`; a replacement password is
collected under a separate key and only replaces the old one after it has really been applied on the router
(overwriting early locks us out of the only box we are trying to reach); no secret, MAC or LAN address in
this repository.
