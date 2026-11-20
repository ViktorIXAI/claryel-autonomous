"""Can the tavern relay be reached locally, without the eWeLink cloud?

Two probes, no credentials involved:
 1. mDNS: listen on 5353 for ~20 s and look for `_ewelink._tcp.local.` announcements - that is how the
    Sonoff integration finds LAN devices (zeroconf service type in core/ewelink/local.py).
 2. TCP 8081: the eWeLink LAN API port, probed against every host currently in the ARP table.
Addresses and MACs are printed masked: only the last octet / last OUI-less part, because the numbers
themselves never go into chat or the repo.
"""
import array
import fcntl
import socket
import struct
import subprocess
import sys
import time

MASK = lambda ip: ".".join(ip.split(".")[:3]) + ".*" if ip.count(".") == 3 else ip


def arp_hosts():
    out = subprocess.run(["ip", "-4", "neigh", "show"], capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        f = line.split()
        if len(f) >= 1 and f[0][0].isdigit():
            ll = next((x for x in f if x == "lladdr"), None)
            mac = f[f.index(ll) + 1] if ll else "?"
            rows.append((f[0], mac))
    return rows


def probe_8081(rows):
    hits = []
    for ip, mac in rows:
        try:
            s = socket.create_connection((ip, 8081), timeout=1.0)
        except OSError:
            continue
        # the eWeLink LAN API answers an unauthenticated GET with {"error":404,...} or similar JSON
        try:
            s.sendall(b"GET /zeroconf/info HTTP/1.1\r\nHost: x\r\nContent-Length: 0\r\n\r\n")
            s.settimeout(2.0)
            body = s.recv(600)
        except OSError as e:
            body = repr(e).encode()
        finally:
            s.close()
        hits.append((ip, mac, body[:120]))
    return hits


def mdns_snoop(seconds=20):
    grp = socket.inet_aton("224.0.0.251")
    found = {}
    for attempt in range(2):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                pass
            s.bind(("", 5353))
            mreq = grp + socket.inet_aton("0.0.0.0")
            fcntl.ioctl(s.fileno(), 0x1127, mreq)  # IP_ADD_MEMBERSHIP (23 on most platforms)
        except OSError as e:
            print("mDNS listener unavailable:", e)
            return found
        s.settimeout(1.0)
        end = time.time() + seconds
        while time.time() < end:
            try:
                data, _ = s.recvfrom(4096)
            except socket.timeout:
                continue
            low = data.lower()
            for token in (b"_ewelink", b"_weblink", b"e-we", b"sonoff", b"itefan", b"_ez-us"):
                if token in low:
                    found[token.decode(errors="replace")] = found.get(token.decode(errors="replace"), 0) + 1
        s.close()
        if found:
            break
    return found


print("=== ARP table size:", len(arp_hosts()))
print("=== TCP 8081 probes (eWeLink LAN API):")
hits = probe_8081(arp_hosts())
if not hits:
    print("   nobody on 8081 among ARP hosts")
for ip, mac, body in hits:
    txt = body.decode(errors="replace").replace("\r", " ").replace("\n", " ")
    print("   ", MASK(ip), "mac", mac[:8] + ":**", "->", txt[:100])
print("=== mDNS announcements seen in ~20 s:")
for tok, n in mdns_snoop().items():
    print("   ", tok, "seen", n, "time(s)")
