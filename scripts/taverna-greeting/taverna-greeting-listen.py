"""Local HTTP trigger that speaks the taverna greeting and then plays quiet internet radio.

Home Assistant (host networking) calls POST /greet/<secret> when the taverna light turns on:
this plays the Italian voice clip out of the analog Line Out and then starts a low-bitrate
radio stream as background music. POST /stop/<secret> (light turned off) ends the music.

Loopback only, path carries a secret, repeats inside the cooldown window are ignored, and the
music is capped so a forgotten "on" cannot stream forever.
"""
import json
import os
import secrets
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("GREET_PORT", "8124"))
MEDIA = os.path.expanduser("~/.hermes/media")
VOICE = os.environ.get("GREET_CLIP", os.path.join(MEDIA, "greeting_voice.wav"))
SECRET_FILE = os.environ.get("GREET_SECRET_FILE", os.path.join(MEDIA, "greet.secret"))
RADIO_URL_FILE = os.path.join(MEDIA, "radio.url")
IMAGE = "taverna-audio:latest"
DEV = os.environ.get("GREET_DEVICE", "hw:0,0")
GAIN_FILE = os.path.join(MEDIA, "radio_gain")


def radio_gain():
    """Background music level in dB, so it can be turned down without touching code."""
    try:
        return open(GAIN_FILE).read().strip() or "-24"
    except OSError:
        return os.environ.get("GREET_RADIO_GAIN", "-24")
COOLDOWN_FILE = os.path.join(MEDIA, "greet_cooldown")


def cooldown_s():
    """Seconds between greetings. Kept in a file: 300 s once swallowed a real guest's greeting
    that arrived 80 s after a test, and the operator wants a greeting per visitor."""
    try:
        return int(open(COOLDOWN_FILE).read().strip())
    except (OSError, ValueError):
        return int(os.environ.get("GREET_COOLDOWN", "90"))
MAX_RADIO_S = int(os.environ.get("GREET_MAX_RADIO_S", "1800"))
VOICE_TIMEOUT_S = 60

_lock = threading.Lock()
_state = {"last_greet": 0.0, "greets": 0, "radio_since": 0.0, "radio_stop": None}
_radio = None


def secret():
    try:
        return open(SECRET_FILE).read().strip()
    except OSError:
        return ""


def radio_url():
    try:
        return open(RADIO_URL_FILE).read().strip()
    except OSError:
        return ""


def sweep_players():
    """Stop any audio container left behind by a previous listener instance."""
    ids = subprocess.run(["docker", "ps", "--filter", "ancestor=" + IMAGE, "-q"],
                         capture_output=True, text=True).stdout.split()
    for c in ids:
        subprocess.run(["docker", "stop", c], capture_output=True, timeout=30)
    if ids:
        print("stopped %d orphan audio container(s)" % len(ids), flush=True)


def stop_radio():
    global _radio
    sweep_players()
    p = _radio
    if p and p.poll() is None:
        try:
            p.send_signal(signal.SIGTERM)
            for _ in range(20):
                if p.poll() is not None:
                    break
                time.sleep(0.2)
            if p.poll() is None:
                p.kill()
        except Exception as ex:
            print("radio stop failed: %s" % ex, flush=True)
    _radio = None
    _state["radio_since"] = 0.0


def run_voice():
    cmd = ["docker", "run", "--rm", "--device", "/dev/snd",
           "-v", os.path.dirname(VOICE) + ":/m:ro", IMAGE, "aplay", "-q", "-D", DEV,
           "/m/" + os.path.basename(VOICE)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=VOICE_TIMEOUT_S)
        print("voice rc=%s %s" % (r.returncode, (r.stdout + r.stderr).strip()[-160:]), flush=True)
    except Exception as ex:
        print("voice failed: %s: %s" % (type(ex).__name__, ex), flush=True)


def run_radio():
    global _radio
    url = radio_url()
    if not url:
        print("no radio url in %s" % RADIO_URL_FILE, flush=True)
        return
    cmd = ["docker", "run", "--rm", "--device", "/dev/snd", IMAGE,
           "ffmpeg", "-hide_banner", "-loglevel", "error",
           "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5",
           "-i", url, "-af", "volume=%s" % radio_gain(),
           "-ar", "48000", "-ac", "2", "-flush_packets", "1", "-f", "alsa", DEV]
    try:
        _radio = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    except Exception as ex:
        print("radio spawn failed: %s: %s" % (type(ex).__name__, ex), flush=True)
        return
    _state["radio_since"] = time.time()
    threading.Timer(MAX_RADIO_S, stop_radio).start()
    err = _radio.stderr.read() if _radio.stderr else ""
    _radio.wait()
    rc = _radio.returncode
    print("radio ended rc=%s since=%s err=%s" % (
        rc, time.strftime("%H:%M:%S", time.localtime(_state["radio_since"])), err.strip()[-200:]),
        flush=True)
    _radio = None
    _state["radio_since"] = 0.0


def greet_flow():
    run_voice()
    if time.time() - _state["last_greet"] < 3:
        return
    run_radio()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _route(self):
        parts = [p for p in self.path.split("?")[0].split("/") if p]
        if len(parts) != 2 or parts[0] not in ("greet", "stop"):
            return None, None
        if not secrets.compare_digest(parts[1], secret() or "unset"):
            return None, "forbidden"
        return parts[0], None

    def do_GET(self):
        if self.path.startswith("/ping"):
            self._send(200, {"ok": True, "greets": _state["greets"],
                             "voice": os.path.basename(VOICE), "radio": radio_url(),
                             "radio_playing": bool(_radio and _radio.poll() is None),
                             "radio_gain_db": radio_gain(), "cooldown_s": cooldown_s()})
        else:
            self._send(404, {"error": "unknown path"})

    def do_POST(self):
        action, deny = self._route()
        if deny:
            print("%s rejected from %s" % (time.strftime("%H:%M:%S"), self.client_address[0]), flush=True)
            self._send(403, {"error": deny})
            return
        if action == "stop":
            print("%s stop requested" % time.strftime("%H:%M:%S"), flush=True)
            stop_radio()
            self._send(200, {"radio": "stopped"})
            return
        now = time.time()
        with _lock:
            since = now - _state["last_greet"]
            if since < cooldown_s():
                print("%s greet SKIPPED cooldown (%.0f s of %d s)"
                      % (time.strftime("%H:%M:%S"), since, cooldown_s()), flush=True)
                self._send(200, {"skipped": "cooldown", "seconds_since_last": round(since, 1)})
                return
            _state["last_greet"] = now
            _state["greets"] += 1
        print("%s greet ACCEPTED (voice + radio)" % time.strftime("%H:%M:%S"), flush=True)
        threading.Thread(target=greet_flow, daemon=True).start()
        self._send(202, {"greeting": os.path.basename(VOICE), "then_radio": radio_url()})

    def log_message(self, fmt, *args):
        pass


def main():
    for path, why in ((VOICE, "voice clip missing"), (secret(), "secret missing"),
                      (radio_url(), "no radio url")):
        if not path:
            print("%s" % why, flush=True)
            return 1
    sweep_players()
    print("listening on 127.0.0.1:%d | voice=%s | radio=%s @ %s dB | cooldown %ds | radio cap %ds"
          % (PORT, VOICE, radio_url(), radio_gain(), cooldown_s(), MAX_RADIO_S), flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    sys.exit(main())
