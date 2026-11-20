"""Add one automation to the inline automation block: shout when the tavern relay is lost.

The BASICR4 relay is Wi-Fi + eWeLink cloud only (RSSI about -72 dBm, no local protocol on this LAN),
so while its entity is `unavailable` every lamp guard in the house is blind and a person walking
downstairs gets a dark room. The watchdog writes a chat line; this automation makes the same fact
loud on the phone (critical sound, verified shape from references/home-assistant.md).

Text insertion at the end of the `automation:` block - the file is hand-maintained inline YAML, so
re-dumping it with a parser would reformat unrelated blocks.
"""
import re
import shutil

PATH = "/config/configuration.yaml"
BACKUP = "/config/configuration.yaml.bak-relay-alert-20261120"
NEW_ID = "tavern_relay_unreachable_alert"

BLOCK = """  - id: tavern_relay_unreachable_alert
    alias: "Таверна: реле недоступно - не молчать"
    description: >-
      BASICR4 lives on Wi-Fi + eWeLink cloud only (rssi about -72 dBm, no local protocol on this
      LAN). While the entity is unavailable no lamp guard can act and motion cannot turn the light
      on, so report it loudly instead of failing silently.
    trigger:
      - platform: state
        entity_id: switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1
        to: "unavailable"
        for: "00:01:00"
    action:
      - service: notify.mobile_app_iphone_viktor
        data:
          title: "Таверна: свет не управляется"
          message: >-
            Реле BASICR4 потеряно (eWeLink cloud). Свет в таверне не включается и не выключается,
            сторожи света слепы.
          data:
            push:
              sound:
                critical: 1
                name: default
                volume: 1.0
            interruption_level: timeSensitive
            tag: tavern-relay
    mode: single
"""

txt = open(PATH, encoding="utf-8").read()
if NEW_ID in txt:
    print("already present, nothing to do")
    raise SystemExit(0)

shutil.copy2(PATH, BACKUP)
lines = txt.splitlines(keepends=True)
start = None
for i, ln in enumerate(lines):
    if re.match(r"^automation:\s*$", ln):
        start = i
        break
if start is None:
    print("no inline automation: block found - aborting")
    raise SystemExit(1)

end = len(lines)
for j in range(start + 1, len(lines)):
    if re.match(r"^[^\s#]", lines[j]) and not lines[j].startswith("\n"):
        end = j
        break

insert_at = end
while insert_at - 1 > start and not lines[insert_at - 1].strip():
    insert_at -= 1
lines.insert(insert_at, BLOCK)
open(PATH, "w", encoding="utf-8").write("".join(lines))
print("inserted after line", start + 1, "block end", end, "| backup:", BACKUP)
