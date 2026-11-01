#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Does the drawing actually move? Machine measurement, no judgement.

Two independent facts, stored separately:
  1. declared animation  — does the model's own file contain animation instructions
     (SMIL <animate>/<animateTransform>/<animateMotion>, CSS @keyframes / animation:,
     CSS transition, JS requestAnimationFrame / setInterval)?
  2. observed motion     — the page is rendered in isolated Chrome (network blocked)
     and screenshots are taken at several timestamps; pixel differences between them
     prove whether pixels change, how much, and in which region of the frame.

A file can declare animation and still not move (broken animation), or move without
declaring anything (JS). Both cases are reported, never averaged into one score.
Usage: python3 pel_motion.py <attempt_dir>
"""
import base64
import io
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request

OUT = os.path.abspath(sys.argv[1])
HTML = os.path.join(OUT, "index.html")
CHROME = os.environ.get("VIS_CHROME", "/usr/bin/google-chrome")
PROFILE = os.path.join(OUT, "chrome-motion-%d" % os.getpid())
SHOTS = int(os.environ.get("PEL_SHOTS", "6"))
STEP = float(os.environ.get("PEL_STEP", "0.45"))
os.makedirs(PROFILE, exist_ok=True)

FLAGS = [CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
         "--disable-extensions", "--disable-background-networking", "--disable-sync",
         "--metrics-recording-only", "--mute-audio", "--window-size=1280,720", "--hide-scrollbars",
         "--user-data-dir=" + PROFILE, "--remote-debugging-port=0", "--remote-allow-origins=*",
         "--host-resolver-rules=MAP * ~NOTFOUND",
         "--proxy-server=http=127.0.0.1:9;https=127.0.0.1:9;socks=127.0.0.1:9;socks5=127.0.0.1:9",
         "--proxy-bypass-list=<notmatched>", "--allow-file-access-from-files", "about:blank"]

from PIL import Image, ImageChops

PATTERNS = [("SMIL <animate>", "<animate"), ("SMIL <animateTransform>", "<animateTransform"),
            ("SMIL <animateMotion>", "<animateMotion"), ("CSS @keyframes", "@keyframes"),
            ("CSS animation property", "animation"), ("CSS transition", "transition:"),
            ("JS requestAnimationFrame", "requestAnimationFrame"), ("JS setInterval", "setInterval")]


def scan_declared(paths):
    found = {}
    for p in paths:
        if not os.path.exists(p):
            continue
        txt = open(p, encoding="utf-8", errors="replace").read()
        for name, pat in PATTERNS:
            n = txt.count(pat)
            if name == "CSS animation property":
                n = len(re.findall(r"animation(?:-name)?\s*:", txt))
            if n:
                found[name] = found.get(name, 0) + n
    return found


class WS:
    # transport copied from pel_validate.py (proven against Chrome 156 page targets)
    def __init__(self, url):
        m = re.match(r"ws://([^:/]+):(\d+)(/.*)", url)
        host, port, path = m.group(1), int(m.group(2)), m.group(3)
        self.s = socket.create_connection((host, port), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall(("GET %s HTTP/1.1\r\nHost: %s:%d\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n" % (path, host, port, key)).encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(4096)
        if b"101" not in buf.split(b"\r\n")[0]:
            raise RuntimeError("handshake failed")
        self.buf = buf.split(b"\r\n\r\n", 1)[1]
        self.id = 0
        self.pending = {}

    def send(self, method, params=None):
        self.id += 1
        mid = self.id
        data = json.dumps({"id": mid, "method": method, "params": params or {}}).encode()
        mask = os.urandom(4)
        n = len(data)
        head = b"\x81"
        if n < 126:
            head += bytes([0x80 | n])
        elif n < 65536:
            head += bytes([0x80 | 126]) + n.to_bytes(2, "big")
        else:
            head += bytes([0x80 | 127]) + n.to_bytes(8, "big")
        self.s.sendall(head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))
        return mid

    def _frame(self):
        while len(self.buf) < 2:
            self.buf += self.s.recv(65536)
        b0, b1 = self.buf[0], self.buf[1]
        ln = b1 & 0x7F
        off = 2
        if ln == 126:
            while len(self.buf) < 4:
                self.buf += self.s.recv(65536)
            ln = int.from_bytes(self.buf[2:4], "big")
            off = 4
        elif ln == 127:
            while len(self.buf) < 10:
                self.buf += self.s.recv(65536)
            ln = int.from_bytes(self.buf[2:10], "big")
            off = 10
        while len(self.buf) < off + ln:
            self.buf += self.s.recv(65536)
        pay = self.buf[off:off + ln]
        self.buf = self.buf[off + ln:]
        return pay

    def pump(self, t):
        self.s.settimeout(t)
        try:
            while True:
                try:
                    m = json.loads(self._frame().decode("utf-8", "ignore"))
                except Exception:
                    break
                if "id" in m:
                    self.pending[m["id"]] = m
        except Exception:
            pass

    def call(self, method, params=None, timeout=15):
        mid = self.send(method, params)
        end = time.time() + timeout
        while time.time() < end:
            if mid in self.pending:
                return self.pending.pop(mid)
            self.pump(0.3)
        return {}


def page_ws(port):
    end = time.time() + 25
    while time.time() < end:
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/json/list" % port, timeout=3) as r:
                for t in json.load(r):
                    if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
                        return t["webSocketDebuggerUrl"]
        except Exception:
            pass
        time.sleep(0.25)
    raise RuntimeError("no page target")


def diff_stats(a, b):
    """Changed pixels, fraction, worst channel delta, motion region.

    The exact bounding box of any difference is taken at full resolution
    (ImageChops + getbbox). The percentages and the 8x5 tile map are measured on a
    160x90 downsampled difference image — that is stated in the JSON so nobody reads
    it as a per-pixel census of the frame.
    """
    d = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
    W, H = d.size
    exact_bbox = d.getbbox()
    small = d.resize((160, 90))
    px = list(small.getdata())
    changed = 0
    worst = 0
    gx, gy = 8, 5
    tiles = set()
    for y in range(90):
        row = y * 160
        for x in range(160):
            r, g, bb = px[row + x]
            m = r if r >= g and r >= bb else (g if g >= bb else bb)
            if m > worst:
                worst = m
            if m > 20:
                changed += 1
                tiles.add((x * gx // 160, y * gy // 90))
    total = 160 * 90
    bbox = None
    if tiles:
        xs = [t[0] for t in tiles]
        ys = [t[1] for t in tiles]
        bbox = [min(xs) * W // gx, min(ys) * H // gy, (max(xs) + 1) * W // gx, (max(ys) + 1) * H // gy]
    return {"changed_pixels_downscaled": changed, "changed_pct": round(100.0 * changed / total, 3),
            "max_channel_delta": worst, "tiles_moving": len(tiles),
            "moving_bbox_tiles": bbox, "moving_bbox_exact": exact_bbox,
            "measured_on": "160x90 downsampled difference image; exact bbox from full frame"}


def main():
    declared = scan_declared([os.path.join(OUT, "art.svg"), HTML,
                              os.path.join(OUT, "raw_response.txt")])
    chrome = subprocess.Popen(FLAGS, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                              stderr=open(os.path.join(OUT, "chrome_motion.log"), "wb"))
    pf = os.path.join(PROFILE, "DevToolsActivePort")
    port = None
    end = time.time() + 25
    while time.time() < end:
        if chrome.poll() is not None:
            raise RuntimeError("chrome died exit=%s" % chrome.poll())
        if os.path.exists(pf):
            port = int(open(pf).read().splitlines()[0])
            break
        time.sleep(0.25)
    if port is None:
        raise RuntimeError("no DevToolsActivePort")
    ws = WS(page_ws(port))
    ws.send("Page.enable")  # fire
    ws.send("Runtime.enable")
    ws.send("Page.navigate", {"url": "file://" + HTML})
    time.sleep(1.2)
    shots = []
    for i in range(SHOTS):
        msg = ws.call("Page.captureScreenshot", {"format": "png"}, timeout=20)
        raw = base64.b64decode(msg.get("result", {}).get("data", ""))
        im = Image.open(io.BytesIO(raw))
        shots.append((round(i * STEP, 2), im))
        im.save(os.path.join(OUT, "motion_shot%d.png" % i))
        time.sleep(STEP)
    chrome.terminate()
    pairs = []
    for i in range(1, len(shots)):
        st = diff_stats(shots[i - 1][1], shots[i][1])
        st["between_s"] = [shots[i - 1][0], shots[i][0]]
        pairs.append(st)
    moving = [p for p in pairs if p["changed_pixels_downscaled"] > 50]
    res = {
        "attempt": os.path.basename(OUT),
        "declared_animation": declared,
        "declares_animation": bool(declared),
        "observed": {"shots": len(shots), "step_s": STEP, "pairs": pairs,
                     "moves": bool(moving),
                     "moving_pairs": len(moving),
                     "max_changed_pct": max([p["changed_pct"] for p in pairs] or [0]),
                     "moving_region": (moving[0]["moving_bbox_exact"] if moving else None)},
        "verdict_motion": "MOVES" if moving else "STATIC",
        "verdict_consistency": ("ANIMATES_AS_DECLARED" if (moving and declared) else
                                "DECLARED_BUT_DOES_NOT_MOVE" if (declared and not moving) else
                                "MOVES_WITHOUT_DECLARATION" if (moving and not declared) else
                                "STATIC_AS_DECLARED"),
        "environment": {"isolated_chrome": True, "network": "blocked (resolver + proxy sinks)",
                        "window": "1280x720"},
    }
    json.dump(res, open(os.path.join(OUT, "pel_motion.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("%s | declared: %s | observed: %s | %s" %
          (os.path.basename(OUT), ", ".join(declared) or "none", res["verdict_motion"],
           res["verdict_consistency"]))
    print("PEL_MOTION_DONE")


if __name__ == "__main__":
    main()
