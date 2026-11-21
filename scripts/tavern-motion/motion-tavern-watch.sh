#!/bin/sh
# [EN] Watchdog for the tavern motion service. Silent when healthy (cron then sends nothing);
#      prints exactly one alert line when Motion is down or is restart-looping.
# [RU] Сторож сервиса движения для таверны. Когда всё хорошо — молчит (cron ничего не шлёт);
#      печатает ровно одну строку предупреждения, если Motion упал или перезапускается по кругу.
set -u

UNIT=motion-tavern.service
STATE=/tmp/motion-tavern/watchdog.state

if ! command -v systemctl >/dev/null 2>&1; then
    echo "MOTION CHECK: systemctl unavailable on this host"
    exit 0
fi

state=$(systemctl is-active "$UNIT" 2>/dev/null); state=${state:-unknown}
restarts=$(systemctl show "$UNIT" -p NRestarts --value 2>/dev/null || echo "")
mainpid=$(systemctl show "$UNIT" -p ExecMainPID --value 2>/dev/null || echo "")

mkdir -p "$(dirname "$STATE")"
prev=$(cat "$STATE" 2>/dev/null || echo "")

if [ "$state" != "active" ]; then
    echo "MOTION DOWN: $UNIT is '$state' on claryel01 - tavern light will not follow motion"
    exit 0
fi

# [EN] Raising/lowering the frame rate (dashboard button, taverna-camera-ctl.py) restarts Motion on
#      purpose - camera-ctl appends one line per requested restart to motion-restarts.log. The state
#      file stores "restarts markers", so only restarts beyond the markers recorded since the last
#      check reach the chat.
# [RU] Поднятие/спускание частоты кадров (кнопка в дашборде, taverna-camera-ctl.py) перезапускает
#      Motion намеренно — camera-ctl дописывает строку на каждый такой запрос в motion-restarts.log.
#      В state-файле пишутся "перезапуски метки", поэтому в чат проходит только то, что сверх меток.
FPS_LOG=/home/viktor/.local/state/taverna-greeting/motion-restarts.log
markers=0
[ -r "$FPS_LOG" ] && markers=$(wc -l < "$FPS_LOG")

if [ -n "$restarts" ] && [ -n "$prev" ]; then
    prev_restart=$(printf '%s' "$prev" | awk '{print $1}')
    prev_markers=$(printf '%s' "$prev" | awk '{print $2}'); prev_markers=${prev_markers:-$markers}
    delta=$((restarts - prev_restart))
    explained=$((markers - prev_markers)); [ "$explained" -lt 0 ] && explained=0
    if [ "$delta" -gt "$explained" ]; then
        echo "MOTION RESTARTED: $UNIT restarted $((delta - explained)) time(s) since last check (total $restarts, $explained were fps switches) - check the camera / journalctl -u $UNIT"
    fi
fi

echo "$restarts $markers" > "$STATE"

# [EN] Latch report (no writes). Home Assistant owns the latch: the hook toggles
#      input_boolean.tavern_motion_now on every accepted frame, and automation
#      tavern_motion_latch_guard clears it after 15 minutes without a refresh. This watchdog only
#      shouts when that failed: latch still on 25+ minutes after its last change.
# [RU] Сообщение о залипании (ничего не пишет). Флажком заведует Home Assistant: хук
#      переключает input_boolean.tavern_motion_now на каждом принятом кадре движения, а автомат
#      tavern_motion_latch_guard снимает его, если 15 минут не было обновления. Сторож только
#      кричит, если это не сработало: флажок всё ещё включён через 25+ минут после изменения.
# [EN] Pinned on purpose (no ${VAR:-} override): during the 2026-11-18 cron runs this script
#      reached Home Assistant with a substituted credential and got 401 on 68 requests while
#      printing nothing - a report-only watchdog that cannot read HA is worse than no watchdog.
#      The HTTP code is now checked and a failure is shouted instead of swallowed.
# [RU] Заданы жёстко (без ${VAR:-}): в кронах 2026-11-18 запросы в Home Assistant уходили с
#      подменённым токеном и давали 401 (68 запросов), а сторож молчал. Сторож, который не видит
#      HA, хуже отсутствующего - теперь код ответа проверяется и ошибка видна.
HA_URL="http://127.0.0.1:8123"
TOKEN_FILE="/home/viktor/.config/motion/hass-token"
BOOLEAN=input_boolean.tavern_motion_now
ha_get() { # ha_get <url> -> тело ответа, последней строкой HTTP-код
    curl -s -m 5 -w '\n%{http_code}' -H "Authorization: Bearer $(cat "$TOKEN_FILE")" "$1" || printf '000'
}
ha_code() { printf '%s' "$1" | tail -n 1; }
ha_body() { printf '%s' "$1" | sed '$d'; }
if [ "$state" = "active" ] && [ -r "$TOKEN_FILE" ]; then
    resp=$(ha_get "$HA_URL/api/states/$BOOLEAN")
    code=$(ha_code "$resp"); body=$(ha_body "$resp")
    [ "$code" != "200" ] && echo "HA UNREADABLE: http=$code for $BOOLEAN - the tavern watchdog is blind (check token and HA_URL)"
    latch=$(printf '%s' "$body" | sed -n 's/.*"state":"\([^"]*\)".*/\1/p' | head -1)
    changed=$(printf '%s' "$body" | sed -n 's/.*"last_changed":"\([^"]*\)".*/\1/p' | head -1)
    if [ "$latch" = "on" ] && [ -n "$changed" ]; then
        age=$(( $(date +%s) - $(date -d "$changed" +%s 2>/dev/null || echo $(date +%s)) ))
        [ -n "$age" ] && [ "$age" -gt 1500 ] && \
            echo "MOTION LATCH STUCK: $BOOLEAN has been on for ${age}s - HA latch guard did not clear it, check automation.taverna_flazhok_dvizheniia_gorit_slishkom_dolgo_sniat"
    fi
