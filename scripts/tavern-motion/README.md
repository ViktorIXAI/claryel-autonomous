# Tavern motion light (claryel01)

Motion-based detection-only motion detector that drives the SONOFF tavern light through
Home Assistant. Design, measurements and known limits:
`docs/tavern-motion-camera-2026-11-18.md`.

Install order on the host:

1. Put `motion-tavern.conf` into `~/.config/motion/motion-tavern.conf`.
2. Put `tavern-motion-hook.sh` into `~/.local/libexec/` and `chmod 755` both.
3. Create `~/.config/motion/hass-token` (mode `0600`) with a Home Assistant long-lived token.
4. `sudo bash install-motion-tavern-root.sh` (installs motion, masks the distro unit,
   installs and enables `motion-tavern.service`; prints `INSTALL DONE.`).
5. Register `motion-tavern-watch.sh` as a 15-minute no-agent cron job.

The token is never stored in these files - the hook reads it from the `0600` file at runtime.
