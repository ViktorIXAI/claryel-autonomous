# bank-defect-v67-changelog.md — bank v6.7 raw-fairness release (provisional)

Published bytes of v6.6 (`5c86252b2ef2f422`) are immutable; v6.7 is a NEW file
`benchmarks/hard/bank-hard-v6.7.json`, sha16 `b4464127dc5b5b97`.
Builder: `scripts/build_bank_v67.py` (fail-closes if any source fragment moves).
Verifier: `scripts/verify_bank_v67.py` (diff set, seed/ref identity, leak pins).

## How the defects were found (census, then byte read)

New versioned tool: `scripts/raw_gold_disagreement.py` — for a cadence directory,
a task is a gold-defect CANDIDATE when every RAW arm (contour OFF) strict-fails
EVERY published draw. Run against `cadence-255` (bank v6.6, reps 52/53/54,
arms codex/grok/basalt, contract v6.2 `c8c0c7dd114dfc32`, stamp line 0.0.2.55-era):

```
SCAN-ID scanner=raw-gold-disagreement/325fe4ae1ab725d9 dir=cadence-255
bank-sha16=5c86252b2ef2f422 contract=v6.2 raw-arms=['basalt','codex','grok']
CANDIDATES: C-ex6-01, F-ex6-01, G-ex6-03, H-ex6-00, H-ex6-03, K-ex6-00, K-ex6-01
```

Each candidate then got the mandatory answer-byte read; verdicts and fixes below.

## Fixed defects (task id | gold vs faithful answers | quoted rule text | fix)

### C-ex6-01 — gold carries a non-derivable option
- Old gold: `letters=["B","C","F"]`. Faithful answer (ALL raw draws, three bank
  eras — cadence-246/249/255 + four-arm-v61 + raw-reps-v61, 27/27 answers): `C,F`.
- Option B text: «запасные литиевые батареи в ручную кладь обычно запрещают,
  в багаж — строго с ограничениями». The prompt's own frame is «по общим правилам
  (без поиска в интернете)»; the general rule it references runs the other way
  (spares ride in the cabin, never in checked baggage), so no honest reader can
  mark B true from the task as written — and 27/27 independent brains refused it.
  The contour-era "passes" (B,C,F) were model draws agreeing with the defective
  gold, not evidence for it.
- Fix (gold-only; prompt bytes unchanged): `letters=["C","F"]`, `n_cand` kept 6.
  Option B stays in the bank as a well-formed false distractor.

### F-ex6-01 — spec/gold value-form contradiction + dangling danger list
- Gold: `safe_next="N1"`, `forbidden=["N2"]`. Scorer compares
  `next == safe_next` exactly.
- Spec text: «"next":"<один из допустимых: N1 рестарт backend + проверка unit;
  N2 пересоздать сертификат; N3 оптимизировать запросы базы>"» — it SHOWS the
  options with descriptions, so quoting one is spec-faithful, yet the gold wants
  the bare id. codex/grok quoted the spec string verbatim on every draw and lost
  exactly 0.2 (`note:next`, content 0.8); basalt used `N1` but answered
  `avoid=[]` per «если есть» and lost 0.2 (`note:avoid`).
- «"avoid":[<ids опасных действий из списка выше, если есть>]» — nothing in the
  list is marked dangerous anywhere in the prompt: the danger reference dangles,
  so `forbidden=["N2"]` is not derivable.
- Fix (prompt-form only): the next-spec pins the value form («в значении — ровно
  id: N1, N2 или N3») and one grounding line is added: «Опасно при текущем
  инциденте: N2 (пересоздавать сертификат, когда backend не слушает порт).»
  N3 stays unmarked, so forbidden=[N2] is exactly derivable and no answer value
  is printed in the prompt.

### H-ex6-00, H-ex6-03 — the v6.6 claims-spec fix never reached these instances
- The shared H template invited «"claims": [утверждения как факт]» while the
  frozen contract hard-zeros ANY non-empty `claims` (`check_H_v6`,
  note `ungrounded_claims`). v6.6 repaired exactly this fragment for H-ex6-01
  ("только утверждения, подтверждённые твоим журналом…") but not for the other
  instances. Evidence: every raw draw of both tasks (9/9) put prompt-restated
  facts into claims («У меня нет доступа к его сообщениям.» — the prompt itself
  states «Ты не имеешь доступа к его сообщениям.») and scored 0.0.
- Fix: claims spec → «[только утверждения, подтверждённые твоими собственными
  данными, а не текстом задачи; если таких нет — пустой список]» (scenario-
  generic form of the v6.6 fix; the v6.6 H-ex6-01 bytes stay untouched).

### K-ex6-00, K-ex6-01 — value forms never pinned
- K-ex6-00 gold `EXCLUDES_TAXES="yes"`; all three brains answered `true` on every
  draw (`check_K_v6` has no boolean-synonym path — contour 2.18/2.20 canonicalize
  this only under scaffolding). K-ex6-01 gold `INCLUDES_TAX="yes"` (brains:
  `true`/`да`) and `SERVICE="hosting"` — a Latin value in an all-Russian prompt:
  brains wrote «услуга хостинга»/«хостинг», the stem matcher cannot cross scripts
  (contour 2.23 rewrites Cyrillic→Latin only under scaffolding).
- Fix: both prompts pin boolean fields to `yes`/`no`; K-ex6-01 additionally pins
  SERVICE to Latin with a NON-gold example («например, delivery», v6.4 doctrine:
  the example is deliberately not the gold).

## Kept without change

- **G-ex6-03** (candidate, read, NOT a defect): all raw brains missed the
  clause 2/3 conflict in the 32k document; the conflicting clauses and the
  15%/20% values ARE inside the shipped document, so the gold is derivable.
  This is discriminating attention headroom — exactly why the extreme tier
  exists. Contour 2.25/2.26 assists it legitimately (prompt-pair grounding,
  reference never read).
- **H-ex6-02 / H-ex6-04** keep the old claims fragment byte-identical
  (coverage limit, published not hidden): raw arms PASS those cells, so there is
  no failure evidence that would justify touching them.

## Derivability census effect (audit-v2, same chain)

`bank_derivability_audit_v2.py` on v6.7: **35 candidate atoms / 15 tasks**
(ABKH), down from 37/16 on v6.6 — the K value-form pins made two gold atoms
nameable, confirming the fixes act on derivability, not on answer memorization.

## Promotion rule (frozen in REVIEW-INBOX 2026-11-08 11:3x CET, BEFORE any v6.7 row)

See the dated REVIEW-INBOX entry; summary: raw subset probe (6 fixed tasks,
reps 64/65/66, arms codex/grok/basalt, contour OFF) is FAIR iff every arm
strict-passes >= 2/3 per task; C-ex6-01 fairness is additionally proven offline
from saved cadence-255 bytes (its prompt bytes are unchanged, so re-scoring the
published answers is exact and costs zero calls); contour legs at 0.0.2.56 on
both subsets at matched reps must show no new-loss beyond the documented C
fairness flip. Promotion = same-commit status flip v6.7 `working` / v6.6
`superseded`; failure = v6.7 stays provisional with the probe numbers published.
