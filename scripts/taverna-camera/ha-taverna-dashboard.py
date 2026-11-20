"""Finish the taverna camera presentation in Home Assistant over the WebSocket API:
name the camera, create the "Таверна" dashboard (metadata first) and save its card config.

HA 2026 notes: lovelace has no REST endpoints; lovelace/dashboards/create takes only the dashboard
metadata and the card config goes through lovelace/config/save.
"""
import asyncio
import json
import subprocess

import websockets

TOKEN = subprocess.run(["sh", "-c", "grep -m1 '^HASS_TOKEN=' ~/.hermes/.env | cut -d= -f2-"],
                       capture_output=True, text=True).stdout.strip().strip('"').strip("'")

ENT = "camera.127_0_0_1"
ENTRY = "01M7VZM5ADZJGSTGXVWTEWF8QS"
NAME = "Таверна: камера подвала"
LAM = "switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1"
URL = "taverna-cam"
CONFIG = {"views": [{
    "title": "Таверна",
    "path": "taverna",
    "icon": "mdi:cctv",
    "cards": [
        {"type": "glance", "title": "Камера подвала — нажми на картинку, откроется живая",
         "entities": [ENT]},
        {"type": "entities", "title": "Свет и движение",
         "entities": [
             {"entity": LAM, "name": "Свет таверны"},
             {"entity": "binary_sensor.taverna_motion",
              "name": "Движение (свет гаснет через 3 мин тишины)"},
             {"entity": "binary_sensor.taverna_motion_quiet",
              "name": "Тишина (музыка гаснет через 2 мин)"},
             {"entity": "input_boolean.taverna_camera_boost", "name": "Камера 5 к/с на 10 минут"},
             {"entity": "input_boolean.tavern_light_manual", "name": "Ручной режим света"}]},
        {"type": "markdown",
         "content": "Картинка с камеры подвала через Home Assistant, 2 кадра в секунду. Кнопка "
                    "«Камера 5 к/с» поднимает частоту на 10 минут и сама возвращает 2. Свет, "
                    "включившийся без движения, гаснет через минуту и молчит."},
    ]}]}


async def main():
    async with websockets.connect("ws://127.0.0.1:8123/api/websocket", max_size=2 ** 24) as ws:
        assert json.loads(await ws.recv()).get("type") == "auth_required"
        await ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
        print("auth:", json.loads(await ws.recv()).get("type"))

        seq = [0]

        async def cmd(payload):
            seq[0] += 1
            payload["id"] = seq[0]
            await ws.send(json.dumps(payload))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == payload["id"]:
                    return msg

        r = await cmd({"type": "config/entity_registry/update", "entity_id": ENT, "name": NAME})
        print("name camera:", r.get("success"), json.dumps(r.get("error"))[:160] if r.get("error") else "")

        lst = await cmd({"type": "lovelace/dashboards/list"})
        items = lst.get("result") or []
        found = next((d for d in items if d.get("url_path") == URL), None)
        print("dashboards:", [d.get("url_path") for d in items])
        if not found:
            r = await cmd({"type": "lovelace/dashboards/create", "title": "Таверна",
                           "icon": "mdi:cctv", "show_in_sidebar": True, "url_path": URL})
            print("create:", r.get("success"), json.dumps(r.get("error"))[:200] if r.get("error") else "",
                  json.dumps(r.get("result"))[:120])
        r = await cmd({"type": "lovelace/config/save", "url_path": URL, "config": CONFIG})
        print("save config:", r.get("success"), json.dumps(r.get("error"))[:200] if r.get("error") else "")

        chk = await cmd({"type": "lovelace/config", "url_path": URL})
        got = chk.get("result") or {}
        print("stored cards:", [c.get("type") for c in (got.get("views") or [{}])[0].get("cards", [])])


asyncio.run(main())