fi

# [EN] Lamp burning with nobody in the room (the 2026-11-18 incident). The SONOFF relay took the
#      ON state by itself at 06:01 - no Motion event, no HA service call, no user - and burned for
#      7 h 18 min, because the motion chain only switches off states it created itself. Home
#      Assistant now has automation tavern_lamp_on_without_motion for that (light on + motion
#      sensor off for 10 minutes -> off). This watchdog shouts only when even that failed, i.e.
#      the lamp is still on 15+ minutes after it entered that state. Manual mode
#      (input_boolean.tavern_light_manual = on) is expected behaviour and stays quiet.
# [RU] Свет горит, а людей нет (инцидент 2026-11-18). Реле SONOFF само перешло в on в 06:01 — без
#      события Motion, без сервиса HA и без пользователя — и горело 7 ч 18 мин, потому что
#      цепочка движения выключает только то, что включила сама. Теперь в Home Assistant есть
#      автомат tavern_lamp_on_without_motion (свет горит 10 минут при выключенном сенсоре -> выкл).
#      Сторож кричит, только если не сработал даже он: свет включён 15+ минут после перехода в
#      это состояние. Ручной режим (input_boolean.tavern_light_manual = on) — норма, тихо.
SWITCH=switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1
if [ "$state" = "active" ] && [ -r "$TOKEN_FILE" ]; then
    resp=$(ha_get "$HA_URL/api/states/$SWITCH")
    code=$(ha_code "$resp"); sbody=$(ha_body "$resp")
    [ "$code" != "200" ] && echo "HA UNREADABLE: http=$code for $SWITCH - the lamp check is blind"
    lamp=$(printf '%s' "$sbody" | sed -n 's/.*"state":"\([^"]*\)".*/\1/p' | head -1)
    onsince=$(printf '%s' "$sbody" | sed -n 's/.*"last_changed":"\([^"]*\)".*/\1/p' | head -1)
    if [ "$lamp" = "on" ]; then
        sensor=$(printf '%s' "$(ha_body "$(ha_get "$HA_URL/api/states/binary_sensor.taverna_motion")")" \
            | sed -n 's/.*"state":"\([^"]*\)".*/\1/p' | head -1)
        manual=$(printf '%s' "$(ha_body "$(ha_get "$HA_URL/api/states/input_boolean.tavern_light_manual")")" \
            | sed -n 's/.*"state":"\([^"]*\)".*/\1/p' | head -1)
        age=$(( $(date +%s) - $(date -d "$onsince" +%s 2>/dev/null || echo $(date +%s)) ))
        if [ "$sensor" != "on" ] && [ "$manual" != "on" ] && [ "$age" -gt 900 ]; then
            echo "LAMP ON WITHOUT MOTION: $SWITCH has been on for ${age}s with motion sensor '$sensor' - automation taverna_svet_gorit_bez_dvizheniia_vykliuchit did not switch it off"
        fi
    fi
fi

