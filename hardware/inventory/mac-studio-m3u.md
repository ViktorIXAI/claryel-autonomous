# Passport MAC-STUDIO — high-memory comparison workstation
Live-collected 2026-11-01.

| field | value |
|---|---|
| role | mandatory paired duplicate for every adopted contour version (label `m`-suffixed files, `PARB_BOX=mac-studio`) |
| vendor/model | Apple Mac Studio, model id Mac15,14 |
| CPU | Apple M3 Ultra, 28 logical cores |
| memory | 274,877,906,944 B = 256 GiB unified |
| GPU | integrated (Metal); no discrete GPU |
| OS | macOS ProductVersion 27.2 (build 26B123), kernel 27.2.0 |
| serving engine | [Strata](https://github.com/Niko1221/Strata) for macOS (Flash-Next supported), engine version `not_recorded` |
| model build | same IQ3_S GGUF build family; on-box copy path differs |

**Sensors:** temperature/power/VRAM-per-component ✖ `not_available` (Apple
silicon does not expose via the sampler) · memory via sysctl ✔. Cross-box
*quality* comparisons use this box; *speed/power* comparisons do not (sensor matrix differs).
