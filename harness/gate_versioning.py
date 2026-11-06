#!/usr/bin/env python3
"""Four-part version scheme for contour/harness releases, carrying two axes.

Canonical form: ``A.B.C.D``

* ``A.B``   — operator-controlled release line. The operator may change these
  first two digits without changing contour behaviour.
* ``C``     — contour track. ``1`` is the v1 contour family; ``2`` is the
  v2 contour family.
* ``D``     — revision inside that track. It changes whenever an audited
  release must be distinguishable in paired results: contour logic,
  measurement methodology, or gate reporting output.

``D`` serves two purposes at once, so the stamped revision alone cannot say
whether the model faced different behavior. The scheme therefore carries both:

* stamped revision (``CURRENT_REVISION``) — artifact identifier used by paired
  comparisons and by the ``at_least`` feature gates.
* contour behavior (``behavior_tuple``) — derived from ``CONTOUR_FEATURES``,
  the model-facing contour changes that actually exist in ``gate_run.py``. It
  moves only when a contour change is implemented, never when only measurement
  or reporting code changed.

History this records: revisions ``2.3`` (resource telemetry), ``2.4`` (full-Mac
resource verdict) and ``2.5`` (OS environment records) changed measurement and
reporting only. Their rows carry contour behavior ``2.2`` because nothing after
the F diagnostic grounding changed what the model is asked or given. A file
named for one revision can legitimately hold rows stamped with another;
``behavior_tuple`` re-derives the real behavior from the feature table, so old
rows stay interpretable and a planned-but-unbuilt revision can never be quoted
as if it changed the contour.

Legacy names are accepted: ``v2.2`` and ``2.2`` become the current release line
plus stamped revision ``2.2``.
"""
from __future__ import annotations

import os
import re

DEFAULT_RELEASE_LINE = (0, 0)

