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

# camera present? (motion reopens it itself, but a missing device means the light is blind)
if [ ! -e /dev/video0 ]; then
    echo "CAMERA MISSING: /dev/video0 is gone from claryel01 - motion has no input"
fi
exit 0
