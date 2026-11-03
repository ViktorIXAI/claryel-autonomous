# Passport MAC-STUDIO — high-memory comparison workstation
Live-collected 2026-11-01.

| field | value |
|---|---|
| role | mandatory paired duplicate for every adopted contour version (label `m`-suffixed files, `PARB_BOX=mac-studio`) |
| vendor/model | Apple Mac Studio, model id Mac15,14 |
| CPU | Apple M3 Ultra, 28 logical cores |
| memory | 274,877,906,944 B = 256 GiB unified |
| GPU | integrated (Metal); no discrete GPU |
| OS / kernel | macOS 27.2 (build 26B123), **desktop**, Darwin kernel 27.2.0; live check 2026-11-03 |
| serving engine | [Strata](https://github.com/Niko1221/Strata) repo v0.2.10, prebuilt Metal engine 0.1.56; text-only serve on :8080 (checked 2026-11-03) |
| model build | same IQ3_S GGUF build family; on-box copy path differs |

**Sensors:** temperature/power/VRAM-per-component ✖ `not_available` (Apple
silicon does not expose via the sampler) · memory via sysctl ✔. Cross-box
*quality* comparisons use this box; *speed/power* comparisons do not (sensor matrix differs).