# Model-facing contour changes implemented in gate_run.py, oldest first. A new
# contour change adds its gate tuple here in the same commit that adds the
# gate; gate_versioning_test.py asserts the two stay in step.
CONTOUR_FEATURES = (
    (1, 7),  # form repaired by code, no extra model call
    (1, 8),  # one targeted nudge per scorer-note kind
    (1, 9),  # D action-order normalized into parser-required slots
    (2, 0),  # G/H post-normalization
    (2, 1),  # H safety normalization
    (2, 2),  # F diagnostic grounding
    (2, 7),  # K tax-negation flag grounded in the task's own text
    (2, 9),  # H best-of-2: lottery-class H notes answered by one more sample + strict-best selection
    (2, 10),  # E multi-failure repair feedback (up to 4 failing tests with their source lines)
    (2, 11),  # D-loop best-of-2: status-filter / dangerous-action lotteries answered by one more loop run + strict-best
    (2, 12),  # truncation budget: ladder ceiling raised to 8192 after a real finish=length at 2048
    (2, 13),  # C format normalization (letters-only contract kept) + C best-of-2 for missed_options lotteries
    (2, 14),  # checker-keyword post-normalization OFF by default (issue #15: no scorer-keyword injection in official score; STRATA_CHECKER_INJECT=1 reproduces historical 2.0-2.13 behaviour)
    (2, 15),  # deterministic format repair: B/D object unwrap, J id-sequence (zero model tokens)
    (2, 16),  # loop-v2 drive: protocol re-ask on an off-protocol turn, in-place gate_rejected marker (no duplicate terminal row), and re-admission of the model's own answer when the early-answer gate left the loop answerless
    (2, 17),  # the 2.15 deterministic format repair reaches the official pipeline: keyword-free repair unbundled from CHECKER_INJECT (issue #15 keeps injection itself OFF)
    (2, 18),  # K boolean synonym canonicalize: true/false -> yes/no on yes/no fields; keyword-free, independent of CHECKER_INJECT
    (2, 19),  # H JSON contract: clear fabricated claims/actions_done arrays (v6 scorer fail-hard); keyword-free
    (2, 20),  # K bool Cyrillic: да/нет -> yes/no on yes/no fields (extends 2.18 true/false)
    (2, 21),  # D-plain uses check_D_plain_v6 (stop mis-routing plain D through loop scorer)
    (2, 22),  # F JSON: next short-id + empty avoid backfill from prompt N-options
    (2, 23),  # K SERVICE alias: prompt Cyrillic hosting forms -> Latin hosting
    (2, 24),  # I duration list: re-sort [label, seconds] pairs by seconds ascending
    (2, 25),  # G short-context: discount no-stack conflict JSON by code
    (2, 26),  # G conflict overwrite when clauses/values disagree with prompt pair
    (2, 27),  # A arithmetic by code from prompt numbers (invoice/FX/proration/trim)
    (2, 28),  # H requires/unknown filled from explicit prompt signature constraint
    (2, 29),  # C coverage_choice contract: option letters read from the task text, answer line built from the model's own verdicts
    (2, 30),  # contract guarantee: an answer with no parseable artifact gets one shape-only re-ask, then deterministic salvage of the model's own text (MEASURED NEGATIVE on bank v6.1, see PAIR-230-V61.md)
    (2, 31),  # self-consistency vote for set/order answers (C letters, J id lists): two extra samples of the same task, the plurality answer wins, no scorer and no reference consulted (MEASURED NEGATIVE on bank v6.1, see PAIR-231-V61.md: the model is biased on these cells, so voting amplifies its own mistake; frozen to this stamp)
    (2, 32),  # J ranking repair: the answer's id order re-derived from the (id, value) table and direction phrase already in the prompt; deterministic, zero model tokens, no reference read, permutation-only over the ids the model listed, refused whenever the rule grammar is unsure (MEASURED +1.3 cells at three seeds, BELOW the ~2-cell noise floor: on-target but unresolvable, NOT adopted, frozen to this stamp, see PAIR-232-V61.md)
    (2, 33),  # A threshold-table arithmetic: a tariff chain «N if var>=T [и var>=T], иначе X» plus «id=... var=Nunit» rows — the map values and the total are recomputed by code from the prompt's own table (the adopted 2.27 family); refuses on any ambiguity, membership of the model's own map keys must equal the prompt rows, reference never read (MEASURED +1.3 cells at three seeds with ZERO live fires in the candidate arm — counterfactual replay on saved bytes repairs the failed control seed, but the arm delta contains no on-target cells: unresolvable, NOT adopted, frozen to this stamp, see PAIR-233-V61.md)
    (2, 34),  # B field completeness: extraction fields recomputed by code from the prompt's own data block — a key:value/- item config block (B-ex6-03 shape) and an embedded-JSON echo-with-count rebuild (B-ex6-05 shape); required names come from the prompt's own JSON spec, extra model keys refuse, any ambiguity refuses, reference never read. Category K excluded: its failing seeds need value SHAPES the prompt never states (bank clarification, not contour guess — the 2.30 lesson). (MEASURED -1.0 cells at three seeds with ZERO live fires in either grammar — the config grammar accepts 1 of 7 B prompts and no-ops, the echo grammar matches 1 and refuses on every saved answer for an extra model key, and the two B cells that actually lose sit outside both grammars: unresolvable, NOT adopted, frozen to this stamp, see PAIR-234-V61.md)
    (2, 35),  # B markdown-table aggregation: a *_total field whose own spec formula names the prompt's table columns (base, «без X», «минус Y») is recomputed by code from that table, including the footnote adjustment the table declares («[1] включает 8 в_transit»); column names matched by stem, one match required, ragged table / unnamed column / unnamed footnote / several footnote numbers / non-numeric cell all refuse and touch nothing, the model's key set is never changed, reference never read. Targets the one B loss no earlier B grammar reaches (B-ex6-06: the model returns a row subtotal where the spec asks for the sum over rows). (MEASURED pair-235, three paired seeds: the mechanism is the strongest confirmed in the series — it fired on exactly its target cell in all three seeds, B-ex6-06 0/3 -> 3/3, `contour:v235_b_table_total` on every converted row, zero extra model calls. But the arm mean moved +2.0, exactly AT the ~2-cell resolution floor, and four off-target cells flipped without any 2.35 event, breaking the pre-registered clean pattern (exactly one cell flips, carrying its event). Per the pre-registered rule and the noise-floor rule: NOT adopted, frozen to this stamp, see PAIR-235-V61.md.)
    (2, 36),  # group-4 lottery selection: UNSTABLE-CELLS-V61 group 4 (`unknown_missing`, `requires_missing:<field>` on H, `avoid` on F) is the newest live failure class and every one of its cells is a seed lottery (4/6-5/6 pass at identical seeds), the class the selection doctrine fixes rather than nudges. Extends the proven 2.9 best-of-2 recipe to those notes: one more sample (H offset seed+8117 kept, F seed+5501), strict-best adoption only, and prefix-matches the parameterized `requires_missing:<field>` note name (the 2.11 lesson: a parameterized note never equals its bare name). Stamps below 2.36 keep the exact old H predicate byte-for-byte. (MEASURED pair-236, three paired seeds: 6 fires — H-ex6-01 x3, H-ex6-03 x1, F-ex6-00 x2 — ZERO converted scoreboard cells; the F wins raised an already-passing cell, and the H re-samples never beat the first draw because the extra sample omits the same component: the class is content-biased, not variance (the 2.31 mode). Arm mean −1.0: NOT adopted, frozen to this stamp, see PAIR-236-V61.md.)
    (2, 37),  # re-adoption of the confirmed B markdown-table aggregation (the only mechanism in the series with a deterministic full-event cell conversion: 2.35 fired 3/3 on B-ex6-06 only and moved it 0/3 -> 3/3 at zero model tokens, PAIR-235-V61.md; its 2.35 arm mean sat exactly at the noise floor only because event-less cells flipped alongside), measured at 2.37 under a pre-registered all-or-nothing attribution rule; plus the freeze of the measured-negative 2.36 group-4 lottery to exactly 2.36. 2.30-2.34 and 2.36 stay frozen to their own stamps and inherit into 2.37 nothing. (MEASURED pair-237, three paired seeds vs 0.0.2.29: the pre-registered pattern held exactly — B-ex6-06 strict-failed 0/3 in control, strict-passed 3/3 in candidate with contour:v235_b_table_total on every converted row, no other 2.37-gated event; arm mean +2.4 (62,63,66 vs 62,59,63), pooled 10W/3L p=0.09, the +1.0 attributable to the mechanism and the rest stated as event-less noise. ADOPTED as the new control line, PAIR-237-V61.md.)
    (2, 38),  # re-adoption of the 2.33 A threshold-table arithmetic (UNSTABLE-CELLS group 3, the newest live class after group 4 closed): pair-237's adopted line lost A-ex6-00 in two of three seeds with fields_mismatch:surcharges,total, and replaying the frozen 2.33 grammar over exactly those published bytes repairs both to 1.00 strict with its v233_a_tariff_table event and no-ops the passing bytes (gate_v50 pins the replay). pair-233 froze the stamp only because its arms never produced an on-target cell (zero live fires), never because the mechanism lost. Re-landed as the single candidate change at 2.38 under a pre-registered rule; the 2.33 arm stays byte-identical; everything measured-negative (2.30/2.31/2.36) and everything unresolved-and-unconverted (2.32/2.34) stays frozen to its own stamp. (MEASURED pair-238, three paired seeds vs 0.0.2.37: UNMEASURED per the pre-registered rule (a) — the adopted line passed A-ex6-00 in all three control seeds, so the pair carried no live on-target cell; the grammar's single live fire landed on the target task in a candidate seed whose raw bytes needed the repair, with no control failure to attribute a conversion to. Arm +1.0 (62,62,66 vs 62,60,65) is below the ~2-cell floor either way. NOT adopted, the flag stays frozen at 2.38, the line stays 0.0.2.37, see PAIR-238-V61.md. Lesson recorded there: pair targets must be chronic stable-fail cells, not one pair's lottery losses — this is the second zero-opportunity pair after 2.33.)
    (2, 39),  # J ranking repair RE-LANDED with grammar v2 (the 2.32 mechanism, coverage raised on exactly the four refusal gaps pair-238 published: the ё adjective `дешёвых`, a primary key named only by its genitive form in the rule or by the `при равенстве <col>` lead, a unique-prefix filter column name (`срок` for `срок_дней`), and an explicit product key `A*B` over two prompt-table columns together with a fully-stated tie chain — every segment must parse or the rule refuses). Same fail-closed contract as 2.32: permutation-only over the ids the model listed, membership never changed, formula/average/weight rules still refuse, ambiguity refuses, reference never read, zero model tokens. Coverage stated before launch: v1 3/7 reproduces, v2 6/7, the one formula task (J-ex6-03) stays refused, mis-sorts 0; over every published pair-238 J row v2 converts all six chronic J-ex6-02 losses (product+tie chain), repairs one J-ex6-06 order flip, and regresses ZERO of the 36 rows (gate_v48 pins the replay). The v1 grammar stays byte-identical at its own stamp 2.32; 2.39 runs v2 only. The pair-238 UNMEASURED A threshold arithmetic does NOT ride into 2.39: `A_TABLE_ARITH` is pinned to exactly (2,33)/(2,38), so the candidate's only mechanism delta over the adopted line is grammar v2.
)

