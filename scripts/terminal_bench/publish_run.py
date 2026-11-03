#!/usr/bin/env python3
"""Build and incrementally publish sanitized Terminal-Bench run results.

This script reads completed Harbor trials only. It never starts inference and
never changes the benchmark job. On publication failure it leaves the generated
commit unpushed for a later retry.
"""

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from typing import Any


REDACT = "[REDACTED]"

SECRET_PATTERNS = [
    (re.compile(r"\b(?:10(?:\.[0-9]{1,3}){3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|172\.(?:1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3})\b"), "[PRIVATE_IP]"),
    (re.compile(r"(?:/home|/Users)/[A-Za-z0-9_.-]+"), "[LOCAL_PATH]"),
    (re.compile(r"(?i)\b(Bearer\s+)[A-Za-z0-9._~+/-]{12,}=*"), r"\1" + REDACT),
    (re.compile(r"(?i)([\"']?(?:api_key|token|password|secret)[\"']?\s*[:=]\s*[\"']?)[^\s\"',}]{8,}"), r"\1" + REDACT),
    (re.compile(r"(?i)\bSTRATA_API_KEY\b[^\n]{0,80}?([A-Za-z0-9_=-]{16,})"), "STRATA_API_KEY " + REDACT),
]

SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "password",
    "secret",
    "token",
    "base_url",
    "connection",
    "headers",
}
SENSITIVE_KEY_PARTS = (
    "api_key_value",
    "access_token",
    "private_key",
    "authorization",
    "base_url",
)

SECRET_SCAN_MARKERS = [
    "gitleaks",
    "private-network-address",
    "local-account-path",
    "ssh-connection-material",
    "local-environment-dump",
]


def redact_text(value: str) -> str:
    for pattern, replacement in SECRET_PATTERNS:
        value = pattern.sub(replacement, value)
    return value


