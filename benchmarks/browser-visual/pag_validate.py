#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Voxel-pagoda benchmark validator (external artifact -> English).

The model's index.html is never edited. If it references CDN JavaScript
(which the published community prompt explicitly asks for), this validator:
  1. downloads each referenced CDN module once into <run>/vendor/ (CDN
     snapshot, sha256 recorded);
  2. writes index_offline.html — byte-identical except import/CDN URLs
     rewritten to the vendored copies — and renders THAT offline.
Everything else runs in an isolated Chrome (resolver + proxy closed).

Measured facts (never averaged into one number):
  * WebGL context: created? renderer string?
  * console errors / uncaught exceptions
  * real rAF frames per second of the page's own loop (rAF counter
    injected before page scripts run; the file itself is unchanged)
  * observed motion: screenshot differences over time
    (auto-rotating camera must move pixels; "spinning in the browser")
Usage: python3 pag_validate.py <attempt_dir>
"""
import base64
import datetime
import hashlib
import json
import os
import re
import socket
import struct
import subprocess
import sys
import time
import urllib.request

RUN = os.path.abspath(sys.argv[1])
HTML = os.path.join(RUN, "index.html")
CHROME = os.environ.get("VIS_CHROME", "/usr/bin/google-chrome")
PROFILE = os.path.join(RUN, "chrome-pag-%d" % os.getpid())
OBS_S = float(os.environ.get("PAG_OBS", "6"))
os.makedirs(PROFILE, exist_ok=True)

CDN_RE = re.compile(r"https?://[^\"'\s)]+/[^\"'\s)]*\.m?js")

FLAGS = [CHROME, "--headless=new", "--no-first-run", "--no-default-browser-check",
         "--disable-extensions", "--disable-background-networking", "--disable-sync",
         "--metrics-recording-only", "--mute-audio", "--window-size=1280,720",
         "--hide-scrollbars", "--enable-unsafe-swiftshader",
         "--use-gl=angle", "--use-angle=swiftshader", "--enable-webgl",
         "--user-data-dir=" + PROFILE, "--remote-debugging-port=0", "--remote-allow-origins=*",
         "--host-resolver-rules=MAP * ~NOTFOUND",
         "--proxy-server=http=127.0.0.1:9;https=127.0.0.1:9;socks=127.0.0.1:9;socks5=127.0.0.1:9",
         "--proxy-bypass-list=<notmatched>", "--allow-file-access-from-files", "about:blank"]


def vendor_cdn():
    """Snapshot CDN modules; return (offline_html_path, mapping).

    Handles both inline CDN URLs and import-map prefix mappings
    ("three/addons/" -> https://.../examples/jsm/), because the standard
    Three.js idiom uses prefix maps; without them the model's page would
    fail for harness reasons, not model reasons.
    """
    src = open(HTML, encoding="utf-8", errors="replace").read()
    mapping = {}
    vdir = os.path.join(RUN, "vendor")

    def fetch(u, name):
        os.makedirs(vdir, exist_ok=True)
        dest = os.path.join(vdir, name)
        sub_dir = os.path.dirname(dest)
        if sub_dir:
            os.makedirs(sub_dir, exist_ok=True)
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "pag-validate-snapshot"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            open(dest, "wb").write(data)
            mapping[u] = {"file": "vendor/" + name, "bytes": len(data),
                          "sha256": hashlib.sha256(data).hexdigest()[:16]}
            return True
        except Exception as e:
            mapping[u] = {"error": str(e)[:120]}
            return False

    out = src
    # 1) import map block
    mm = re.search(r'<script[^>]*type="importmap"[^>]*>(.*?)</script>', src, re.S | re.I)
    if mm:
        try:
            imap = json.loads(mm.group(1))
            imports = imap.get("imports", {})
            changed = False
            for key, url in list(imports.items()):
                if key != url:
                    if url.endswith("/"):
                        sub = re.sub(r"[^a-zA-Z0-9.-]", "_", url.split("//", 1)[1])[:60]
                        # download every specifier the page imports under this prefix
                        for spec in re.findall(r"from\s*['\"]([^'\"]+)['\"]", src):
                            if spec == key or spec.startswith(key if key.endswith("/") else key + "/"):
                                rel = spec[len(key):] if spec.startswith(key) else ""
                                u = url + rel
                                ok = fetch(u, sub + "/" + rel)
                                if ok:
                                    imports[key] = "./vendor/%s/" % sub
                                    changed = True
                    else:
                        name = re.sub(r"[^a-zA-Z0-9.-]", "_", url.split("//", 1)[1])[:80]
                        if fetch(url, name):
                            imports[key] = "./vendor/" + name
                            changed = True
            if changed:
                new_block = json.dumps({"imports": imports}, indent=1)
                out = out.replace(mm.group(1), new_block, 1)
        except Exception as e:
            mapping["_importmap_error"] = str(e)[:120]
    # 2) any remaining literal CDN .js URLs in the code
    for u in sorted(set(CDN_RE.findall(out))):
        if any(u == k for k in mapping):
            continue
        name = re.sub(r"[^a-zA-Z0-9.-]", "_", u.split("//", 1)[1])[:80]
        if fetch(u, name):
            out = out.replace(u, "./vendor/" + name)
    if not mapping:
        return HTML, mapping
    off = os.path.join(RUN, "index_offline.html")
    open(off, "w", encoding="utf-8").write(out)
    return off, mapping


class WS:  # same transport as pel_validate.py
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
        self.events = []

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
            head += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            head += bytes([0x80 | 127]) + struct.pack(">Q", n)
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

    def pump(self, t):
        self.s.settimeout(t)
        try:
            while True:
                try:
                    m = json.loads(self._frame().decode("utf-8", "ignore"))
                except Exception:
                    break
                if "method" in m:
                    self.events.append(m)
                else:
                    self.pending[m["id"]] = m
        except Exception:
            pass

    def wait(self, iid, timeout=20):
        end = time.time() + timeout
        while time.time() < end:
            if iid in self.pending:
                return self.pending.pop(iid)
            self.pump(0.3)
        return {}


from PIL import Image, ImageChops
import io as _io


def shot(ws):
    r = ws.wait(ws.send("Page.captureScreenshot", {"format": "png"}))
    return Image.open(_io.BytesIO(base64.b64decode(r.get("result", {}).get("data", "")))).convert("RGB")


def main():
    res = {"run": os.path.basename(RUN), "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
    off, mapping = vendor_cdn()
    res["cdn_snapshot"] = mapping
    res["rendered_file"] = os.path.basename(off)

    chrome = subprocess.Popen(FLAGS, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                              stderr=open(os.path.join(RUN, "chrome_pag.log"), "wb"))
    try:
        pf = os.path.join(PROFILE, "DevToolsActivePort")
        port = None
        end = time.time() + 25
        while time.time() < end:
            if chrome.poll() is not None:
                raise RuntimeError("chrome exit=%s" % chrome.returncode)
            if os.path.exists(pf):
                port = int(open(pf).read().splitlines()[0])
                break
            time.sleep(0.25)
        tgt = None
        for _ in range(40):
            try:
                with urllib.request.urlopen("http://127.0.0.1:%d/json/list" % port, timeout=3) as r:
                    for t in json.load(r):
                        if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
                            tgt = t["webSocketDebuggerUrl"]
                            break
            except Exception:
                pass
            if tgt:
                break
            time.sleep(0.25)
        ws = WS(tgt)
        ws.send("Page.enable")
        ws.send("Runtime.enable")
        ws.send("Log.enable")
        # rAF counter injected into every new document BEFORE page scripts run.
        ws.send("Page.addScriptToEvaluateOnNewDocument", {"source": """
            window.__pagRaf=0; const _r=window.requestAnimationFrame.bind(window);
            window.requestAnimationFrame=function(cb){window.__pagRaf++;return _r(cb);};
        """})
        iid = ws.send("Page.navigate", {"url": "file://" + off})
        ws.wait(iid)
        ws.pump(2.0)

        def ev(expr):
            r = ws.wait(ws.send("Runtime.evaluate", {"expression": expr, "returnByValue": True}))
            return r.get("result", {}).get("result", {}).get("value")

        gl = ev("""(() => {
          const c = document.createElement('canvas');
          const g = c.getContext('webgl2') || c.getContext('webgl');
          if (!g) return {ok:false};
          return {ok:true, version: g.getParameter(g.VERSION),
                  renderer: g.getParameter(g.RENDERER),
                  max_tex: g.getParameter(g.MAX_TEXTURE_SIZE)};
        })()""")
        res["webgl_probe_isolated"] = gl
        time.sleep(2.0)
        res["canvases"] = ev("[...document.querySelectorAll('canvas')].map(c=>({w:c.width,h:c.height}))")
        res["dom_text_len"] = ev("document.body.innerText.length")

        shots = [shot(ws)]
        t0 = time.time()
        while time.time() - t0 < OBS_S:
            time.sleep(0.5)
            shots.append(shot(ws))
        res["raf_frames_first_%ds" % int(OBS_S)] = ev("window.__pagRaf")
        res["observed"] = {"shots": len(shots)}
        pcts = []
        for i in range(1, len(shots)):
            d = ImageChops.difference(shots[i - 1], shots[i])
            bb = d.getbbox()
            small = d.resize((160, 90))
            px = list(small.getdata())
            ch = sum(1 for (r, g, b) in px if max(r, g, b) > 20)
            pcts.append(round(100.0 * ch / (160 * 90), 3))
        res["observed"]["moving_pct_per_step"] = pcts
        res["observed"]["max_moving_pct"] = max(pcts) if pcts else 0
        res["observed"]["spinning"] = res["observed"]["max_moving_pct"] > 0.5
        shots[0].save(os.path.join(RUN, "screenshot.png"))

        errors = [e.get("message", {}).get("text", "") for e in ws.events
                  if e.get("method") == "Log.entryAdded" and e["params"]["entry"].get("level") == "error"]
        excs = [e["params"].get("exceptionDetails", {}).get("exception", {}).get("description", "")
                or e["params"].get("exceptionDetails", {}).get("text", "")
                for e in ws.events if e.get("method") == "Runtime.exceptionThrown"]
        res["console_errors"] = errors[:6]
        res["exceptions"] = excs[:6]
        nonfile = []
        for e in ws.events:
            if e.get("method") == "Network.requestWillBeSent":
                u = e["params"]["request"]["url"]
                if not u.startswith("file://"):
                    nonfile.append(u)
        res["nonfile_network"] = nonfile[:6]
        res["nonfile_network_total"] = len(nonfile)

        ok_html = res["cdn_snapshot"] and all("file" in v for v in res["cdn_snapshot"].values())
        if res["exceptions"] or res["console_errors"]:
            res["verdict"] = "FAIL"
        elif res["observed"]["spinning"] and (res["canvases"] or []):
            res["verdict"] = "RENDERS_AND_SPINS"
        elif res["canvases"]:
            res["verdict"] = "RENDERS_STATIC"
        else:
            res["verdict"] = "FAIL"
    finally:
        chrome.kill()
        import shutil
        shutil.rmtree(PROFILE, ignore_errors=True)
    json.dump(res, open(os.path.join(RUN, "pag_validation.json"), "w"), indent=1, ensure_ascii=False)
    print(res["run"], res["verdict"], "raf=", res.get("raf_frames_first_%ds" % int(OBS_S)),
          "max_moving_pct=", res["observed"]["max_moving_pct"],
          "errors=", len(res["console_errors"]) + len(res["exceptions"]))


if __name__ == "__main__":
    main()
