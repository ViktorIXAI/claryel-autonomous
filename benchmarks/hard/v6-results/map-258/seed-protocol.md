# map-258 seed protocol audit (sp1)

Seed protocol: `gseed = int(sha256(f"{task}|{rep}")[:8], 16) % 999983` — identical on every box,
so (task, rep) pairing is exact and the whole seed set is re-derivable from the published
`plan-rep25/26/27.json`.

Legs and reps (map legs of the adopted line, fresh matched seeds):

| leg | rep | tasks | loop |
|---|---|---|---|
| c68r25 | 25 | 77 | 6 |
| c68r26 | 26 | 77 | 6 |
| c68r27 | 27 | 77 | 6 |

Audit result: **231/231** result rows have `gen.request_seed` == the plan `gseed` == the sp1
formula value, for every (task, rep). Zero mismatches. Bank v6.8 `7a9527bf2e4ebbff`
(ws copy `361f7bdb24d6ac71`), scorer contract v6.2 `c8c0c7dd114dfc32`, contour stamp 0.0.2.56
(behavior 2.56), harness git `22516491b30748e14945972aca1b74d43ad0168e`.
