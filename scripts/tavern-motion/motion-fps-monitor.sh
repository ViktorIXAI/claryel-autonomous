#!/bin/sh
# Five-minute report on the tavern motion detector: how many camera events fired in the last
# five minutes (the room is empty at night, so a camera event = a false trigger), what detection
# settings are live, what the light is doing and what Motion costs. Stops itself after 12 samples.
set -u
CFG=/home/viktor/.config/motion/motion-tavern.conf
UNIT=motion-tavern.service
STATE=/home/viktor/.local/state/tavern-motion/monitor.state
TOKEN_FILE=/home/viktor/.config/motion/hass-token
HA=http://127.0.0.1:8123
SW=switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1

fps=$(awk '/^framerate /{print $2}' "$CFG")
mmf=$(awk '/^minimum_motion_frames /{print $2}' "$CFG")
mft=$(awk '/^minimum_frame_time /{print $2}' "$CFG")

events=$(journalctl -u "$UNIT" --since "-5 min" --no-pager -o short-iso 2>/dev/null |
         grep -ciE "motion detected - starting event")
events24=$(journalctl -u "$UNIT" --since "-24 h" --no-pager -o short-iso 2>/dev/null |
         grep -ciE "motion detected - starting event")

pid=$(systemctl show "$UNIT" -p ExecMainPID --value 2>/dev/null)
cpu="?"; rss="?"
if [ -n "${pid:-}" ] && [ -r "/proc/$pid/stat" ]; then
    hz=$(getconf CLK_TCK)
    c1=$(awk '{print $14+$15}' "/proc/$pid/stat"); sleep 3
    c2=$(awk '{print $14+$15}' "/proc/$pid/stat")
    cpu=$(awk -v a="$c1" -v b="$c2" -v h="$hz" 'BEGIN{printf "%.2f", (b-a)/h/3*100}')
    rss=$(awk '/VmRSS/{printf "%.0f MB", $2/1024}' "/proc/$pid/status")
fi

light="?"
if [ -r "$TOKEN_FILE" ]; then
    light=$(curl -s -m 5 -H "Authorization: Bearer $(cat "$TOKEN_FILE")" \
            "$HA/api/states/$SW" | sed -n 's/.*"state":"\([^"]*\)".*/\1/p' | head -1)
fi

mkdir -p "$(dirname "$STATE")"
n=$(cat "$STATE" 2>/dev/null || echo 0); n=$((n + 1)); echo "$n" > "$STATE"

echo "MOTION REPORT ${n}/12 $(date '+%H:%M'): событий за 5 мин = $events (за 24 ч = $events24); режим ${fps} к/с, minimum_motion_frames $mmf, minimum_frame_time $mft; свет=$light; motion CPU=${cpu}% ядра, RAM=$rss"
[ "$n" -ge 12 ] && echo "MONITOR_DONE: 12 снятых проб, задачу cron нужно поставить на паузу"
exit 0
