"""Ask the LAN directly: does the tavern relay announce the eWeLink LAN API (mDNS), and what does it
answer on 8081?

The Sonoff integration finds local devices through the zeroconf type `_ewelink._tcp.local.`
(core/ewelink/local.py), so if the relay answers this query, cloud-free control is technically
available and the fix is Home Assistant's config, not hardware.
"""
import random
import socket
import struct
import sys
import time

QNAME = b"\x09_ewelink\x04_tcp\x05local\x00"
MULTICAST = "224.0.0.251"


def query(name_bytes, qtype=12):  # 12 = PTR
    tid = random.randint(0, 0xFFFF)
    head = struct.pack(">HHHHHH", tid, 0x0000, 1, 0, 0, 0)
    return head + name_bytes + struct.pack(">HH", qtype, 1)


def names(packet):
    """Crude label extraction - enough to see which devices answered."""
    out = []
    i = 0
    while i < len(packet):
        ln = packet[i]
        if 0 < ln < 64 and all(32 <= c < 127 for c in packet[i + 1:i + 1 + ln]):
            out.append(packet[i + 1:i + 1 + ln].decode("ascii", "replace"))
            i += 1 + ln
        else:
            i += 1
    return out


def a_records(packet):
    ips = []
    for i in range(len(packet) - 4):
        # A-record data rdata is 4 bytes; only report plausible private ranges
        b = packet[i:i + 4]
        if b[0] in (10, 172, 192, 169) and (b[0] != 172 or 16 <= b[1] <= 31):
            if b[0] == 192 or b[0] == 169 or b[0] == 10 or (b[0] == 172 and 16 <= b[1] <= 31):
                ips.append(".".join(str(x) for x in b))
    return ips


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", 5353))
    mreq = struct.pack("4s4s", socket.inet_aton(MULTICAST), socket.inet_aton("0.0.0.0"))
    s.setsockopt(socket.IPPROTO_IP, 35, mreq)  # IP_ADD_MEMBERSHIP
    pkt = query(QNAME)
    for _ in range(3):
        s.sendto(pkt, (MULTICAST, 5353))
        time.sleep(0.4)
    seen = {}
    end = time.time() + 12
    while time.time() < end:
        s.settimeout(1.0)
        try:
            data, addr = s.recvfrom(65535)
        except socket.timeout:
            continue
        lab = names(data)
        if any("_ewelink" in x.lower() or "ewelink" in x.lower() for x in lab):
            key = (addr[0], tuple(x for x in lab if "ewelink" in x.lower()))
            seen[key] = seen.get(key, 0) + 1
    s.close()
    if not seen:
        print("no _ewelink._tcp answers on the LAN (relays do not announce the local API here)")
    for (src, labels), n in seen.items():
        print("answer from", ".".join(src.split(".")[:3]) + ".*", "x", n, "->", labels)


main()
