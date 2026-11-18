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

if [ -n "$restarts" ] && [ -n "$prev" ] && [ "$restarts" -gt "$prev" ]; then
    echo "MOTION RESTARTED: $UNIT restarted $((restarts - prev)) time(s) since last check (total $restarts) - check the camera / journalctl -u $UNIT"
fi

echo "$restarts" > "$STATE"

# [EN] Latch report (no writes). Home Assistant owns the latch: the hook toggles
#      input_boolean.tavern_motion_now on every accepted frame, and automation
#      tavern_motion_latch_guard clears it after 15 minutes without a refresh. This watchdog only
#      shouts when that failed: latch still on 25+ minutes after its last change.
# [RU] Сообщение о залипании (ничего не пишет). Флажком заведует Home Assistant: хук
#      переключает input_boolean.tavern_motion_now на каждом принятом кадре движения, а автомат
#      tavern_motion_latch_guard снимает его, если 15 минут не было обновления. Сторож только
#      кричит, если это не сработало: флажок всё ещё включён через 25+ минут после изменения.
HA_URL=${HA_URL:-http://127.0.0.1:8123}
TOKEN_FILE=${TOKEN_FILE:-/home/viktor/.config/motion/hass-token}
BOOLEAN=input_boolean.tavern_motion_now
if [ "$state" = "active" ] && [ -r "$TOKEN_FILE" ]; then
    token=$(cat "$TOKEN_FILE")
    body=$(curl -s -m 5 -H "Authorization: Bearer ***" "$HA_URL/api/states/$BOOLEAN")
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
    token=$(cat "$TOKEN_FILE")
    lamp=$(curl -s -m 5 -H "Authorization: Bearer ***" "$HA_URL/api/states/$SWITCH" \
        | sed -n 's/.*"state":"\([^"]*\)".*/\1/p' | head -1)
    if [ "$lamp" = "on" ]; then
        sensor=$(curl -s -m 5 -H "Authorization: Bearer ***" "$HA_URL/api/states/binary_sensor.taverna_motion" \
            | sed -n 's/.*"state":"\([^"]*\)".*/\1/p' | head -1)
        manual=$(curl -s -m 5 -H "Authorization: Bearer ***" "$HA_URL/api/states/input_boolean.tavern_light_manual" \
            | sed -n 's/.*"state":"\([^"]*\)".*/\1/p' | head -1)
        onsince=$(curl -s -m 5 -H "Authorization: Bearer ***" "$HA_URL/api/states/$SWITCH" \
            | sed -n 's/.*"last_changed":"\([^"]*\)".*/\1/p' | head -1)
        age=$(( $(date +%s) - $(date -d "$onsince" +%s 2>/dev/null || echo $(date +%s)) ))
        if [ "$sensor" != "on" ] && [ "$manual" != "on" ] && [ "$age" -gt 900 ]; then
            echo "LAMP ON WITHOUT MOTION: $SWITCH has been on for ${age}s with motion sensor '$sensor' - automation taverna_svet_gorit_bez_dvizheniia_vykliuchit did not switch it off"
        fi
    fi
fi

# Zigbee reachability of the relay: it dropped out of the mesh 4 times on 2026-11-18
# (11:35, 11:36, 13:01, 13:11 local). HA reports 'unavailable'; a relay that is not answering
# cannot be switched off by the motion chain either.
if [ "$state" = "active" ] && [ -r "$TOKEN_FILE" ]; then
    lampstate=$(curl -s -m 5 -H "Authorization: Bearer ***" "$HA_URL/api/states/$SWITCH" \
        | sed -n 's/.*"state":"\([^"]*\)".*/\1/p' | head -1)
    [ "$lampstate" = "unavailable" ] && \
        echo "RELAY UNREACHABLE: $SWITCH is 'unavailable' in Home Assistant - Zigbee link to the tavern relay is down"
fi

# camera present? (motion reopens it itself, but a missing device means the light is blind)
if [ ! -e /dev/video0 ]; then
    echo "CAMERA MISSING: /dev/video0 is gone from claryel01 - motion has no input"
fi
exit 0
