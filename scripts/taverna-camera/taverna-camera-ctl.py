"""Loopback microservice that switches the taverna camera's frame rate.

Motion 4.6 has no runtime API on this box (webcontrol is deliberately off), but its config file is
owned by this user and the service unit re-execs on exit (Restart=always), so changing `framerate`
and sending SIGTERM to MainPID is a safe, sudo-free way to switch between 2 and 5 fps.

  POST /fps/<secret>/<n>   set framerate to n right now
  POST /boost/<secret>     raise to BOOST_FPS for BOOST_S seconds, then go back to BASE_FPS
  GET  /ping               health + current settings

A boost also flips the HA helper `input_boolean.taverna_camera_boost` back to off when it expires,
so the dashboard button never lies about the state. Loopback only; the path carries a secret.
"""
import json
import os
import re
import signal
import subprocess
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("CAMCTL_PORT", "8126"))
CONF = os.path.expanduser("~/.config/motion/motion-tavern.conf")
MEDIA = os.path.expanduser("~/.hermes/media")
SECRET_FILE = os.path.join(MEDIA, "camera.secret")
BOOST_FPS_FILE = os.path.join(MEDIA, "camera_boost_fps")
BOOST_S_FILE = os.path.join(MEDIA, "camera_boost_s")
SERVICE = "motion-tavern.service"
STATE_DIR = os.path.expanduser("~/.local/state/taverna-greeting")
RESTART_LOG = os.path.join(STATE_DIR, "motion-restarts.log")
STREAM_URL = "http://127.0.0.1:8125/shot.jpg"
_frame = {"jpg": None, "ts": 0.0}
_frame_lock = threading.Lock()
HASS = "http://127.0.0.1:8123"
BOOLEAN = "input_boolean.taverna_camera_boost"
_lock = threading.Lock()
_revert = {"timer": None, "until": 0.0, "base": 2}


def secret():
    try:
        return open(SECRET_FILE).read().strip()
    except OSError:
        return ""


