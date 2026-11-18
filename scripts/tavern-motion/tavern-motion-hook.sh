#!/bin/sh
# [EN] Motion -> Home Assistant bridge for the tavern light. Motion calls this with one
#      argument: start | frame | end | failure. It only talks to the local HA REST API.
# [RU] Мост Motion -> Home Assistant для света в таверне. Motion вызывается одним аргументом:
#      start | frame | end | failure. Обращение только к локальному REST API Home Assistant.
#
# Guards:
#   * boot guard: events in the first BOOT_GUARD_S after the service starts are dropped
#     (auto-exposure settling on the first frames looks like motion);
#   * throttle: 'frame' calls are forwarded at most once per THROTTLE_S (motion at 2 fps
#     would otherwise fire ~2 HTTP calls per second);
#   * no recordings, no pictures: this script only sets helpers in Home Assistant.
set -eu

HA_URL="${HA_URL:-http://127.0.0.1:8123}"
TOKEN_FILE="${TOKEN_FILE:-/home/viktor/.config/motion/hass-token}"
# [EN] /tmp works for both the sandboxed service (PrivateTmp gives it a private /tmp) and
#      manual test runs; it resets on boot, which the unit's ExecStartPre recreates.
# [RU] /tmp подходит и изолированному сервису (PrivateTmp даёт ему свой /tmp), и ручным
#      проверкам; при загрузке очищается, ExecStartPre в юните это пересоздаёт.
STATE_DIR="${STATE_DIR:-/tmp/motion-tavern}"
BOOT_GUARD_S=30
THROTTLE_S=20

BOOLEAN="input_boolean.tavern_motion_now"

mkdir -p "$STATE_DIR"

call_ha() { # call_ha <service/path> <json body>
    [ -r "$TOKEN_FILE" ] || { echo "hook: token file unreadable" >&2; return 0; }
    token=$(cat "$TOKEN_FILE")
    curl -s -m 3 -o /dev/null -X POST \
        -H "Authorization: Bearer $token" \
        -H 'Content-Type: application/json' \
        -d "$2" "$HA_URL/api/services/$1" || true
}

now=$(date +%s)
start_ts=$(cat "$STATE_DIR/start-ts" 2>/dev/null || echo 0)

case "${1:-}" in
    start | frame)
        if [ $((now - start_ts)) -lt "$BOOT_GUARD_S" ]; then
            exit 0
        fi
        if [ "${1:-}" = "frame" ]; then
            last=$(cat "$STATE_DIR/last-post" 2>/dev/null || echo 0)
            if [ $((now - last)) -lt "$THROTTLE_S" ]; then
                exit 0
            fi
        fi
        echo "$now" > "$STATE_DIR/last-post"
        call_ha "input_boolean/turn_on" "{\"entity_id\":\"$BOOLEAN\"}"
        ;;
    end)
        call_ha "input_boolean/turn_off" "{\"entity_id\":\"$BOOLEAN\"}"
        ;;
    failure)
        # [EN] camera lost: motion restarts by itself (Restart=always); clear the helper so the
        #      light cannot stay on forever because of a stuck "motion" state.
        # [RU] камера потеряна: motion перезапустится сам (Restart=always); снимаем хелпер,
        #      чтобы свет не остался включённым из-за застрявшего состояния «движение».
        echo "motion-tavern: camera failure event" >&2
        call_ha "input_boolean/turn_off" "{\"entity_id\":\"$BOOLEAN\"}"
        ;;
    *)
        echo "usage: tavern-motion-hook.sh start|frame|end|failure" >&2
        exit 1
        ;;
esac
