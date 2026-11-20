"""Enable the eWeLink integration's diagnostic sensors for the tavern relay.

They ship disabled, so the Wi-Fi level (rssi) and the transport (cloud/local) of the relay are
invisible exactly when they matter - the relay drops with cloud 504s and nothing records the signal.
Enables by entity id, then prints the resulting states.
"""
import asyncio
import json
import os
import websockets

TOKEN = open(os.path.expanduser("~/.config/motion/hass-token")).read().strip()
URL = "ws://127.0.0.1:8123/api/websocket"
DESIRED = [
    "sensor.taverna_basicr4_sonoff_1002bd4e01_rssi",
    "sensor.taverna_basicr4_sonoff_1002bd4e01_connection",
]


async def main():
    async with websockets.connect(URL, max_size=None) as ws:
        if json.loads(await ws.recv())["type"] != "auth_required":
            raise SystemExit("no auth_required")
        await ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
        if json.loads(await ws.recv())["type"] != "auth_ok":
            raise SystemExit("auth failed")
        seq = [0]

        async def cmd(t, **kw):
            seq[0] += 1
            await ws.send(json.dumps({"id": seq[0], "type": t, **kw}))
            while True:
                m = json.loads(await ws.recv())
                if m.get("id") == seq[0]:
                    return m

        reg = (await cmd("config/entity_registry/list")).get("result", [])
        rel = [e for e in reg if "basicr4" in e["entity_id"]]
        print("basicr4 entities in the registry:")
        for e in sorted(rel, key=lambda x: x["entity_id"]):
            print("   %-62s disabled_by=%s" % (e["entity_id"], e.get("disabled_by")))

        for want in DESIRED:
            hit = next((e for e in rel if e["entity_id"] == want), None)
            if not hit:
                print("not in registry:", want)
                continue
            if hit.get("disabled_by"):
                r = await cmd("config/entity_registry/update", entity_id=want, disabled_by=None)
                print("enable", want, "->", "ok" if "result" in r else r)
        sub = await cmd("config/entity_registry/get", entity_id=DESIRED[0])
        print("registry says:", DESIRED[0], "disabled_by =", (sub.get("result") or {}).get("disabled_by"))


asyncio.run(main())
