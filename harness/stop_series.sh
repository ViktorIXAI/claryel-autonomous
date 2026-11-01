#!/bin/bash
# Точечная остановка только нужной серии: критерий — переменная PARB_STATE у процесса.
# Linux: читаем /proc/PID/environ. macOS: берём окружение через `ps -E -o pid,args`.
# Первый аргумент: подстрока, например "state-v12.json".
cd ~/parb || exit 1
NEED="$1"
[ -z "$NEED" ] && { echo "нужен аргумент: подстрока PARB_STATE"; exit 1; }

state_of() {
  local pid="$1"
  if [ -r "/proc/$pid/environ" ]; then
    tr '\0' '\n' < "/proc/$pid/environ" 2>/dev/null | grep '^PARB_STATE=' | cut -d= -f2
  else
    ps -E -o pid,args -p "$pid" 2>/dev/null | tr ' ' '\n' | grep '^PARB_STATE=' | cut -d= -f2
  fi
}
ver_of() {
  local pid="$1"
  if [ -r "/proc/$pid/environ" ]; then
    tr '\0' '\n' < "/proc/$pid/environ" 2>/dev/null | grep '^PARB_GATE_VERSION=' | cut -d= -f2
  else
    ps -E -o pid,args -p "$pid" 2>/dev/null | tr ' ' '\n' | grep '^PARB_GATE_VERSION=' | cut -d= -f2
  fi
}

KILLED=""
for pid in $(pgrep -f 'gate_run\.py'); do
  st=$(state_of "$pid")
  case "$st" in
    *"$NEED"*) kill -TERM "$pid" 2>/dev/null; KILLED="$KILLED $pid($st)";;
  esac
done
# обёртки nohup bash -c: только те, в командной строке которых есть и gate_run.py, и нужный state.
# Свой собственный процесс и предков не трогаем (иначе pgrep матчит саму команду остановки).
for pid in $(pgrep -f 'bash -c.*gate_run'); do
  [ "$pid" = "$$" ] && continue
  case "$(ps -o args= -p $pid 2>/dev/null)" in
    *"bash -c"*gate_run*"$NEED"*) kill -TERM "$pid" 2>/dev/null; KILLED="$KILLED $pid(обёртка)";;
  esac
done
p=$PPID
for i in 1 2 3 4; do [ -n "$p" ] && [ "$p" != "1" ] && kill -0 "$p" 2>/dev/null || break
  for pid in $(pgrep -f 'bash -c.*gate_run'); do [ "$pid" = "$p" ] && KILLED="$KILLED $pid(предок,пропущен)"; done
  p=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' '); done
[ -z "$KILLED" ] && echo "НИЧЕГО с PARB_STATE~$NEED не запущено" || echo "остановлено:$KILLED"
sleep 3
echo "живые gate_run:"
for pid in $(pgrep -f 'gate_run\.py'); do
  echo "  $pid state=$(state_of "$pid") version=$(ver_of "$pid")"
done