# Revisions 2.3-2.6 are permanently reserved: they were released as
# measurement/reporting revisions with contour behavior 2.2. A new contour
# feature may never be registered inside that band, because historical rows
# stamped 0.0.2.3-0.0.2.6 must keep resolving to behavior 2.2 forever.
RESERVED_TOOLING_REVISIONS = (2, 3), (2, 4), (2, 5), (2, 6), (2, 8)

# Artifact identifier of the current release: 0.0.2.6 separated the two axes,
# 0.0.2.7 adds the K tax-negation contour change, 0.0.2.8 adds the engine-stall
# guard (measurement validity: stalled responses are no longer scored as wrong
# answers, and every run records the conditions it was measured under). Bump this
# for any audited release; move the contour axis only by adding a gate tuple to
# CONTOUR_FEATURES — never inside the reserved tooling band.
CURRENT_REVISION = (2, 39)
CURRENT_STAMP = "0.0.2.39"


def _digits(value: str) -> list[int]:
    return [int(x) for x in re.findall(r"\d+", value)]


def parse_release_line(value: str | None = None) -> tuple[int, int]:
    raw = os.environ.get("PARB_VERSION_PREFIX") if value is None else value
    parts = _digits(raw or "")
    if len(parts) >= 2:
        return (parts[0], parts[1])
    return DEFAULT_RELEASE_LINE


