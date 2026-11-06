# Contour cell stability across 6 seeds (stamp 0.0.2.29, bank v6.1)

Ledgers: ledger-c229full.jsonl, ledger-c229r12.jsonl, ledger-c229r3.jsonl, ledger-c229r45.jsonl. Reason strings are recomputed from the published answer bytes with the frozen scorer; contour events come from the same ledger rows.

stable pass 52, stable fail 5, seed-unstable 14 of 71 cells

Stable fails (candidate bank or model ceiling): A-ex6-03, B-ex6-04, B-ex6-06, C-ex6-02, J-ex6-02

| task | cat | passes / seeds | reason in a failing seed | contour events in a failing seed |
|---|---|---|---|---|
| J-ex6-01 | J | 1/6 (...P..) | j content=0.00 format=False ['no_list'] | — |
| C-ex6-00 | C | 3/6 (P..PP.) | c content=0.00 format=False ['no_answer_line'] | — |
| C-ex6-01 | C | 4/6 (.PPP.P) | c content=0.00 format=False ['no_answer_line'] | — |
| F-ex6-00 | F | 4/6 (P..PPP) | f content=0.00 format=False ['no_json'] | — |
| A-ex6-00 | A | 5/6 (PP.PPP) | a content=0.00 format=False ['no_json'] | — |
| B-ex6-03 | B | 5/6 (PP.PPP) | b content=0.00 format=False ['no_json'] | — |
| B-ex6-05 | B | 5/6 (PPP.PP) | b content=0.00 format=False ['no_json'] | — |
| C-ex6-03 | C | 5/6 (PPPPP.) | c content=0.00 format=False ['no_answer_line'] | — |
| H-ex6-00 | H | 5/6 (PPPP.P) | h content=0.00 format=False ['no_json'] | — |
| H-ex6-01 | H | 5/6 (.PPPPP) | h content=0.00 format=False ['no_json'] | — |
| H-ex6-03 | H | 5/6 (PPPPP.) | h content=0.00 format=False ['no_json'] | — |
| J-ex6-03 | J | 5/6 (P.PPPP) | j content=0.00 format=False ['no_list'] | — |
| J-ex6-06 | J | 5/6 (PP.PPP) | j content=0.00 format=False ['no_list'] | — |
| K-ex6-03 | K | 5/6 (PPPPP.) | k content=0.00 format=False ['missing:ITEM', 'missing:QTY', 'missing:LEAD_WEEKS', 'missing:FREE_SHIPPING'] | — |

Reading rule: a cell that flips between seeds is not a scoring mystery, it is the model giving a
different answer under a different seed. Only a mechanism that makes the model re-check that
answer can convert it, and converting it is measurable cell by cell.

## What the map actually says (05:55 CET)

Twelve of the fourteen unstable cells fail with a **parse collapse**: `no_json`, `no_list`,
`no_answer_line`. In the losing seed the contour emitted prose where the contract demanded a JSON object,
a JSON list or an answer line, and nothing repaired it — the ledger shows no contour repair event in those
seeds. So the seed-to-seed spread of this stamp is mostly **not the model changing its mind**; it is the
contract sometimes not being enforced.

That is the cheapest measurable target in this benchmark, and it is contour-side work rather than a model
swap: guarantee the artifact shape (bounded re-ask, then deterministic salvage) and these cells stop being
coin flips. The measurable claim for a future stamp is per-cell — `x/6` becomes `6/6` — visible without
touching any frozen scorer.

The real content failures are the stable ones: `A-ex6-03`, `B-ex6-04`, `B-ex6-06`, `C-ex6-02`, `J-ex6-02`.
Two of them are documented bank defects (`B-ex6-04` demands a year the prompt never states;
see `bank-defect-b04.md`), so no gate should pretend otherwise.