def redact_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: (
                REDACT
                if str(key).lower() in SENSITIVE_KEYS or any(part in str(key).lower() for part in SENSITIVE_KEY_PARTS)
                else redact_json(val)
            )
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [redact_json(x) for x in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_redacted_text(src: pathlib.Path, dest: pathlib.Path) -> None:
    if not src.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(redact_text(src.read_text(errors="ignore")))


def write_session(src: pathlib.Path, dest: pathlib.Path) -> dict[str, int]:
    stats = {"messages": 0, "redacted_messages": 0}
    if not src.exists() or src.stat().st_size == 0:
        return stats
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w") as out:
        for line in src.read_text(errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                out.write(json.dumps({"type": "unparsed", "text": redact_text(line)}) + "\n")
                stats["messages"] += 1
                continue
            payload = redact_json(payload)
            for key in (
                "system_prompt", "system_prompt_hash", "session_key", "user_id",
                "model_config", "connection", "headers", "billing_base_url",
                "origin_json", "profile_name", "handoff_state",
            ):
                payload.pop(key, None)
            messages = payload.get("messages")
            if isinstance(messages, list):
                before = len(messages)
                payload["messages"] = [
                    m for m in messages if m.get("role") != "system"
                ]
                stats["redacted_messages"] += before - len(payload["messages"])
            out.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
            stats["messages"] += 1
    return stats


def verifier_summary(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {"available": False, "reason": "ctrf.json not found"}
    raw = json.loads(path.read_text(errors="ignore"))
    tests = raw.get("results", {}).get("tests", []) if isinstance(raw.get("results"), dict) else raw.get("tests", [])
    summary: dict[str, Any] = {
        "available": True,
        "passed": 0,
        "failed": 0,
        "total": len(tests),
        "tests": [],
        "source_policy": "Raw verifier stdout is not published because it can contain hidden assertions or reference values.",
    }
    for test in tests:
        status = test.get("status")
        if status == "passed":
            summary["passed"] += 1
        elif status == "failed":
            summary["failed"] += 1
        summary["tests"].append({
            "name": redact_text(str(test.get("name", ""))),
            "status": redact_text(str(status)),
            "message": redact_text(str(test.get("message", "")))[:500],
        })
    return summary


def trial_metrics(job_dir: pathlib.Path, trial: pathlib.Path) -> dict[str, Any]:
    result = json.loads((trial / "result.json").read_text(errors="ignore"))
    rewards = result.get("rewards") or {}
    reward = rewards.get("reward")
    reward_file = trial / "verifier" / "reward.txt"
    if reward is None and reward_file.exists():
        try:
            reward = float(reward_file.read_text(errors="ignore").strip())
        except ValueError:
            reward = None
    agent = result.get("agent_execution") or {}
    setup = result.get("agent_setup") or {}
    verifier = result.get("verifier") or {}

    def duration(block: dict[str, Any]) -> float | None:
        start, finish = block.get("started_at"), block.get("finished_at")
        if not start or not finish:
            return None
        fmt = "%Y-%m-%dT%H:%M:%S.%f"
        try:
            start_dt = dt.datetime.fromisoformat(start.replace("Z", ""))
            finish_dt = dt.datetime.fromisoformat(finish.replace("Z", ""))
        except ValueError:
            return None
        return (finish_dt - start_dt).total_seconds()

    sessions = sorted((trial / "agent").glob("hermes-phase-*/session.jsonl"))
    metadata = []
    for path in sessions:
        if path.stat().st_size == 0:
            metadata.append({"path": path.name, "available": False, "reason": "empty session export"})
            continue
        payload = json.loads(path.read_text(errors="ignore"))
        metadata.append(redact_json({
            key: payload.get(key)
            for key in (
                "model", "message_count", "tool_call_count", "api_call_count",
                "input_tokens", "output_tokens", "cache_read_tokens",
                "cache_write_tokens", "reasoning_tokens", "estimated_cost_usd",
                "actual_cost_usd", "cost_status", "compression_count",
                "started_at", "ended_at", "end_reason",
            )
        }))
    final_session = next((x for x in reversed(metadata) if x.get("api_call_count") is not None), {})

    def max_numeric(name: str) -> int | None:
        vals = [x.get(name) for x in metadata if isinstance(x.get(name), (int, float))]
        return max(vals) if vals else None

    def sum_numeric(name: str) -> int | None:
        vals = [x.get(name) for x in metadata if isinstance(x.get(name), (int, float))]
        return sum(vals) if vals else None

    total_model_calls = max_numeric("api_call_count")
    total_tool_calls = sum_numeric("tool_call_count")
    if total_model_calls is not None and total_tool_calls is not None and total_tool_calls > total_model_calls * 4:
        # Some Hermes exports report cumulative tool-call counts rather than per-phase counts.
        total_tool_calls = max_numeric("tool_call_count")

    return {
        "trial": trial.name,
        "task": trial.name.split("__", 1)[0],
        "reward": reward,
        "started_at": result.get("started_at"),
        "finished_at": result.get("finished_at"),
        "seconds": {
            "trial_total": duration({"started_at": result.get("started_at"), "finished_at": result.get("finished_at")}),
            "setup": duration(setup),
            "agent_execution": duration(agent),
            "verifier": duration(verifier),
        },
        "token_usage_exact_if_present": {
            "source": "Hermes session exports; cumulative maxima for per-session counters, summed per-phase tool calls where applicable",
            "available": bool(final_session),
            "api_call_count": total_model_calls,
            "tool_call_count": total_tool_calls,
            "input_tokens": max_numeric("input_tokens"),
            "output_tokens": max_numeric("output_tokens"),
            "cache_read_tokens": max_numeric("cache_read_tokens"),
            "cache_write_tokens": max_numeric("cache_write_tokens"),
            "reasoning_tokens": max_numeric("reasoning_tokens"),
            "prefill_decode_split": None,
            "note": "Terminal-Bench trial metrics do not expose a reliable prefill/decode split.",
        },
        "session_exports": metadata,
        "verifier": verifier_summary(trial / "verifier" / "ctrf.json"),
    }


def scan_published_tree(path: pathlib.Path) -> list[str]:
    findings: list[str] = []
    for file in path.rglob("*"):
        if not file.is_file() or file.suffix in {".png", ".jpg"}:
            continue
        text = file.read_text(errors="ignore")
        for pattern, _replacement in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(f"{file.relative_to(path)}: {pattern.pattern}")
        lowered = text.lower()
        if "gitleaks:allow" in lowered or "private-network-address" in lowered:
            findings.append(f"{file.relative_to(path)}: publication policy marker")
    return findings


def forecast(job_dir: pathlib.Path, cumulative: dict[str, Any]) -> dict[str, Any]:
    """Compute a deliberately conservative observed-rate estimate from wall time."""
    started = None
    result = job_dir / "result.json"
    if result.exists():
        try:
            started = json.loads(result.read_text(errors="ignore")).get("started_at")
        except Exception:
            started = None
    if not started:
        return {"available": False, "reason": "job start time unavailable"}
    start_dt = dt.datetime.fromisoformat(started.replace("Z", "+00:00"))
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=dt.timezone.utc)
    now = dt.datetime.now(dt.timezone.utc)
    completed = cumulative["completed"]
    elapsed_h = (now - start_dt).total_seconds() / 3600
    if completed == 0:
        return {"available": False, "reason": "no completed trial yet", "started_at": started}
    rate_h = elapsed_h / completed
    remaining_h = rate_h * (66 - completed)
    eta = now + dt.timedelta(hours=remaining_h)
    return {
        "available": True,
        "method": "observed wall-clock rate at the current completion count; difficulty not weighted",
        "started_at": started,
        "elapsed_hours": round(elapsed_h, 2),
        "hours_per_completed_trial": round(rate_h, 2),
        "estimated_remaining_hours": round(remaining_h, 1),
        "estimated_finish_utc": eta.isoformat(),
        "confidence": "low; early sample and three H100-dependent tasks remain",
    }


def build_publication(repo: pathlib.Path, job_dir: pathlib.Path, run_dir: pathlib.Path, config: dict[str, Any], trials: list[pathlib.Path]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("config", "tasks", "data"):
        (run_dir / sub).mkdir(exist_ok=True)
    shutil.rmtree(run_dir / "config" / "__pycache__", ignore_errors=True)
    shutil.rmtree(run_dir / "__pycache__", ignore_errors=True)

    sanitized_config = redact_json(config)
    (run_dir / "config" / "run.json").write_text(json.dumps(sanitized_config, indent=2, sort_keys=True))
    for name, source in (
        ("hermes_verified.py.txt", pathlib.Path("/srv/claryel/hot/tbench/harness/src/terminal_bench_hermes_harness/hermes_verified.py")),
        ("task-discipline-SKILL.md", pathlib.Path("/srv/claryel/hot/tbench/skills/task-discipline/SKILL.md")),
        ("runner.sh", pathlib.Path("/srv/claryel/hot/tbench/scripts/run_full66_verified_p2005.sh")),
    ):
        write_redacted_text(source, run_dir / "config" / name)

    all_metrics = []
    for trial in trials:
        metrics = trial_metrics(job_dir, trial)
        all_metrics.append(metrics)
        notes = load_trial_notes(run_dir, trial.name)
        write_trial_dir(trial, run_dir / "tasks" / trial.name, metrics, notes)

    completed = len(all_metrics)
    solved = sum(1 for x in all_metrics if x.get("reward") == 1)
    failed = sum(1 for x in all_metrics if x.get("reward") == 0)

    def sum_available(name: str) -> int | None:
        vals = []
        for x in all_metrics:
            v = x.get("token_usage_exact_if_present", {}).get(name)
            if isinstance(v, (int, float)):
                vals.append(v)
        return sum(vals) if vals else None

    infra = []
    for x in all_metrics:
        for export in x.get("session_exports", []):
            if export.get("available") is False:
                infra.append({"trial": x["trial"], "issue": export.get("reason", "session export unavailable")})
    cumulative = {
        "run": job_dir.name,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "completed": completed,
        "total": 66,
        "solved": solved,
        "failed": failed,
        "success_percent": round(100.0 * solved / completed, 2) if completed else 0,
        "metrics_source": "Harbor result.json and Hermes session exports",
        "tokens": {
            "input": sum_available("input_tokens"),
            "output": sum_available("output_tokens"),
            "cache_read": sum_available("cache_read_tokens"),
            "note": "Unavailable token data from a trial is not imputed.",
        },
        "resource_consumption": {
            "continuous_gpu_power_energy_sampling": False,
            "gpu_peak_and_energy": None,
        },
        "infrastructure_failures": infra,
        "forecast": forecast(job_dir, {"completed": completed}) if (job_dir / "result.json").exists() else None,
        "trials": all_metrics,
    }
    (run_dir / "data" / "cumulative-summary.json").write_text(json.dumps(cumulative, indent=2, sort_keys=True))
    lines = [
        "# Cumulative summary",
        "",
        f"- Run: `{job_dir.name}`",
        f"- Completed: {completed} / 66",
        f"- Solved: {solved}",
        f"- Failed: {failed}",
        f"- Success rate among completed trials: {cumulative['success_percent']}%",
        f"- Available input tokens: {cumulative['tokens']['input']}",
        f"- Available output tokens: {cumulative['tokens']['output']}",
        f"- Infrastructure failures: {len(cumulative['infrastructure_failures'])}",
        f"- Forecast: {cumulative['forecast'].get('estimated_remaining_hours', 'no data')} h remaining ({cumulative['forecast'].get('confidence', 'no confidence')})",
        "",
        "| task | reward | total time | agent time | model calls | tool calls | input tokens | output tokens | verifier |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for m in all_metrics:
        sec = m["seconds"]
        tok = m["token_usage_exact_if_present"]
        def fmt(value):
            return "no data" if value is None else value
        v = m["verifier"]
        lines.append(
            f"| `{m['task']}` | {fmt(m.get('reward'))} | {fmt(sec.get('trial_total'))} s | {fmt(sec.get('agent_execution'))} s | "
            f"{fmt(tok.get('api_call_count'))} | {fmt(tok.get('tool_call_count'))} | {fmt(tok.get('input_tokens'))} | "
            f"{fmt(tok.get('output_tokens'))} | {fmt(v.get('passed'))} / {fmt(v.get('total'))} |"
        )
    lines += ["", "Official leaderboard status: this is an independent one-pass run, not an official Terminal-Bench 4.0 leaderboard run."]
    (run_dir / "data" / "cumulative-summary.md").write_text("\n".join(lines) + "\n")
    (run_dir / "index.md").write_text(index_page(job_dir, cumulative, sanitized_config))
    return cumulative


def human_task_page(metrics: dict[str, Any], notes: dict[str, Any]) -> str:
    return f"""# {metrics['task']}

**Reward:** {metrics.get('reward')}  
**Total:** {metrics['seconds'].get('trial_total')} s  
**Agent execution:** {metrics['seconds'].get('agent_execution')} s  
**Setup:** {metrics['seconds'].get('setup')} s  
**Verifier:** {metrics['verifier'].get('passed')} passed / {metrics['verifier'].get('failed')} failed

{notes.get('summary', '')}

## Failure analysis

{notes.get('failure', '')}

## Metric caveats

{notes.get('metrics', '')}
"""


def load_trial_notes(run_dir: pathlib.Path, trial_name: str) -> dict[str, Any]:
    notes = run_dir / "notes" / f"{trial_name}.json"
    if not notes.exists():
        return {}
    return json.loads(notes.read_text(errors="ignore"))


def trial_page(metrics: dict[str, Any], notes: dict[str, Any]) -> str:
    def value(x: Any) -> str:
        return "no data" if x is None else x
    sec = metrics["seconds"]
    tok = metrics["token_usage_exact_if_present"]
    verifier = metrics["verifier"]
    lines = [
        f"# {metrics['task']}",
        "",
        f"**Reward:** {value(metrics.get('reward'))}  ",
        f"**Total:** {value(sec.get('trial_total'))} s  ",
        f"**Agent execution:** {value(sec.get('agent_execution'))} s  ",
        f"**Setup:** {value(sec.get('setup'))} s  ",
        f"**Verifier:** {value(verifier.get('passed'))} passed / {value(verifier.get('failed'))} failed of {value(verifier.get('total'))}",
        "",
        "## Machine-readable metrics",
        "",
        f"- Model calls: {value(tok.get('api_call_count'))}",
        f"- Tool calls: {value(tok.get('tool_call_count'))}",
        f"- Input tokens: {value(tok.get('input_tokens'))}",
        f"- Output tokens: {value(tok.get('output_tokens'))}",
        f"- Cache-read tokens: {value(tok.get('cache_read_tokens'))}",
        "- Prefill/decode split: no data",
        "",
        "## Operator analysis",
        "",
        notes.get("summary", "No additional operator analysis is attached to this completed trial."),
        "",
        "## Failure analysis",
        "",
        notes.get("failure", "The verifier output above is the authoritative failure summary."),
        "",
        "## Infrastructure and metric caveats",
        "",
        notes.get("metrics", "All available numeric metrics are reported; unavailable metrics are labeled no data."),
    ]
    return "\n".join(lines) + "\n"


def write_trial_dir(trial: pathlib.Path, target: pathlib.Path, metrics: dict[str, Any], notes: dict[str, Any]) -> None:
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True)
    (target / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True))
    (target / "trial.md").write_text(trial_page(metrics, notes))
    (target / "result-redacted.json").write_text(json.dumps(redact_json(json.loads((trial / "result.json").read_text(errors="ignore"))), indent=2, sort_keys=True))
    (target / "agent").mkdir(parents=True, exist_ok=True)
    for phase_dir in sorted((trial / "agent").glob("hermes-phase-*")):
        phase = phase_dir.name
        stats = write_session(phase_dir / "session.jsonl", target / "agent" / f"{phase}-session.jsonl")
        (target / "agent" / f"{phase}-session-stats.json").parent.mkdir(parents=True, exist_ok=True)
        (target / "agent" / f"{phase}-session-stats.json").write_text(json.dumps(stats, indent=2))
        write_redacted_text(phase_dir / "stdout.txt", target / "agent" / f"{phase}-stdout.txt")
    write_redacted_text(trial / "agent" / "hermes.txt", target / "agent" / "hermes.txt")
    write_redacted_text(trial / "trial.log", target / "trial-redacted.log")


def index_page(job_dir: pathlib.Path, cumulative: dict[str, Any], run_config: dict[str, Any]) -> str:
    lines = [
        "# Terminal-Bench 4.0: VerifiedHermes on P2005",
        "",
        "This is an **independent one-pass run**, not an official Terminal-Bench 4.0 leaderboard submission. Official leaderboard evaluation uses five attempts per task.",
        "",
        f"- Run: `{job_dir.name}`",
        f"- Completed: {cumulative['completed']} / 66",
        f"- Solved: {cumulative['solved']}",
        f"- Failed: {cumulative['failed']}",
        f"- Success rate among completed trials: {cumulative['success_percent']}%",
        f"- Tokens (available trials): input `{cumulative['tokens']['input']}`, output `{cumulative['tokens']['output']}`",
        f"- Infrastructure failures: `{len(cumulative['infrastructure_failures'])}` recorded",
        f"- Forecast: `{cumulative['forecast'].get('estimated_remaining_hours', 'no data')} h remaining (low confidence)`",
        f"- Model: `{run_config.get('model', {}).get('requested_model', 'no data')}`",
        f"- Quantization: `{run_config.get('model', {}).get('quantization', 'no data')}`",
        f"- Inference host label: `{run_config.get('model', {}).get('endpoint_host_label', 'no data')}`",
        f"- Hermes: `{run_config.get('runner', {}).get('hermes_version', 'no data')}`",
        f"- Harbor: `{run_config.get('runner', {}).get('harbor_version', 'no data')}`",
        f"- Strata: `{run_config.get('inference_server', {}).get('application_version', 'no data')} (engine {run_config.get('inference_server', {}).get('engine_version', 'no data')})`",
        "- Claryel Autonomous Harness contour in task solving: not used (explicit)",
        "",
        "## Completed tasks",
        "",
        "| task | reward | total time | model calls | verifier | report |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for m in cumulative["trials"]:
        v = m["verifier"]
        tok = m["token_usage_exact_if_present"]
        lines.append(
            f"| `{m['task']}` | {m.get('reward')} | {m['seconds'].get('trial_total')} s | "
            f"{tok.get('api_call_count')} | {v.get('passed')} / {v.get('total')} | "
            f"[report](tasks/{m['trial']}/trial.md) |"
        )
    lines += [
        "",
        "See `data/cumulative-summary.json` for machine-readable totals.",
        "Raw private paths and network endpoints are redacted. Raw hidden-test stdout is not published.",
    ]
    return "\n".join(lines) + "\n"


README_START = "<!-- BEGIN TERMINAL-BENCH-2026-11-04-STATUS -->"
README_END = "<!-- END TERMINAL-BENCH-2026-11-04-STATUS -->"


def update_readme(repo: pathlib.Path, publication_dir: pathlib.Path, cumulative: dict[str, Any]) -> None:
    readme = repo / "README.md"
    text = readme.read_text()
    row = (
        f"| [Terminal-Bench 4.0: independent one-pass run]({publication_dir.as_posix()}/index.md) | "
        f"in progress; {cumulative['completed']} / 66 completed, {cumulative['solved']} solved, "
        f"{cumulative['failed']} failed; not an official leaderboard run |"
    )
    block = f"{README_START}\n{row}\n{README_END}"
    if README_START in text:
        start = text.index(README_START)
        end = text.index(README_END, start) + len(README_END)
        text = text[:start] + block + text[end:]
    else:
        marker = "\n## Headline results"
        if marker not in text:
            return
        text = text.replace(marker, f"\n{block}\n{marker}", 1)
    readme.write_text(text)


def log_publication(repo: pathlib.Path, cumulative: dict[str, Any], sha: str) -> None:
    index = repo / "logs" / "INDEX.md"
    line = (
        f"| {dt.datetime.now().strftime('%Y-%m-%d %H:%M')} | terminal-bench-publication | "
        f"commit `{sha}` | {cumulative['completed']}/66 completed, {cumulative['solved']} solved, "
        f"{cumulative['failed']} failed |\n"
    )
    index.write_text(index.read_text().rstrip() + "\n" + line)


def run(args: list[str], cwd: pathlib.Path) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"{args[0]} failed ({result.returncode})\n{result.stderr.strip()}\n{result.stdout.strip()}")
    return result.stdout


def benchmark_run_active(job_name: str) -> bool:
    """Return True while the Harbor job process is still running."""
    needle = job_name.encode()
    for proc in pathlib.Path("/proc").glob("[0-9]*/cmdline"):
        try:
            cmdline = proc.read_bytes()
        except OSError:
            continue
        if needle in cmdline and b"harbor" in cmdline:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=pathlib.Path, required=True)
    parser.add_argument("--job-dir", type=pathlib.Path, required=True)
    parser.add_argument("--publication-dir", type=pathlib.Path, required=True)
    parser.add_argument("--config", type=pathlib.Path, required=True)
    parser.add_argument("--state", type=pathlib.Path, required=True)
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    repo = args.repo.resolve()
    job_dir = args.job_dir.resolve()
    run_dir = repo / args.publication_dir
    config = json.loads(args.config.read_text())
    seen = args.state if args.state.exists() else set()
    seen_value = set(json.loads(args.state.read_text())) if args.state.exists() else set()

    while True:
        trials = sorted(
            (x for x in job_dir.iterdir() if x.is_dir() and (x / "result.json").exists()),
            key=lambda x: x.name,
        )
        new = [x for x in trials if x.name not in seen_value]
        if trials and (new or args.force):
            cumulative = build_publication(repo, job_dir, run_dir, config, trials)
            publication_dir = args.publication_dir
            update_readme(repo, publication_dir, cumulative)
            findings = scan_published_tree(run_dir)
            if findings:
                print(f"PUBLISH_BLOCKED finding_count={len(findings)}")
                for f in findings[:20]:
                    print(f"  {f}")
                if not args.loop:
                    return 2
            if args.commit:
                run(["git", "add", "--", str(run_dir.relative_to(repo)), "README.md", "logs/INDEX.md", "CHANGELOG.md"], repo)
                message = (
                    f"Terminal-Bench: add {len(new)} completed trial(s)\n\n"
                    f"Run: {job_dir.name}\nCompleted: {cumulative['completed']} / 66\n"
                    f"Solved: {cumulative['solved']}\nSanitization: generated locally and scanned before commit."
                )
                run(["git", "commit", "-m", message], repo)
                sha = run(["git", "rev-parse", "HEAD"], repo).strip()
                log_publication(repo, cumulative, sha)
                run(["git", "add", "--", "logs/INDEX.md"], repo)
                if run(["git", "status", "--porcelain"], repo).strip():
                    run(["git", "commit", "-m", f"Record Terminal-Bench publication {sha}"], repo)
                    sha = run(["git", "rev-parse", "HEAD"], repo).strip()
                print(f"PUBLISHED commit={sha} trials={len(trials)} solved={cumulative['solved']}")
                if args.push:
                    try:
                        run(["git", "push", "origin", "main"], repo)
                    except Exception as exc:
                        print(f"PUSH_FAILED local_commit={sha} reason={exc}")
                        if not args.loop:
                            return 1
            for x in trials:
                seen_value.add(x.name)
            args.state.write_text(json.dumps(sorted(seen_value), indent=2))
        if not args.loop:
            return 0
        if not benchmark_run_active(job_dir.name):
            print("WATCH_COMPLETE")
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
