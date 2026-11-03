#!/usr/bin/env python3
"""Summarize Harbor/Terminal-Bench trial results into one comparison row."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


def parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return dt.datetime.fromisoformat(value)


def reward(result: dict) -> float:
    rewards = (result.get("verifier_result") or {}).get("rewards") or {}
    if "reward" in rewards:
        return float(rewards["reward"])
    return sum(float(v) for v in rewards.values())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs_dir", type=Path)
    ap.add_argument("--arm", default="")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    rows = []
    for path in sorted(args.jobs_dir.rglob("result.json")):
        result = json.loads(path.read_text())
        if path.parent == args.jobs_dir:
            continue
        start = parse_time(result.get("started_at"))
        end = parse_time(result.get("finished_at"))
        agent_execution = result.get("agent_execution") or {}
        agent_start = parse_time(agent_execution.get("started_at"))
        agent_end = parse_time(agent_execution.get("finished_at"))
        r = reward(result)
        rows.append({
            "path": str(path),
            "task": result.get("task_name"),
            "trial": result.get("trial_name"),
            "agent": (result.get("agent_info") or {}).get("name"),
            "model": ((result.get("agent_info") or {}).get("model_info") or {}),
            "reward": r,
            "solved": r > 0,
            "exception": result.get("exception_info"),
            "trial_seconds": round((end - start).total_seconds(), 1) if start and end else None,
            "agent_execution_seconds": round((agent_end - agent_start).total_seconds(), 1) if agent_start and agent_end else None,
            "tokens": result.get("agent_result"),
        })

    solved = sum(bool(r["solved"]) for r in rows)
    exceptions = sum(bool(r["exception"]) for r in rows)
    durations = [r["trial_seconds"] for r in rows if r["trial_seconds"] is not None]
    agent_durations = [
        r["agent_execution_seconds"] for r in rows
        if r["agent_execution_seconds"] is not None
    ]
    out = {
        "arm": args.arm or "unknown",
        "jobs_dir": str(args.jobs_dir),
        "trials": len(rows),
        "solved": solved,
        "solve_rate_pct": round(100.0 * solved / len(rows), 2) if rows else 0.0,
        "exceptions": exceptions,
        "mean_trial_seconds": round(sum(durations) / len(durations), 1) if durations else None,
        "mean_agent_execution_seconds": round(sum(agent_durations) / len(agent_durations), 1) if agent_durations else None,
        "rows": rows,
    }
    text = json.dumps(out, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
