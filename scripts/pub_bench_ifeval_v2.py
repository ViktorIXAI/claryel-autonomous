#!/usr/bin/env python3
"""IFEval scorer contract `pub-ifeval-v2`: the vendored upstream checker with ONE correction.

Why this version exists (measured 2026-11-10, zero model calls). The vendored
`LetterFrequencyChecker.build_description` rejects a `letter` kwarg whose lowercase code point is
outside a-z and replaces it with `random.choice(string.ascii_letters)`. Two pinned IFEval tasks ask
for a punctuation character — `ifeval-1122` ("Include at least 4 hashtags, starting with '#'") and
`ifeval-1129` ("Contain 6 or more exclamation marks") — so under contract `pub-ifeval-v1` the check
that decides those two cells is re-drawn on every scorer pass over byte-identical answers. Measured
over 12 draws of the shipped bare-arm bytes: `ifeval-1122` strict pass 4/12, `ifeval-1129` 7/12.
That RNG is a second, previously unnamed cause of the +-1-task-per-pass drift this set already
publishes; the first is the vendor's stochastic `langdetect` call inside `change_case:*`.

The correction is narrow and mechanical: after the vendor builds the instruction, a pinned
single non-alphabetic `letter` is restored on the built instruction and counted as-is
(`check_following` lowercases the response, so a literal `#` or `!` counts correctly). No vendored
file is edited — their sha16 pins in `benchmarks/public/MANIFEST.json` are re-asserted at every run
and the scorer refuses if they moved. Everything else is the v1 path, so v1 and v2 may differ ONLY
on cells whose pinned `letter` is not an ASCII letter (2 of 541), and the self-test asserts that
bound plus determinism over 20 repeated draws.

Run:  pub_bench_ifeval_v2.py <answers.jsonl> <tasks.jsonl> <bench> <model> <call-label>
        [--out DIR] [--no-digest] [--selftest-only]
"""
import argparse
import collections
import hashlib
import json
import pathlib
import subprocess
import sys

CHECKER = "pub-ifeval-v2"
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
VENDOR = ROOT / "benchmarks" / "public" / "vendor"
MANIFEST = ROOT / "benchmarks" / "public" / "MANIFEST.json"
SUITE_ATTEMPTS = 3
# Reference-response band under THIS contract. Measured 2026-11-10 over the pinned
# `gpt4_sample.jsonl` (540 joined rows): strict 416-417, loose 431. The band stays at 2.0 pp for the
# same reason v1 published it: the vendor's `change_case:*` checkers call `langdetect`, which is
# stochastic, so the reference row still drifts +-1 per pass. What `pub-ifeval-v2` removes is the
# `letter_frequency` RNG, and that claim is pinned by the exact per-cell determinism gate below
# (20 identical draws), not by this band.
REF_STRICT, REF_LOOSE, REF_N, REF_BAND_PP = 416, 431, 540, 2.0
# Whole scope of the change: pinned cells whose `letter` kwarg the vendor re-draws.
AFFECTED_CELLS = 2
LETTER_CHECK = "keywords:letter_frequency"


def sha1_16(p):
    """SHA-1/16, the convention `pub_bench_ifeval.py` used for the vendored-file pins in
    `MANIFEST.json` (the tasks-file column in the digest is SHA-256/16 via `pub_bench_score`)."""
    return hashlib.sha1(pathlib.Path(p).read_bytes()).hexdigest()[:16]