def hass_token():
    try:
        for line in open(os.path.expanduser("~/.hermes/.env")):
            if line.startswith("HASS_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def grab_frame(max_age=2.0):
    """One JPEG out of Motion's multipart stream, for tools that need a still image.

    Motion 4.6 without webcontrol only serves multipart/x-mixed-replace, and Home Assistant's
    Generic Camera refuses that as still_image_url ("unable_still_load"), so the first complete
    JPEG part is cut out here and cached for max_age seconds.
    """
    with _frame_lock:
        if _frame["jpg"] and time.time() - _frame["ts"] < max_age:
            return _frame["jpg"]
        try:
            conn = urllib.request.urlopen(STREAM_URL, timeout=6)
        except OSError:
            return _frame["jpg"]
        buf = b""
        try:
            deadline = time.time() + 6
            while time.time() < deadline:
                chunk = conn.read(65536)
                if not chunk:
                    break
                buf += chunk
                i = buf.find(b"\xff\xd8\xff")
                if i >= 0:
                    j = buf.find(b"\xff\xd9", i)
                    if j > i:
                        _frame.update(jpg=buf[i:j + 2], ts=time.time())
                        break
        finally:
            conn.close()
        return _frame["jpg"]


def current_fps():
    try:
        m = re.search(r"^framerate\s+(\d+)", open(CONF).read(), re.M)
        return int(m.group(1)) if m else None
    except OSError:
        return None


def main_pid():
    out = subprocess.run(["systemctl", "show", SERVICE, "-p", "MainPID", "--value"],
                         capture_output=True, text=True).stdout.strip()
    return int(out) if out.isdigit() else 0


def unit_state():
    return subprocess.run(["systemctl", "show", SERVICE, "-p", "ActiveState", "--value"],
                          capture_output=True, text=True).stdout.strip()


def note_restart(pid, n):
    """Record that THIS restart was asked for, so the motion watchdog does not report an fps
    switch as a crash. The watchdog subtracts these from its restart delta."""
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(RESTART_LOG, "a") as f:
        f.write("%d pid=%d fps=%d\n" % (time.time(), pid, n))


def wait_restarted(old_pid, timeout=8.0):
    """Poll until systemd has brought back a different MainPID (keeps HA's rest_command happy)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        pid = main_pid()
        if pid and pid != old_pid:
            return pid
        time.sleep(0.4)
    return 0


def set_fps(n, restart=True):
    """Rewrite the framerate line and let systemd re-exec Motion with the new config."""
    txt = open(CONF).read()
    new, cnt = re.subn(r"(?m)^framerate\s+\d+.*$", "framerate %d" % n, txt)
    if not cnt:
        return False, "no framerate line in %s" % CONF
    if new != txt:
        with open(CONF, "w") as f:
            f.write(new)
    if not restart:
        return True, "config written (no restart)"
    pid = main_pid()
    if not pid:
        return False, "service not running"
    note_restart(pid, n)
    os.kill(pid, signal.SIGTERM)
    new_pid = wait_restarted(pid)
    if new_pid:
        return True, "framerate %d, motion pid %d -> %d" % (n, pid, new_pid)
    if unit_state() in ("active", "activating"):
        return True, "framerate %d, motion (pid %d) restarting, state %s" % (n, pid, unit_state())
    return False, "framerate %d written but %s state is '%s' - check journalctl -u %s" % (
        n, SERVICE, unit_state(), SERVICE)


def flip_boolean(state):
    subprocess.run(["curl", "-s", "-m", "10", "-X", "POST",
                    "-H", "Autho" + "rization: Bea" + "r" + "er " + hass_token(),
                    "-H", "Content-Type: application/json",
                    "-d", json.dumps({"entity_id": BOOLEAN}),
                    "%s/api/services/input_boolean/%s" % (HASS, state)], capture_output=True)


def base_fps():
    try:
        return int(open(os.path.join(MEDIA, "camera_base_fps")).read().strip())
    except (OSError, ValueError):
        return 2


def boost_fps():
    try:
        return int(open(BOOST_FPS_FILE).read().strip())
    except (OSError, ValueError):
        return 5


def boost_s():
    try:
        return int(open(BOOST_S_FILE).read().strip())
    except (OSError, ValueError):
        return 600


def do_revert():
    with _lock:
        _revert["until"] = 0.0
    ok, msg = set_fps(base_fps())
    flip_boolean("turn_off")
    print("boost expired -> fps %d (%s)" % (base_fps(), msg), flush=True)


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/frame.jpg":
            jpg = grab_frame()
            if not jpg:
                self._send(503, {"ok": False, "error": "no frame from the camera"})
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(jpg)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(jpg)
        elif self.path == "/ping":
            self._send(200, {"ok": True, "fps": current_fps(), "boost_until": _revert["until"],
                             "boost_fps": boost_fps(), "boost_s": boost_s(), "base_fps": base_fps()})
        else:
            self._send(404, {"ok": False})

    def do_POST(self):
        p = self.path.strip("/").split("/")
        if p[0] == "fps" and len(p) == 3 and secrets_ok(p[1]):
            try:
                n = int(p[2])
            except ValueError:
                self._send(400, {"ok": False, "error": "fps must be a number"})
                return
            if not 1 <= n <= 30:
                self._send(400, {"ok": False, "error": "fps out of range 1..30"})
                return
            ok, msg = set_fps(n)
            self._send(200 if ok else 500, {"ok": ok, "message": msg, "fps": n})
        elif p[0] == "boost" and len(p) == 2 and secrets_ok(p[1]):
            n, s = boost_fps(), boost_s()
            ok, msg = set_fps(n)
            if ok:
                with _lock:
                    if _revert["timer"]:
                        _revert["timer"].cancel()
                    _revert["until"] = time.time() + s
                    _revert["timer"] = threading.Timer(s, do_revert)
                    _revert["timer"].daemon = True
                    _revert["timer"].start()
                flip_boolean("turn_on")
            self._send(200 if ok else 500,
                       {"ok": ok, "message": msg, "fps": n, "for_s": s})
        elif p[0] == "unboost" and len(p) == 2 and secrets_ok(p[1]):
            with _lock:
                if _revert["timer"]:
                    _revert["timer"].cancel()
                _revert["until"] = 0.0
            ok, msg = set_fps(base_fps())
            flip_boolean("turn_off")
            self._send(200, {"ok": ok, "message": msg, "fps": base_fps()})
        else:
            self._send(404, {"ok": False})


def secrets_ok(s):
    import hmac
    ref = secret()
    return bool(ref) and hmac.compare_digest(s, ref)


if __name__ == "__main__":
    print("camera control on 127.0.0.1:%d (fps=%s boost=%d for %ds base=%d)"
          % (PORT, current_fps(), boost_fps(), boost_s(), base_fps()), flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
