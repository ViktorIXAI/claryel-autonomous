#!/bin/sh
# [EN] Motion -> Home Assistant bridge for the tavern light. Motion calls this with one
#      argument: start | frame | end | failure. It only talks to the local HA REST API.
# [RU] Мост Motion -> Home Assistant для света в таверне. Motion вызывается одним аргументом:
#      start | frame | end | failure. Обращение только к локальному REST API Home Assistant.
#
# Guards:
#   * boot guard: events in the first BOOT_GUARD_S after the service starts are dropped
#     (auto-exposure settling on the first frames looks like motion);
#   * throttle: 'frame' calls are forwarded at most once per THROTTLE_S (motion at 5 fps
#     would otherwise fire ~5 HTTP calls per second);
#   * no recordings, no pictures: this script only sets helpers in Home Assistant and
#     switches the tavern relay on at the start of an event;
#   * light dedupe: the relay is commanded at most once per LIGHT_DEDUPE_S.
set -eu

HA_URL="${HA_URL:-http://127.0.0.1:8123}"
TOKEN_FILE="${TOKEN_FILE:-/home/viktor/.config/motion/hass-token}"
# [EN] /tmp works for both the sandboxed service (PrivateTmp gives it a private /tmp) and
#      manual test runs; it resets on boot, which the unit's ExecStartPre recreates.
# [RU] /tmp подходит и изолированному сервису (PrivateTmp даёт ему свой /tmp), и ручным
#      проверкам; при загрузке очищается, ExecStartPre в юните это пересоздаёт.
STATE_DIR="${STATE_DIR:-/tmp/motion-tavern}"
# [EN] Heartbeat visible to every process: PrivateTmp gives the service its own /tmp, so the
#      watchdog cannot see STATE_DIR. This file is touched on every accepted event; the watchdog
#      uses it to clear a latch that Motion never closed (lost 'end', HA unreachable at that moment).
# [RU] Пульс, видимый всем процессам: PrivateTmp даёт сервису свой /tmp, поэтому сторож не видит
#      STATE_DIR. Файл обновляется на каждое принятое событие; сторож по нему снимает залипший
#      флажок, если Motion не передал 'end' (или HA был недоступен в этот момент).
HB_FILE="${HB_FILE:-/home/viktor/.local/state/tavern-motion/heartbeat}"
BOOT_GUARD_S=30
THROTTLE_S=20

BOOLEAN="input_boolean.tavern_motion_now"
LIGHT="switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1"
# [EN] dedupe: do not hammer the relay if Motion opens events back to back
LIGHT_DEDUPE_S=8
# [EN] Fast path. Home Assistant keeps the OFF authority (the template sensor holds for 5 min
#      after the last motion, then the automation switches off). The ON path used to run through
#      boolean -> template sensor delay_on -> automation, which added ~4-5 s. On an event start
#      the light is now switched on directly; the sensor path stays as a backup.
# [RU] Быстрый путь. Выключением по-прежнему заведует Home Assistant (шаблонный сенсор держится
#      5 минут после последнего движения, затем автомат гасит свет). Путь ВКЛЮЧЕНИЯ раньше шёл
#      через boolean -> delay_on шаблона -> автомат и добавлял ~4-5 с. Теперь при старте события
#      свет включается напрямую; цепочка через сенсор остаётся запасной.

mkdir -p "$STATE_DIR"
mkdir -p "$(dirname "$HB_FILE")" && touch "$HB_FILE"

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
    start)
        if [ $((now - start_ts)) -lt "$BOOT_GUARD_S" ]; then
            exit 0
        fi
        echo "$now" > "$STATE_DIR/last-post"
        # [EN] relay first: the light is the thing the user waits for, the latch only feeds the
        #      sensor and the OFF timer. Measured order saves ~150 ms.
        # [RU] сначала реле: свет — то, чего ждёт человек; флажок нужен только сенсору и таймеру
        #      выключения. Такой порядок даёт ~150 мс.
        last_on=$(cat "$STATE_DIR/last-light-on" 2>/dev/null || echo 0)
        if [ $((now - last_on)) -ge "$LIGHT_DEDUPE_S" ]; then
            echo "$now" > "$STATE_DIR/last-light-on"
            call_ha "switch/turn_on" "{\"entity_id\":\"$LIGHT\"}"
        fi
        call_ha "input_boolean/turn_on" "{\"entity_id\":\"$BOOLEAN\"}" 
        ;;
    frame)
        if [ $((now - start_ts)) -lt "$BOOT_GUARD_S" ]; then
            exit 0
        fi
        last=$(cat "$STATE_DIR/last-post" 2>/dev/null || echo 0)
        if [ $((now - last)) -lt "$THROTTLE_S" ]; then
            exit 0
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
