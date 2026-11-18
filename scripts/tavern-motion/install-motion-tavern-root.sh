#!/usr/bin/env bash
# [EN] One-time root installer for the tavern motion detector on this host (claryel01,
#      Ubuntu 24.04). Installs Motion as its own systemd service, independent of Docker and
#      Home Assistant. Idempotent: safe to re-run. Writes no secrets; the camera config and
#      the Home Assistant token stay in viktor's home (mode 600) and are never committed.
# [RU] Одноразовый root-установщик датчика движения в таверне (claryel01, Ubuntu 24.04).
#      Ставит Motion отдельным systemd-сервисом, независимо от Docker и Home Assistant.
#      Идемпотентен. Секретов не пишет: конфиг камеры и токен Home Assistant лежат в домашней
#      папке viktor (права 600) и в репозиторий не попадают.
#
# Run once:  sudo bash ~/.hermes/setup/install-motion-tavern-root.sh
set -euo pipefail

USER_NAME=viktor
CFG=/home/viktor/.config/motion/motion-tavern.conf
STATE_DIR=/tmp/motion-tavern
UNIT=/etc/systemd/system/motion-tavern.service
LOG=/home/viktor/.hermes/logs/motion-install.log

if [ "$(id -u)" != "0" ]; then echo "run with sudo" >&2; exit 1; fi
[ -f "$CFG" ] || { echo "missing config: $CFG" >&2; exit 1; }

# [EN] keep a readable transcript of the whole run for the agent (mode 600 -> viktor)
mkdir -p "$(dirname "$LOG")"
exec > >(tee -a "$LOG") 2>&1
trap 'chown viktor:viktor "$LOG" 2>/dev/null || true' EXIT
echo "##### run started $(date -u +%FT%TZ) #####"

export DEBIAN_FRONTEND=noninteractive
echo "=== 1. install motion package ==="
apt-get update -y -qq
apt-get install -y motion
dpkg -s motion | grep -m1 -E "^(Version|Status)"

echo "=== 2. disable and mask the stock 'motion' service (it would grab /dev/video0 too) ==="
systemctl disable --now motion.service 2>/dev/null || true
systemctl mask motion.service

echo "=== 3. give $USER_NAME access to the camera (video group) ==="
getent group video >/dev/null
if id -nG "$USER_NAME" | tr ' ' '\n' | grep -qx video; then
    echo "already in group video"
else
    # [EN] usermod (not vgs - that is the LVM tool); systemd resolves groups at exec time,
    #      so no re-login is needed for the service itself.
    # [RU] именно usermod (vgs - это утилита LVM); systemd читает группы при старте процесса,
    #      поэтому сервису перезаход в сессию не нужен.
    usermod -aG video "$USER_NAME"
    getent group video
fi

echo "=== 4. state directory ==="
install -d -o "$USER_NAME" -g "$USER_NAME" -m 755 "$STATE_DIR"

echo "=== 5. systemd unit: $UNIT ==="
cat > "$UNIT" <<'UNIT_EOF'
[Unit]
Description=Motion detection daemon for the tavern light (USB camera)
Documentation=https://motion-project.github.io/motion_config.html
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=viktor
Group=viktor
# [EN] start-ts is read by the hook: events in the first 30 s after (re)start are dropped,
#      because the camera's auto-exposure settling on the first frames looks like motion.
# [RU] start-ts читается хуком: события в первые 30 с после (пере)запуска отбрасываются,
#      потому что настройка автоэкспозиции на первых кадрах выглядит как движение.
ExecStartPre=/bin/sh -c 'mkdir -p /tmp/motion-tavern && date +%%s > /tmp/motion-tavern/start-ts'
ExecStart=/usr/bin/motion -n -c /home/viktor/.config/motion/motion-tavern.conf
Restart=always
RestartSec=5
# [EN] keep detection cheap and subordinate to the workloads on this machine
Nice=10
CPUWeight=20
MemoryHigh=300M
MemoryMax=400M
TasksMax=64
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ProtectKernelTunables=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true

[Install]
WantedBy=multi-user.target
UNIT_EOF

systemctl daemon-reload
systemctl enable motion-tavern.service
systemctl restart motion-tavern.service

echo "=== 6. status ==="
sleep 8
systemctl --no-pager status motion-tavern.service 2>&1 | sed -n '1,12p' || true
echo "=== recent log ==="
journalctl -u motion-tavern --since "-1 min" --no-pager 2>&1 | tail -25 || true
echo "=== listening sockets owned by motion (must be none: no stream, no webcontrol) ==="
ss -ltnp 2>/dev/null | grep -iE "motion|:8080|:8081" || echo "none"
echo "=== group check ==="
id -nG "$USER_NAME" | tr ' ' '\n' | grep -qx video && echo "$USER_NAME is in group video" || echo "WARNING: $USER_NAME still not in video group"
echo "=== resource usage right now ==="
systemctl show motion-tavern -p MemoryCurrent -p CPUUsageNSec -p NRestarts -p ExecMainPID -p ActiveState -p SubState || true
echo "INSTALL DONE."
