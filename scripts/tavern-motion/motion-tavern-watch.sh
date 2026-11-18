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

# [EN] Latch guard. Motion closes an event with the 'end' hook; if that call is lost (daemon
#      restarted mid-event, HA unreachable at that moment) input_boolean.tavern_motion_now stays
#      on and the light would never turn off. The hook touches HB_FILE on every accepted event, so
#      "latch on + no heartbeat for STALE_S" means the camera stopped reporting while the latch
#      stayed up: clear it and let HA's 5-minute delay switch the light off.
# [RU] Защита от залипания. Motion закрывает событие хуком 'end'; если этот вызов потерялся
#      (демон перезапустился посреди события, HA был недоступен в этот момент), флажок
#      tavern_motion_now остаётся включённым и свет никогда не погаснет. Хук трогает HB_FILE на
#      каждом принятом событии, поэтому «флажок включён + нет пульса STALE_S» означает, что камера
#      перестала сообщать о движении, а флажок остался: снимаем его, и пауза HA в 5 минут гасит свет.
HB_FILE=${HB_FILE:-/home/viktor/.local/state/tavern-motion/heartbeat}
HA_URL=${HA_URL:-http://127.0.0.1:8123}
TOKEN_FILE=${TOKEN_FILE:-/home/viktor/.config/motion/hass-token}
BOOLEAN=input_boolean.tavern_motion_now
STALE_S=900
if [ "$state" = "active" ] && [ -r "$TOKEN_FILE" ]; then
    token=$(cat "$TOKEN_FILE")
    latch=$(curl -s -m 5 -H "Authorization: Bearer ***" \
            "$HA_URL/api/states/$BOOLEAN" | sed -n 's/.*"state":"\([^"]*\)".*/\1/p' | head -1)
    hb_mtime=$(stat -c %Y "$HB_FILE" 2>/dev/null || echo 0)
    hb_age=$(( $(date +%s) - hb_mtime ))
    if [ "$latch" = "on" ] && [ "$hb_age" -gt "$STALE_S" ]; then
        curl -s -m 5 -X POST -H "Authorization: Bearer ***" -H 'Content-Type: application/json' \
             -d "{\"entity_id\":\"$BOOLEAN\"}" \
             "$HA_URL/api/services/input_boolean/turn_off" -o /dev/null
        echo "MOTION LATCH CLEARED: $BOOLEAN was on for ${hb_age}s with no camera heartbeat (hook 'end' lost) - HA delay will switch the light off"
    fi
fi

# camera present? (motion reopens it itself, but a missing device means the light is blind)
if [ ! -e /dev/video0 ]; then
    echo "CAMERA MISSING: /dev/video0 is gone from claryel01 - motion has no input"
fi
exit 0
