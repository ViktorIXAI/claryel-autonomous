#!/bin/bash
# Targeted stop of only the selected series: the criterion is the process's PARB_STATE variable.
# Linux: read /proc/PID/environ. macOS: take the environment via `ps -E -o pid,args`.
# First argument: a substring, e.g. "state-v12.json".
cd ~/parb || exit 1
NEED="$1"
[ -z "$NEED" ] && { echo "an argument is required: a PARB_STATE substring"; exit 1; }

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
# nohup bash -c wrappers: only those whose command line contains both gate_run.py and the needed state.
# We do not touch our own process or the ancestors (otherwise pgrep matches the stop command itself).
for pid in $(pgrep -f 'bash -c.*gate_run'); do
  [ "$pid" = "$$" ] && continue
  case "$(ps -o args= -p $pid 2>/dev/null)" in
    *"bash -c"*gate_run*"$NEED"*) kill -TERM "$pid" 2>/dev/null; KILLED="$KILLED $pid(wrapper)";;
  esac
done
p=$PPID
for i in 1 2 3 4; do [ -n "$p" ] && [ "$p" != "1" ] && kill -0 "$p" 2>/dev/null || break
  for pid in $(pgrep -f 'bash -c.*gate_run'); do [ "$pid" = "$p" ] && KILLED="$KILLED $pid(ancestor,skipped)"; done
  p=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' '); done
[ -z "$KILLED" ] && echo "NOTHING with PARB_STATE~$NEED is running" || echo "stopped:$KILLED"
sleep 3
echo "live gate_run:"
for pid in $(pgrep -f 'gate_run\.py'); do
  echo "  $pid state=$(state_of "$pid") version=$(ver_of "$pid")"
done