# Reachability of the relay: it went 'unavailable' 4 times on 2026-11-18 (11:35, 11:36, 13:01,
# 13:11 local). The BASICR4 is a Wi-Fi device on the eWeLink cloud integration - it is NOT part of
# the Zigbee mesh, so a drop here means the Wi-Fi/cloud path, not the Zigbee radio. A relay that is
# not answering cannot be switched off by the motion chain either.
# 2026-11-20: three drops in 25 minutes (11:07, 11:21, 11:30) with RSSI -72 dBm and connection=none.
# The integration stops refreshing the device until its config entry is reloaded, and a reload brings
# the relay back in ~45 s - so the watchdog now performs it itself, at most once per 10 minutes, and
# says so. The Zigbee devices live on a different config entry, so this reload cannot drop the mesh.
# 2026-11-21 04:31: measured FOUR drops in one hour (03:35:52, 03:53:03, 04:16:18, 04:30:25) while RSSI had
# improved from -70 to -55 dBm, three of them self-recovering in 1-30 s and one lasting 12 minutes. So the
# weak Wi-Fi signal is not the whole cause, and the number of drops is the number the owner actually needs:
# the per-drop alert alone hides whether things are getting better or worse. One extra summary line per
# increase in the drop count, plus the longest outage in the window, from the HA recorder history API.
SONOFF_ENTRY=01M7P351JEYY2KWTXH2A4EWNPA
RELOAD_MARK=/tmp/motion-tavern/relay-reload.state
FLAP_MARK=/tmp/motion-tavern/relay-flap.state
if [ "$state" = "active" ] && [ -r "$TOKEN_FILE" ]; then
    lampstate=$(printf '%s' "$(ha_body "$(ha_get "$HA_URL/api/states/$SWITCH")")" \
        | sed -n 's/.*"state":"\([^"]*\)".*/\1/p' | head -1)
    if [ "$lampstate" = "unavailable" ]; then
        rssi=$(printf '%s' "$(ha_body "$(ha_get "$HA_URL/api/states/sensor.taverna_basicr4_sonoff_1002bd4e01_rssi")")" \
            | sed -n 's/.*"state":"\([^"]*\)".*/\1/p' | head -1)
        conn=$(printf '%s' "$(ha_body "$(ha_get "$HA_URL/api/states/sensor.taverna_basicr4_sonoff_1002bd4e01_connection")")" \
            | sed -n 's/.*"state":"\([^"]*\)".*/\1/p' | head -1)
        echo "RELAY UNREACHABLE: $SWITCH is 'unavailable' in Home Assistant - the Wi-Fi/eWeLink path to the tavern relay is down (last rssi=$rssi connection=$conn)"
        now=$(date +%s); last=$(cat "$RELOAD_MARK" 2>/dev/null || echo 0)
        if [ $((now - last)) -ge 600 ]; then
            echo "$now" > "$RELOAD_MARK"
            code=$(curl -s -m 20 -o /dev/null -w '%{http_code}' -X POST \
                -H "Authorization: Bearer $(cat "$TOKEN_FILE")" \
                "$HA_URL/api/config/config_entries/entry/$SONOFF_ENTRY/reload")
            echo "RELAY RELOAD: forced eWeLink entry reload http=$code - the relay should answer within ~1 min; if this repeats all day the relay needs DIY Mode or a power cycle by hand"
        fi
    fi
fi

# Flap counter: the per-drop alert above only speaks while a drop is happening, so an hour of 1-30 s
# micro-outages reads as noise and hides the trend. Count the 'unavailable' transitions in the last 60
# minutes from the HA recorder, keep the longest one, and print one summary line only when the count grew.
if [ "$state" = "active" ] && [ -r "$TOKEN_FILE" ]; then
    hist=$(curl -s -m 20 -H "Authorization: Bearer $(cat "$TOKEN_FILE")" \
        "$HA_URL/api/history/period/$(date -u -d '-60 minutes' +%Y-%m-%dT%H:%M:%S)Z?filter_entity_id=$SWITCH")
    flap=$(printf '%s' "$hist" | python3 -c '
import json, sys, datetime
rows = []
try:
    chunks = json.load(sys.stdin)
except Exception:
    print("-1 0"); sys.exit(0)
for chunk in chunks:
    for s in chunk:
        try:
            rows.append((datetime.datetime.fromisoformat(s["last_changed"]), s["state"]))
        except Exception:
            continue
rows.sort()
drops = 0; longest = 0; start = None
for ts, st in rows:
    if st == "unavailable" and start is None:
        start = ts; drops += 1
    elif st != "unavailable" and start is not None:
        longest = max(longest, int((ts - start).total_seconds())); start = None
if start is not None:
    longest = max(longest, int((datetime.datetime.now(datetime.timezone.utc) - start).total_seconds()))
print(drops, longest)
' 2>/dev/null || echo "-1 0")
    drops=$(printf '%s' "$flap" | awk '{print $1}'); longest=$(printf '%s' "$flap" | awk '{print $2}')
    prev_drops=$(cat "$FLAP_MARK" 2>/dev/null | awk '{print $1}'); prev_drops=${prev_drops:--1}
    case "$drops" in ''|*[!0-9]*) drops=-1 ;; esac
    if [ "$drops" -gt 0 ] && [ "$drops" -gt "$prev_drops" ]; then
        echo "RELAY FLAPPY: $drops 'unavailable' transitions on $SWITCH in the last 60 min (longest ${longest}s) - the eWeLink/Wi-Fi path keeps blinking; signal alone does not explain it (RSSI was -55 dBm during the 4 drops on 2026-11-21)"
        echo "$drops $longest" > "$FLAP_MARK"
    fi
fi

# camera present? (motion reopens it itself, but a missing device means the light is blind)
if [ ! -e /dev/video0 ]; then
    echo "CAMERA MISSING: /dev/video0 is gone from claryel01 - motion has no input"
fi
exit 0
