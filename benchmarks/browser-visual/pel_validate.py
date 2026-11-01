#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Isolated validation of one pelican-benchmark attempt (SVG drawing).

Machine checks only — no aesthetic judgement here:
  * page loads in headless Chrome, network hard-blocked (resolver + proxy sinks);
  * console errors / uncaught exceptions counted;
  * any non-file:// request counted (must be 0);
  * SVG is present in DOM and has geometry;
  * screenshot taken, then pixel analysis: ink coverage, colour count, ink bbox,
    wheel-like circles taken from SVG geometry (radius + aligned centres).
Verdicts: FAIL / STRUCT_OK / STRUCT_SUSPECT. The human/model visual judgement of
"does this actually look like a pelican on a bicycle" is stored separately by the
scoring script, never merged into these machine checks.
Usage: python3 pel_validate.py <attempt_dir>
"""
import base64
import json
import os
import re
import socket
import struct
import subprocess
import sys
import time
import urllib.request

OUT = sys.argv[1]
HTML = os.path.join(OUT, "index.html")
CHROME = os.environ.get("VIS_CHROME", "/usr/bin/google-chrome")
FFMPEG = os.environ.get("FFMPEG", "/path/to/ffmpeg")
PROFILE = os.path.join(OUT, "chrome-profile-%d" % os.getpid())
os.makedirs(PROFILE, exist_ok=True)

flags = [CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
         "--disable-extensions", "--disable-background-networking", "--disable-sync",
         "--metrics-recording-only", "--mute-audio", "--window-size=1280,720", "--hide-scrollbars",
         "--user-data-dir=" + PROFILE, "--remote-debugging-port=0", "--remote-allow-origins=*",
         "--host-resolver-rules=MAP * ~NOTFOUND",
         "--proxy-server=http=127.0.0.1:9;https=127.0.0.1:9;socks=127.0.0.1:9;socks5=127.0.0.1:9",
         "--proxy-bypass-list=<notmatched>", "--allow-file-access-from-files", "about:blank"]
clog = open(os.path.join(OUT, "chrome_stderr.log"), "wb")
chrome = subprocess.Popen(flags, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=clog)


def page_ws_url(port):
    """Browser-level socket does not speak Page/Runtime — attach to the real page target."""
    for _ in range(40):
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/json/list" % port, timeout=3) as r:
                tg = json.load(r)
            for t in tg:
                if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
                    return t["webSocketDebuggerUrl"]
        except Exception:
            pass
        time.sleep(0.25)
    raise RuntimeError("no page target")


def devtools_url():
    pf = os.path.join(PROFILE, "DevToolsActivePort")
    end = time.time() + 25
    while time.time() < end:
        if chrome.poll() is not None:
            raise RuntimeError("chrome died, exit=%s" % chrome.poll())
        if os.path.exists(pf):
            port = int(open(pf).read().splitlines()[0])
            try:
                with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % port, timeout=3) as r:
                    v = json.load(r)
                if v.get("webSocketDebuggerUrl"):
                    return port, v.get("Browser", "")
            except Exception:
                pass
        time.sleep(0.25)
    raise RuntimeError("no DevToolsActivePort")


class WS:
    def __init__(self, url):
        m = re.match(r"ws://([^:/]+):(\d+)(/.*)", url)
        host, port, path = m.group(1), int(m.group(2)), m.group(3)
        self.s = socket.create_connection((host, port), timeout=20)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall(("GET %s HTTP/1.1\r\nHost: %s:%d\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n" % (path, host, port, key)).encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(4096)
        if b"101" not in buf.split(b"\r\n")[0]:
            raise RuntimeError("handshake failed")
        self.buf = buf.split(b"\r\n\r\n", 1)[1]

    def send(self, obj):
        data = json.dumps(obj).encode()
        mask = os.urandom(4)
        n = len(data)
        head = b"\x81"
        if n < 126:
            head += bytes([0x80 | n])
        elif n < 65536:
            head += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            head += bytes([0x80 | 127]) + struct.pack(">Q", n)
        self.s.sendall(head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def _frame(self):
        while len(self.buf) < 2:
            self.buf += self.s.recv(65536)
        b0, b1 = self.buf[0], self.buf[1]
        ln = b1 & 0x7F
        off = 2
        if ln == 126:
            while len(self.buf) < 4:
                self.buf += self.s.recv(65536)
            ln = struct.unpack(">H", self.buf[2:4])[0]
            off = 4
        elif ln == 127:
            while len(self.buf) < 10:
                self.buf += self.s.recv(65536)
            ln = struct.unpack(">Q", self.buf[2:10])[0]
            off = 10
        while len(self.buf) < off + ln:
            self.buf += self.s.recv(65536)
        pay = self.buf[off:off + ln]
        self.buf = self.buf[off + ln:]
        return pay

    def recv(self):
        try:
            return json.loads(self._frame().decode("utf-8", "ignore"))
        except Exception:
            return None


PORT, BROWSER = devtools_url()
ws = WS(page_ws_url(PORT))
_id = [0]
events = []


def send(method, params=None):
    _id[0] += 1
    ws.send({"id": _id[0], "method": method, "params": params or {}})
    return _id[0]


def pump(t=0.25):
    ws.s.settimeout(t)
    try:
        while True:
            m = ws.recv()
            if not m:
                break
            if "method" in m:
                events.append(m)
            else:
                pending[m["id"]] = m
    except Exception:
        pass


pending = {}


def wait(iid, timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        if iid in pending:
            return pending.pop(iid)
        pump(0.3)
    return {}


send("Network.enable")
send("Runtime.enable")
send("Log.enable")
send("Page.enable")
iid = send("Page.navigate", {"url": "file://" + os.path.abspath(HTML)})
wait(iid)
pump(3.0)
time.sleep(1.5)
pump(1.0)

probe = """(() => {
  const svgs = document.querySelectorAll('svg');
  if (!svgs.length) return {svg_count: 0};
  const s = svgs[0];
  const r = s.getBoundingClientRect();
  return {svg_count: svgs.length,
          nodes: s.querySelectorAll('*').length,
          w: Math.round(r.width), h: Math.round(r.height),
          x: Math.round(r.x), y: Math.round(r.y),
          body_scroll: [document.body.scrollWidth, document.body.scrollHeight]};
})()"""
iid = send("Runtime.evaluate", {"expression": probe, "returnByValue": True})
pr = wait(iid).get("result", {}).get("result", {}).get("value") or {}

iid = send("Page.captureScreenshot", {"format": "png"})
shot = wait(iid, 20).get("result", {}).get("data")
shot_path = os.path.join(OUT, "screenshot.png")
if shot:
    open(shot_path, "wb").write(base64.b64decode(shot))

# second shot after a pause: SVG is static by design, but this proves no hidden animation churn
time.sleep(2.0)
iid = send("Page.captureScreenshot", {"format": "png"})
shot2 = wait(iid, 20).get("result", {}).get("data")
shot2_path = os.path.join(OUT, "screenshot_t2.png")
if shot2:
    open(shot2_path, "wb").write(base64.b64decode(shot2))

console_errors, exceptions, net_nonfile = [], [], []
for e in events:
    m = e.get("method")
    if m == "Log.entryAdded":
        en = e["params"]["entry"]
        if en.get("level") == "error":
            console_errors.append(en.get("text", "")[:200])
    elif m == "Runtime.exceptionThrown":
        d = e["params"]["exceptionDetails"]
        exceptions.append((d.get("text") or "")[:200])
    elif m == "Network.requestWillBeSent":
        u = e["params"]["request"].get("url", "")
        if not u.startswith("file://") and not u.startswith("data:"):
            net_nonfile.append(u[:120])

chrome.terminate()
try:
    chrome.wait(timeout=5)
except Exception:
    chrome.kill()

# --- pixel analysis on the screenshot ---
pix = {}
if os.path.exists(shot_path):
    from PIL import Image
    im = Image.open(shot_path).convert("RGB")
    W, H = im.size
    px = im.load()
    bg = px[2, 2]
    ink = 0
    cols = {}
    minx, miny, maxx, maxy = W, H, 0, 0
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            r, g, b = px[x, y]
            if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > 40:
                ink += 1
                cols[(r // 32, g // 32, b // 32)] = cols.get((r // 32, g // 32, b // 32), 0) + 1
                if x < minx:
                    minx = x
                if y < miny:
                    miny = y
                if x > maxx:
                    maxx = x
                if y > maxy:
                    maxy = y
    total = (W // 2 + 1) * (H // 2 + 1)
    pix = {"size": [W, H], "bg_rgb": list(bg),
           "ink_frac": round(ink / float(total), 4),
           "color_buckets": len(cols),
           "ink_bbox": [minx, miny, maxx, maxy] if ink else None}
    # is the second shot identical? (static vector drawing => expected identical)
    if os.path.exists(shot2_path):
        im2 = Image.open(shot2_path).convert("RGB")
        p2 = im2.load()
        diff = 0
        for y in range(0, H, 8):
            for x in range(0, W, 8):
                a = px[x, y]
                b2 = p2[x, y]
                if abs(a[0] - b2[0]) + abs(a[1] - b2[1]) + abs(a[2] - b2[2]) > 24:
                    diff += 1
        pix["changed_blocks_t2"] = diff

# --- geometry inventory from the SVG source (no judgement) ---
geo = {}
svgp = os.path.join(OUT, "art.svg")
if os.path.exists(svgp):
    svg = open(svgp, encoding="utf-8", errors="ignore").read()
    radii = [float(v) for v in re.findall(r"<circle[^>]*\br\s*=\s*\"([0-9.]+)\"", svg)]
    radii += [float(v) for v in re.findall(r"<ellipse[^>]*\brx\s*=\s*\"([0-9.]+)\"", svg)]
    geo["circles_total"] = len(radii)
    geo["big_circle_radii"] = sorted([r for r in radii if r >= 25], reverse=True)[:8]
    cy = re.findall(r"<circle[^>]*\bcy\s*=\s*\"([0-9.]+)\"[^>]*\br\s*=\s*\"([0-9.]+)\"", svg)
    pairs = [(float(y), float(r)) for y, r in cy if float(r) >= 25]
    aligned = 0
    for i in range(len(pairs)):
        for j in range(i + 1, len(pairs)):
            if abs(pairs[i][0] - pairs[j][0]) <= max(6.0, 0.12 * pairs[i][1]) and \
               abs(pairs[i][1] - pairs[j][1]) <= 0.25 * pairs[i][1]:
                aligned += 1
    geo["wheel_like_aligned_pairs"] = aligned
    geo["lines"] = len(re.findall(r"<(?:line|path|polyline|polygon)\b", svg))
    geo["paths"] = len(re.findall(r"<path\b", svg))

blank = pix.get("ink_frac", 0) < 0.002
if not pr.get("svg_count"):
    verdict = "FAIL"
    why = "no <svg> in the rendered page"
elif exceptions or console_errors:
    verdict = "FAIL"
    why = "page threw errors"
elif blank:
    verdict = "FAIL"
    why = "render is blank (ink < 0.2%)"
elif geo.get("wheel_like_aligned_pairs", 0) >= 1 and geo.get("lines", 0) >= 3:
    verdict = "STRUCT_OK"
    why = "valid SVG renders; two wheel-like circles aligned; frame lines present"
else:
    verdict = "STRUCT_SUSPECT"
    why = "renders, but wheel/frame geometry is missing or misaligned"

res = {"verdict": verdict, "why": why,
       "dom_probe": pr, "console_errors": console_errors, "exceptions": exceptions,
       "net_nonfile": net_nonfile, "pixels": pix, "geometry": geo,
       "screenshot": shot_path, "chrome": BROWSER}
json.dump(res, open(os.path.join(OUT, "pel_validation.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(json.dumps({"dir": os.path.basename(OUT), "verdict": verdict, "why": why,
                  "nodes": pr.get("nodes"), "ink": pix.get("ink_frac"),
                  "colors": pix.get("color_buckets"), "big_circles": geo.get("big_circle_radii"),
                  "aligned_pairs": geo.get("wheel_like_aligned_pairs"),
                  "paths": geo.get("paths"), "err": len(console_errors) + len(exceptions),
                  "net": len(net_nonfile)}, ensure_ascii=False))
