# Bank-defect queue for owner clarification — A-ex6-03, C-ex6-02, K-ex6-03 (+ C-ex6-00/01 reach limit)

Raised while attributing the pair-239 / pair-240 / pair-241 / pair-242 losses. Recorded, not
patched around: the bank bytes and the frozen scorers stay exactly as published. The contour line
stays `0.0.2.40`; no pair launches against these cells until the owner ships a clarified bank
(see the pair-242 closure in `REVIEW-INBOX.md`).

Bank identity for every number below: published `benchmarks/hard/bank-hard-v6.json` sha16
`9ec86dfca4a6f85f`; run-workspace `bank.json` sha16 `f4553aab304f60d7` (the bank every quoted row
ran on). Evidence method: prompts and references re-computed from the shipped bytes, snippets
executed on CPython, and a tally over ALL 28 published results directories
(`full-*`, `pair-*`, `four-arm-v61`, probes). Every cited row lives in those directories.

## A-ex6-03: the reference is computed from a base the prompt never prints

Task as shipped (verbatim):

> Зарплата: gross=9500.0. Соцвзнос 22% от базы (gross), но не более 6100. Налог 19% от
> (gross - соцвзнос - вычет 1200), не менее 0. Верни JSON {"social","tax","net"}
> (net = gross - social - tax).

Reference: `social=1254.0, tax=616.74, net=7629.26`.

- The prompt states база = gross = 9500.0. Faithful execution (re-run from the shipped text):
  `social = min(0.22*9500, 6100) = 2090.0`, `tax = 0.19*(9500-2090-1200) = 1179.9`,
  `net = 6230.1`.
- `social = 1254.0` implies a base of `1254.0/0.22 = 5700.0`, and `tax = 616.74 = 0.19*(5700-1254-1200)`
  fits that same hidden base — but **5700 appears nowhere in the prompt**. The reference then
  computes `net` from gross=9500 anyway (`9500-1254-616.74 = 7629.26`), so the gold itself does not
  satisfy its own stated chain (`0.19*(9500-1254-1200) = 1338.74 ≠ 616.74`). This is the
  generator/prompt desync family: same shape as `J-ex6-03` on bank v6 (data table not shipped),
  which was fixed in v6.1 rather than papered over.
- Published evidence: **89/89 rows across all published arms score below 1.0** — every contour
  stamp, every seed, and both external raw brains; 87 carry `fields_mismatch:net,social,tax`.
  The dominant answer block is exactly the faithful `social=2090.0` (35 rows at
  `2090.0/1122.9/6287.1`, 22 at `2090.0/1103.9/6306.1` — the models' own slips in `tax` are
  genuine errors, but even the perfect faithful `1179.9` scores 0). No cell in the published tree
  has ever passed this task.
- NOT a defect: the `tax` arithmetic of individual answers; the cap wording (6100) is consistent
  and simply inactive at gross=9500.
- Proposed bank v6.2 (owner's call, not applied by me): either print the real base in the prompt
  ("Соцвзнос 22% от базы 5700") or regenerate the reference from the shipped gross=9500.

## C-ex6-02: the reference contradicts its own snippets, all of which print `[1, 2, 3]`

Task as shipped (verbatim): "Python: какой вариант печатает [1, 2, 3]?" with

> A: sorted({3,2,1,1})   B: list(set([1,2,3,3]))   C: sorted([3,1,2])   D: [3,2,1][::-1][:3]

Reference: `letters=["C"]`.

- Executed on CPython (the runtime the task is about): `A -> [1, 2, 3]`, `B -> [1, 2, 3]`,
  `C -> [1, 2, 3]`, `D -> [1, 2, 3]`. A set of small ints iterates in ascending order in CPython,
  so even the intended distractor B prints the target. A, C, D are unconditionally right; even
  treating B as implementation-defined, `want=["C"]` is refuted by A and D alone.
- Published evidence: **89/89 rows score 0** across every contour arm and both raw brains.
  Observed answer blocks: `A,C,D` x27, `C,D` x25, `A,B,C,D` x24 — three different reasoning
  errors, none reachable, because the only defensible superset answer still mismatches the gold.
  Notes: `set_mismatch got=... want=['C']` on every scored row.
- Contour cannot and does not touch this: the 2.41 rule-grounding grammar reads the prompt's own
  stated rule; this prompt states none, and every C prompt without a stated rule refuses
  byte-identically (pair-242 wiring proof, zero touched refusals).
- Proposed bank v6.2: make one option genuinely non-printing (e.g. `B: sorted({3,2,1}, reverse=True)`)
  and keep `want=["A","C","D"]`, or set the gold to the executed truth table. Owner's call.

## K-ex6-03: the boolean field's value form is unstated (weaker defect)

Task as shipped (verbatim):

> Извлеки поля. Верни ровно 4 строк вида FIELD: значение, по одному полю на строку, без пояснений.
> Заявка RFQ-9: поставка 200 кресел 'Oslo', срок 14 недель, доставка бесплатная.
> Поля: ITEM, QTY, LEAD_WEEKS, FREE_SHIPPING

Reference: `["кресла Oslo", "200", "14", "yes"]`.

- The Russian prompt never states that `FREE_SHIPPING` takes an English `yes`. The frozen scorer
  (`check_K_v6`, unchanged) matches case-insensitive substring or stem-token overlap; the gold
  token `yes` has no ≥4-char token to stem-match, so the Russian answers `да` / `бесплатная`
  cannot bridge to it and lose exactly 0.25.
- Published evidence: **81/91 rows pass** — the cell is mostly fine; exactly 9 rows lost 0.25 on
  `value:FREE_SHIPPING` (forms `бесплатная` x4, `да` x3, `true` x2), plus one old malformed row
  that typed the literal `FIELD:` prefix into every line and missed all four fields (a model
  format error, not the defect). This is a contract gap, not a blocker; it costs the smallest
  share of the queue and is listed for completeness.
- Proposed bank v6.2: state the value form in the field spec (`FREE_SHIPPING: yes/no`).

## C-ex6-00 / C-ex6-01: NOT defects — the published reach limit

`C-ex6-00` ("По политике безопасности production-базы: какие действия ДОПУСТИМЫ?") and `C-ex6-01`
("по общим правилам (без поиска в интернете)") state no rule inside the prompt. The proven
zero-token grounding family (0.0.2.40 J membership, 0.0.2.41 C rule-ground — both refused
byte-identically here, pair-242) can only re-derive rules the prompt itself carries. Grounding
these two would inject the maintainer's verdict — the 0.0.2.30 lesson. If the owner wants this
family to reach them, the clarification is to print the policy/rule text in the prompt (a
`C-ex6-00` candidate line: "Политика: допустимы миграции с репети-прогоном, чтение реплик и
записи в test.* с автоочисткой; ручные правки GUI и drop без согласования запрещены"), then
re-run the four arms. That is an owner-commanded bank change, never a contour move.

## What happens after the owner clarifies

Same protocol as `bank-defect-b04.md`: re-score BOTH sides on the clarified bank with
`scripts/rescore_all_arms.py` (stored answer bytes vs new references, and new-bank runs vs the
old scorer), and re-run the four arms (contour / raw ChatGPT / raw Grok / bare basalt) on the
clarified bank, because raw-arm improvement is the fairness check. Until then: contour line
`0.0.2.40`, frozen flags `C_RULE_GROUND=(2,41)`, `A_TABLE_ARITH=(2,33)/(2,38)`, and no new pair.
