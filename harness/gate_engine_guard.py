#!/usr/bin/env python3
"""Engine-stall guard: keep serve failures out of quality numbers.

Why this exists. On 2026-11-03 the full `0.0.2.1 -> 0.0.2.2` pair on P2005 looked
like a contour regression of -0.109 overall. The ledger said otherwise: on 140 of
645 rows of the first side and 157 of 298 rows of the second side the prompt token
count was 0, the wall time was exactly 20 s and no completion came back at all.
The serve had been squeezed by parked conversation snapshots (up to 2.6 GiB each,
`K/V trimmed to 8192 cells`), so it accepted the connection, held it, and returned
an empty stream with no usage block. Those rows measured the box, not the contour,
and they were scored as zero-quality answers. On the 82 pairs where neither side
stalled, the two contours were 0.9961 against 0.9820.

The rule this module implements:

* an answer-less response with no HTTP error and no usage block is a **stall**, not
  a wrong answer;
* one same-seed retry is allowed, because the retry draws the identical sample and
  only skips a transient stall — it does not change the measured distribution;
* a row that still stalls is marked `engine_stalled` and must be excluded from
  quality means (it belongs to the capacity counter instead);
* a run whose stall rate over a rolling window crosses the threshold stops, so an
  unfit serve cannot burn hours of gate time.

Measurement validity only: nothing here changes what the model is asked or given,
so it moves the tooling revision, never the contour behavior.
"""
from collections import deque

STALL_S = 18.0
STALL_RATE = 0.25
STALL_WINDOW = 20


def is_stalled(text, err, ptok, ctok):
    """True when the request produced nothing and the engine never reported usage."""
    if (text or "").strip() or err:
        return False
    return not ptok and not ctok


class StallTracker:
    """Rolling stall rate; decides when a serve is unfit for measurement."""

    def __init__(self, rate=STALL_RATE, window=STALL_WINDOW):
        self.rate = rate
        self.win = deque(maxlen=max(1, int(window)))

    def add(self, stalled):
        self.win.append(1 if stalled else 0)

    def fraction(self):
        return (sum(self.win) / len(self.win)) if self.win else 0.0

    def unfit(self):
        """Armed only once the window is full, so a startup hiccup cannot abort a run."""
        return len(self.win) == self.win.maxlen and self.fraction() > self.rate

    def verdict(self):
        return "stalled %d/%d (%.0f%%), threshold %.0f%%" % (
            sum(self.win), len(self.win), 100.0 * self.fraction(), 100.0 * self.rate)


def run_record(box, model, api, contour_summary, contour_behavior, health=None,
               git_sha="", plan_tasks=None, notes=None):
    """A machine-readable record of the conditions a run was measured under.

    Without it, a bad pair cannot be diagnosed later: the artifacts said the model
    scored 0 while the serve was silently refusing requests.
    """
    rec = {"box": box, "model": model, "api_host": _host_of(api),
           "contour_version": (contour_summary or {}).get("canonical_version"),
           "contour_behavior": contour_behavior,
           "contour_changed_at_this_release": (contour_summary or {}).get(
               "contour_changed_at_this_release"),
           "git_sha": git_sha, "plan_tasks": plan_tasks, "serve_health": health,
           "stall_policy": {"retry": 1, "rate": STALL_RATE, "window": STALL_WINDOW,
                            "stall_seconds": STALL_S}}
    if notes:
        rec["notes"] = notes
    return rec


def health_url(api):
    """`http://host:port/v1/chat/completions` -> `http://host:port/health`."""
    h = _host_of(api)
    return h + "/health" if h else ""


def _host_of(api):
    if not api or "://" not in api:
        return ""
    rest = api.split("://", 1)[1]
    host = rest.split("/", 1)[0]
    return "http://" + host if host else ""