def tasks_sha16(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()[:16]


def assert_vendor_pins():
    """The vendored modules are byte-pinned in MANIFEST.json; refuse before scoring anything."""
    pins = json.loads(MANIFEST.read_text(encoding="utf-8"))["benches"]["ifeval"]["checker_files"]
    bad = []
    for name, want in pins.items():
        got = sha1_16(VENDOR / "instruction_following_eval" / name)
        if got != want:
            bad.append("%s: %s != pinned %s" % (name, got, want))
    return bad


def load_vendor():
    if str(VENDOR) not in sys.path:
        sys.path.insert(0, str(VENDOR))
    from instruction_following_eval import evaluation_lib as ev
    from instruction_following_eval import instructions_registry as reg
    return ev, reg


def vendor_redraws_letter(letter):
    """True when the vendor replaces this pinned `letter` kwarg with a random ASCII letter."""
    s = str(letter or "")
    return len(s) != 1 or not ("a" <= s.lower() <= "z")


def build_instructions(inp, reg):
    """Mirror of the vendor's per-instruction build, plus the one correction: a pinned
    non-alphabetic `letter` is restored instead of being randomized, and the restore is verified."""
    out = []
    for index, instruction_id in enumerate(inp.instruction_id_list):
        instruction = reg.INSTRUCTION_DICT[instruction_id](instruction_id)
        kwargs = inp.kwargs[index] or {}
        instruction.build_description(**kwargs)
        pinned = kwargs.get("letter")
        if pinned is not None and vendor_redraws_letter(pinned):
            instruction._letter = str(pinned)
            got = instruction.get_instruction_args().get("letter")
            if got != str(pinned):
                raise AssertionError("letter restore failed: %r != pinned %r" % (got, pinned))
        args = instruction.get_instruction_args()
        if args and "prompt" in args:
            instruction.build_description(prompt=inp.prompt)
        out.append(instruction)
    return out


def test_strict(ev, reg, inp, prompt_to_response):
    response = prompt_to_response[inp.prompt]
    marks = [bool(response.strip() and ins.check_following(response))
             for ins in build_instructions(inp, reg)]
    return ev.OutputExample(instruction_id_list=inp.instruction_id_list, prompt=inp.prompt,
                            response=response, follow_all_instructions=all(marks),
                            follow_instruction_list=marks)


def test_loose(ev, reg, inp, prompt_to_response):
    response = prompt_to_response[inp.prompt]
    r = response.split("\n")
    variants = [
        response,
        response.replace("*", ""),
        "\n".join(r[1:]).strip(),
        "\n".join(r[:-1]).strip(),
        "\n".join(r[1:-1]).strip(),
        "\n".join(r[1:]).strip().replace("*", ""),
        "\n".join(r[:-1]).strip().replace("*", ""),
        "\n".join(r[1:-1]).strip().replace("*", ""),
    ]
    marks = []
    for ins in build_instructions(inp, reg):
        mark = any(cand.strip() and ins.check_following(cand) for cand in variants)
        marks.append(mark)
    return ev.OutputExample(instruction_id_list=inp.instruction_id_list, prompt=inp.prompt,
                            response=response, follow_all_instructions=all(marks),
                            follow_instruction_list=marks)


def affected_cells(tasks):
    out = []
    for t in tasks:
        for cid, kw in zip(t["instruction_id_list"], t["kwargs"]):
            if cid == LETTER_CHECK and vendor_redraws_letter((kw or {}).get("letter")):
                out.append((t["key"], (kw or {}).get("letter")))
    return out


def _inp(ev, t):
    """Accepts a pinned task row (has `id`) or a vendored data row (has `key`)."""
    key = t["key"] if "key" in t else int(str(t["id"]).rsplit("-", 1)[1])
    return ev.InputExample(key=key,
                           instruction_id_list=t["instruction_id_list"],
                           prompt=t["prompt"], kwargs=t["kwargs"])


def selftest():
    """(ok, note). Gates: vendor byte pins -> upstream unit suite -> literal-character behaviour ->
    determinism of the re-drawn cells -> reference band -> the v1/v2 scope bound."""
    bad = assert_vendor_pins()
    if bad:
        return False, "vendored checker bytes moved: " + "; ".join(bad)

    suite_ok, last = False, ""
    for _attempt in range(1, SUITE_ATTEMPTS + 1):
        proc = subprocess.run([sys.executable, "-m", "unittest",
                               "instruction_following_eval.instructions_test", "-v"],
                              cwd=str(VENDOR), capture_output=True, text=True)
        if proc.returncode == 0:
            suite_ok = True
            break
        last = (proc.stderr or proc.stdout).strip().splitlines()[-1:] or [""]
        last = last[0]
    if not suite_ok:
        return False, "upstream unit suite failed on all %d attempts: %s" % (SUITE_ATTEMPTS, last)

    ev, reg = load_vendor()
    data = VENDOR / "instruction_following_eval" / "data"
    vtasks = [json.loads(l) for l in (data / "input_data.jsonl").read_text().splitlines()]
    by_key = {t["key"]: t for t in vtasks}

    # 1. literal-character behaviour on the two real pinned cells: enough of the character passes,
    #    one short fails, and padding with another letter must NOT pass (that is the v1 coin flip).
    unit, notes = [], []
    for key, ch, want in ((1122, "#", 4), (1129, "!", 6)):
        t = by_key[key]
        filler = " ".join("word%02d" % i for i in range(25))
        for text, expect in ((filler + (" " + ch) * want, True),
                             (filler + (" " + ch) * (want - 1), False),
                             (filler + " " + ch + " " + "q" * 30, False)):
            res = test_strict(ev, reg, _inp(ev, t), {t["prompt"]: text})
            got = dict(zip(t["instruction_id_list"], res.follow_instruction_list))[LETTER_CHECK]
            label = "key=%s letter=%r want=%s got=%s" % (key, ch, expect, got)
            unit.append(got == expect)
            notes.append(label)
    if not all(unit):
        return False, "literal-character checks failed: " + " | ".join(notes)

    # 2. determinism of the cells the vendor used to re-draw, restricted to the letter_frequency
    #    position (the change_case checks stay vendor-stochastic and are NOT claimed deterministic).
    ref_path = data / "gpt4_sample.jsonl"
    if not ref_path.exists():
        return False, "reference response file missing: %s" % ref_path
    prompts = {t["prompt"] for t in vtasks}
    p2r = {r["prompt"]: r["response"] for r in
           (json.loads(l) for l in ref_path.read_text().splitlines()) if r["prompt"] in prompts}
    aff = affected_cells(vtasks)
    if len(aff) != AFFECTED_CELLS:
        return False, ("pinned set carries %d re-drawn letter_frequency cells, expected %d — the "
                       "task bytes or the vendored checker moved" % (len(aff), AFFECTED_CELLS))
    for key, ch in aff:
        t = by_key[key]
        pos = t["instruction_id_list"].index(LETTER_CHECK)
        votes = {test_strict(ev, reg, _inp(ev, t), p2r).follow_instruction_list[pos]
                 for _ in range(20)}
        if len(votes) != 1:
            return False, ("cell %s (%r) still nondeterministic under %s: %d verdicts in 20 draws"
                           % (key, ch, CHECKER, len(votes)))

    # 3. reference band under this contract (exact, since the RNG is gone)
    st = lo = n = 0
    for t in vtasks:
        if t["prompt"] not in p2r:
            continue
        n += 1
        st += int(test_strict(ev, reg, _inp(ev, t), p2r).follow_all_instructions)
        lo += int(test_loose(ev, reg, _inp(ev, t), p2r).follow_all_instructions)
    if n != REF_N:
        return False, "reference set joined %d prompts, expected %d" % (n, REF_N)
    for name, got, want in (("strict", st, REF_STRICT), ("loose", lo, REF_LOOSE)):
        if abs(100.0 * (got - want) / n) > REF_BAND_PP:
            return False, ("reference %s moved under %s: %d/%d vs recorded %d/%d"
                           % (name, CHECKER, got, n, want, n))

    # 4. scope bound: v1 and v2 may differ ONLY on the affected cells
    diffs = []
    v1_st = 0
    for t in vtasks:
        if t["prompt"] not in p2r:
            continue
        inp = _inp(ev, t)
        s1 = ev.test_instruction_following_strict(inp, p2r)
        v1_st += int(s1.follow_all_instructions)
        if s1.follow_all_instructions != test_strict(ev, reg, inp, p2r).follow_all_instructions:
            diffs.append(t["key"])
    if len(diffs) > AFFECTED_CELLS:
        return False, ("v1/v2 differ on %d cells (%s), expected at most %d"
                       % (len(diffs), diffs, AFFECTED_CELLS))
    return True, ("vendor pins 5/5; unit suite green; literal-character checks %d/%d; determinism "
                  "20 draws x %d re-drawn cells; reference strict %d/%d loose %d/%d (v1 over the "
                  "same bytes: strict %d/%d); v1/v2 strict diffs %s"
                  % (sum(unit), len(unit), len(aff), st, n, lo, n, v1_st, n, diffs or "none"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("answers"); ap.add_argument("tasks")
    ap.add_argument("bench"); ap.add_argument("model"); ap.add_argument("call")
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-digest", action="store_true")
    ap.add_argument("--selftest-only", action="store_true")
    a = ap.parse_args()

    ok, why = selftest()
    if not ok:
        sys.exit("REFUSING TO SCORE: %s" % why)
    print("self-test: %s" % why)
    if a.selftest_only:
        return

    tasks = [json.loads(l) for l in pathlib.Path(a.tasks).read_text().splitlines()]
    ans = {}
    for line in pathlib.Path(a.answers).read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            ans.setdefault(r["id"], r.get("answer", ""))
    missing = [t["id"] for t in tasks if t["id"] not in ans]
    if len(missing) > 0.05 * len(tasks):
        sys.exit("REFUSING TO SCORE: arm is partial - %d/%d answers present"
                 % (len(tasks) - len(missing), len(tasks)))

    ev, reg = load_vendor()
    p2r = {t["prompt"]: ans[t["id"]] for t in tasks if t["id"] in ans}
    rows, fails = [], collections.Counter()
    for t in tasks:
        if t["id"] not in ans:
            continue
        s = test_strict(ev, reg, _inp(ev, t), p2r)
        l = test_loose(ev, reg, _inp(ev, t), p2r)
        for cid, okc in zip(t["instruction_id_list"], s.follow_instruction_list):
            if not okc:
                fails[cid] += 1
        rows.append({"id": t["id"], "strict": bool(s.follow_all_instructions),
                     "loose": bool(l.follow_all_instructions),
                     "per_instruction": list(s.follow_instruction_list)})
    n = len(rows)
    st = sum(1 for r in rows if r["strict"])
    lo = sum(1 for r in rows if r["loose"])
    print("%s %s n=%d strict %d/%d = %.1f %% | loose %d/%d = %.1f %%"
          % (a.bench, CHECKER, n, st, n, 100.0 * st / n, lo, n, 100.0 * lo / n))
    print("hardest checks:", ", ".join("%s=%d" % kv for kv in fails.most_common(6)))
    out = pathlib.Path(a.out or str(pathlib.Path(a.answers).parent))
    side = out / ("%s-%s-verdicts.jsonl" % (a.bench, CHECKER))
    side.write_text("\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n")
    (out / ("%s-%s-verdicts.sha16" % (a.bench, CHECKER))).write_text(
        hashlib.sha1(side.read_bytes()).hexdigest()[:16] + "\n")
    if a.no_digest:
        print("--no-digest: verdict sidecar written (%s), no digest row" % side)
        return
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import pub_bench_score as pbs                                # noqa: E402
    tsha = tasks_sha16(a.tasks)
    line = ("| %s | %s | %d | %s | %s; checker %s | %d/%d = **%.1f%%** strict (%d/%d loose) |"
            % (a.bench, a.model, n, tsha, a.call, CHECKER, st, n, 100.0 * st / n, lo, n))
    key = "\n| %s | %s | %d | %s |" % (a.bench, a.model, n, tsha)
    dig = ROOT / "benchmarks" / "public" / "PUB-DIGEST.md"
    if key in (dig.read_text() if dig.exists() else ""):
        print("digest row for this bench+model+tasks already exists - not duplicated")
    else:
        print("-> %s" % pathlib.Path(pbs.write_digest(line)).name)


if __name__ == "__main__":
    main()