def parse_version(value: str | None = None) -> tuple[int, int, int, int]:
    raw = os.environ.get("PARB_GATE_VERSION") if value is None else value
    s = str(raw or "").strip().lower()
    if not s:
        return parse_release_line() + CURRENT_REVISION
    s = s.replace("contour", "").replace("v", "", 1).strip()
    parts = _digits(s)

    if len(parts) == 2:
        return parse_release_line() + (parts[0], parts[1])
    if len(parts) == 4:
        return (parts[0], parts[1], parts[2], parts[3])

    raise ValueError(f"unsupported contour version: {raw!r}")


def registered_stamp(value: str | None = None) -> tuple[int, int, int, int]:
    """Strict stamp check for an official arm run (0.0.2.29 bookkeeping).

    `parse_version` stays tolerant on purpose: a stamp ahead of the newest implemented feature is
    a reporting release and `behavior_tuple` tops out at the newest feature (contract in
    gate_versioning_test). That tolerance is wrong at arm-start though: a typo such as
    PARB_GATE_VERSION=0.0.2.228 parses as contour 2.228, turns on EVERY shipped feature, exits 0
    and writes healthy-looking ledgers. Two such "arms" under two labels produced a fake paired
    comparison with zero flips. Official runs therefore call this and die on an unknown stamp.
    """
    parsed = parse_version(value)
    stamp = parsed[2:]
    if stamp > CURRENT_REVISION and stamp not in RESERVED_TOOLING_REVISIONS:
        raise ValueError(
            "unknown contour stamp %r: it selects %d.%d, newer than the newest release "
            "0.0.%d.%d. Fix the stamp — an unknown one must not silently enable every shipped "
            "feature (see harness/gate_v45_stamp_guard_test.py)."
            % (value if value is not None else os.environ.get("PARB_GATE_VERSION"),
               stamp[0], stamp[1], CURRENT_REVISION[0], CURRENT_REVISION[1]))
    return parsed


def contour_tuple(value: str | None = None) -> tuple[int, int]:
    """Stamped revision: what feature gates and paired comparisons select."""
    return parse_version(value)[2:]


def behavior_tuple(value: str | None = None) -> tuple[int, int]:
    """Contour behavior actually implemented at that stamp.

    A stamp newer than the newest implemented contour feature is a measurement
    or reporting release, so it reports that newest feature. Tooling revisions
    can never be read as a new contour generation.
    """
    stamp = contour_tuple(value)
    enabled = [feature for feature in CONTOUR_FEATURES if feature <= stamp]
    return max(enabled) if enabled else (0, 0)


def format_version(value: str | None = None) -> str:
    return ".".join(str(x) for x in parse_version(value))


def format_behavior(value: str | None = None) -> str:
    return ".".join(str(x) for x in behavior_tuple(value))


def at_least(track: int, revision: int, value: str | None = None) -> bool:
    return contour_tuple(value) >= (track, revision)


def summary(value: str | None = None) -> dict[str, object]:
    version = parse_version(value)
    stamped = ".".join(str(x) for x in version[2:])
    behavior = ".".join(str(x) for x in behavior_tuple(value))
    return {
        "canonical_version": ".".join(str(x) for x in version),
        "release_line": ".".join(str(x) for x in version[:2]),
        "contour_version": stamped,
        "contour_behavior": behavior,
        "contour_changed_at_this_release": behavior == stamped,
    }
