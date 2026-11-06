# Bank defect: B-ex6-04 asks for a year the prompt never states

Found in the contour 0.0.2.29 full arm on bank v6.1 (`../full-229/`), while attributing the lost
B cells. Not a contour failure, so it is not "fixed" by a contour change — it is recorded.

## Task as shipped

> Письмо: 'Контракт NN-42 подписан 3 марта, старт работ 1 апреля, бюджет 48000 EUR, штраф за
> просрочку 2% в неделю. Мой отпуск 10-20 марта к этому не относится.'
> JSON: {"contract","start_date":"ГГГГ-ММ-ДД","budget_eur":число,"penalty_per_week"}.

Reference: `{"contract": "NN-42", "start_date": "2026-04-01", "budget_eur": 48000, "penalty_per_week": "2%"}`.

## Why it is not answerable as written

The letter gives day and month only ("подписан 3 марта", "старт работ 1 апреля"). No year appears
anywhere in the prompt, and no date in the surrounding text pins one: an answer of
`2024-04-01`, `2025-04-01` or `2026-04-01` is equally consistent with the evidence given, while the
scorer requires `2026-04-01` exactly. The contour answer `2024-04-01` is therefore not a reasoning
error; the task has no determinate answer. Same class as `J-ex6-03` on bank v6 (data table missing),
which was fixed in v6.1 rather than papered over by the contour.

## Second, smaller finding in the same cell

`penalty_per_week`: the model emitted the number `2`, the reference wants the string `"2%"`. The
prompt states the value with a unit ("2% в неделю") and gives no type for this field (unlike
`budget_eur: число`). Strict type equality here is a scoring policy choice, not a content error —
worth stating explicitly in the bank contract: either declare `penalty_per_week: "<число>%>"` in the
field spec, or accept number and unit-annotated string as equal.

## What is NOT a defect

`B-ex6-06` (`available_total`: reference 60, model 30) is a genuine model failure: the table gives
W1 50 (of which 8 in transit, minus reserve 12) and W2 30, and the field definition asks for the
total. 30+30=60 is computable from the shipped text.

## Proposed bank v6.2 (owner's call, not applied by me)

- B-ex6-04: state the year in the letter ("подписан 3 марта 2026"), and declare the
  `penalty_per_week` value form in the field spec.
- Re-score both frozen sides after the change: old answers against the new reference and new bank
  against the old scorer, so nobody can claim the fix moved the score. `scripts/rescore_all_arms.py`
  already re-scores stored answer bytes for exactly this purpose.
