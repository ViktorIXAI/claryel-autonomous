#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal sandbox runner for category-E model-produced code (issue #15 P0).

Goals (before any real E battery on the host):
  - no network (prefer docker --network=none; else unshare -n/-rn; else refuse net claim)
  - no host secrets in env (PATH/LANG/HOME=tmp only; never mount ~/.ssh, secrets, .env)
  - host FS read-only where needed; writes only in a temp cwd
  - CPU / memory / wall-clock limits
  - kill the whole process tree (new session + killpg, or docker kill)

Self-test (no model, no real E bank):
  python3 harness/e_sandbox.py --self-test

Do NOT wire this into gate_run / real E battery in this change set.
"""
from __future__ import annotations

import argparse
import os
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence

DEFAULT_CPU_SEC = 4
DEFAULT_AS_BYTES = 512 * 1024 * 1024
DEFAULT_WALL_SEC = 8
# Pinned by digest (issue #15 GPT-6 blocker 2): mutable tags are not acceptable
# for untrusted-code execution. Update deliberately, never implicitly.
DEFAULT_DOCKER_IMAGE = os.environ.get(
    "STRATA_E_SANDBOX_IMAGE",
    "python@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159",
)

_FORBIDDEN_MOUNT_SUFFIXES = (
    "/.ssh",
    "/.gnupg",
    "/production.env",
    "/.env",
    "/secrets",
    "/.aws",
    "/.config/gcloud",
)


@dataclass
class SandboxResult:
    ok: bool
    backend: str
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    wall_sec: float
    detail: str = ""


def _which(name: str) -> Optional[str]:
    return shutil.which(name)


def detect_backends() -> dict:
    """Probe host capabilities. unshare may exist but be AppArmor-blocked."""
    info = {
        "bwrap": _which("bwrap"),
        "firejail": _which("firejail"),
        "unshare": _which("unshare"),
        "docker": _which("docker"),
        "unshare_net_ok": False,
        "docker_ok": False,
    }
    if info["unshare"]:
        for flags in (["-rn"], ["-n"]):
            try:
                r = subprocess.run(
                    [info["unshare"], *flags, "true"],
                    capture_output=True,
                    timeout=3,
                )
                if r.returncode == 0:
                    info["unshare_net_ok"] = True
                    break
            except Exception:
                pass
    if info["docker"]:
        try:
            r = subprocess.run(
                [info["docker"], "info"],
                capture_output=True,
                timeout=8,
            )
            info["docker_ok"] = r.returncode == 0
        except Exception:
            info["docker_ok"] = False
    return info


def _assert_safe_mount(path: Path) -> None:
    resolved = str(path.resolve())
    home = str(Path.home().resolve())
    for suf in _FORBIDDEN_MOUNT_SUFFIXES:
        if resolved.endswith(suf) or (home + suf) in resolved:
            raise ValueError("refusing to mount sensitive path: %s" % resolved)
    base = os.path.basename(resolved)
    if base in (".ssh", "secrets", "production.env", ".env"):
        raise ValueError("refusing to mount sensitive path: %s" % resolved)


def _scrubbed_env(home: str = "/tmp") -> dict:
    return {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "HOME": home,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
    }


def _write_payload(workdir: Path, code: str, filename: str = "payload.py") -> Path:
    p = workdir / filename
    p.write_text(code if code.endswith("\n") else code + "\n", encoding="utf-8")
    return p


def _local_wrapper(payload_name: str, cpu_sec: int, as_bytes: int, *, audit: bool = True) -> str:
    """Host-side defence-in-depth when net ns is unavailable: rlimits + audit hook."""
    not_audit = not audit
    return textwrap.dedent(
        f"""\
        import os, sys, resource
        resource.setrlimit(resource.RLIMIT_CPU, ({cpu_sec}, {cpu_sec + 1}))
        resource.setrlimit(resource.RLIMIT_AS, ({as_bytes}, {as_bytes}))
        resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024 * 1024, 8 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))
        if not {not_audit}:
            _root = os.path.realpath(os.getcwd())
            def _audit(ev, args):
                if ev in (
                    "subprocess.Popen", "os.system", "os.exec", "os.execv", "os.spawn",
                    "os.spawnv", "os.execle", "os.putenv", "os.unsetenv", "os.kill",
                    "shutil.rmtree",
                ):
                    raise RuntimeError("blocked dangerous call: " + ev)
                if ev == "open":
                    p = os.path.realpath(str(args[0]))
                    mode = args[1] if len(args) > 1 else "r"
                    writing = isinstance(mode, str) and any(c in mode for c in "wxa+")
                    if writing and not (p == _root or p.startswith(_root + os.sep)):
                        raise RuntimeError("blocked write path: " + p)
                    base = os.path.basename(p)
                    if base in ("shadow", "production.env", ".env") or "/.ssh/" in p or p.endswith("/.ssh"):
                        raise RuntimeError("blocked secret path: " + p)
            sys.addaudithook(_audit)
        import runpy
        runpy.run_path({payload_name!r}, run_name="__main__")
        """
    )


def _run_popen_killable(
    cmd: Sequence[str],
    *,
    cwd: str,
    env: dict,
    wall_sec: float,
    backend: str,
) -> SandboxResult:
    t0 = time.monotonic()
    timed_out = False
    try:
        p = subprocess.Popen(
            list(cmd),
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
    except Exception as e:
        return SandboxResult(False, backend, 127, "", str(e), False, 0.0, "spawn_failed")
    try:
        out, err = p.communicate(timeout=wall_sec)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
        try:
            out, err = p.communicate(timeout=2)
        except Exception:
            out, err = "", ""
    wall = time.monotonic() - t0
    rc = p.returncode if p.returncode is not None else -9
    return SandboxResult(
        ok=(not timed_out) and rc == 0,
        backend=backend,
        returncode=rc if not timed_out else -9,
        stdout=out or "",
        stderr=err or "",
        timed_out=timed_out,
        wall_sec=wall,
    )


def run_docker(
    code: str,
    *,
    files: Optional[Mapping[str, str]] = None,
    audit: bool = True,
    image: str = DEFAULT_DOCKER_IMAGE,
    cpu_sec: int = DEFAULT_CPU_SEC,
    as_bytes: int = DEFAULT_AS_BYTES,
    wall_sec: float = DEFAULT_WALL_SEC,
    ro_binds: Optional[Sequence[tuple[str, str]]] = None,
) -> SandboxResult:
    docker = _which("docker")
    if not docker:
        return SandboxResult(False, "docker", 127, "", "docker not found", False, 0.0, "no_docker")

    cid = "e-sbx-" + secrets.token_hex(6)
    with tempfile.TemporaryDirectory(prefix="e_sandbox_") as td:
        work = Path(td)
        payload = _write_payload(work, code)
        wrapper = work / "_wrap.py"
        wrapper.write_text(_local_wrapper(payload.name, cpu_sec, as_bytes, audit=audit), encoding="utf-8")
        extra = []
        if files:
            for fname, ftext in files.items():
                if "/" in fname or fname.startswith("."):
                    return SandboxResult(False, "docker", 2, "", "bad extra filename", False, 0.0, "bad_extra_file")
                fp = work / fname
                fp.write_text(ftext, encoding="utf-8")
                os.chmod(fp, 0o644)
                extra.append(fname)
        # Container runs as uid 65534; host mkdtemp is 0700 — open it up read-only for others.
        os.chmod(work, 0o755)
        os.chmod(payload, 0o644)
        os.chmod(wrapper, 0o644)

        cmd = [
            docker, "run", "--rm", "--name", cid, "--label", "e-sbx=1",
            "--network=none",
            "--read-only",
            "--tmpfs", "/work:exec,mode=1777,size=64m",
            "--tmpfs", "/tmp:exec,mode=1777,size=32m",
            "--user", "65534:65534",
            "--cap-drop=ALL",
            "--security-opt", "no-new-privileges",
            "--memory", str(as_bytes),
            "--memory-swap", str(as_bytes),
            "--cpus", "1",
            "--pids-limit", "64",
            "-w", "/work",
            "-e", "PATH=/usr/local/bin:/usr/bin:/bin",
            "-e", "LANG=C.UTF-8",
            "-e", "HOME=/work",
            "-v", f"{work}:/input:ro",
        ]
        if ro_binds:
            for host, guest in ro_binds:
                hp = Path(host).resolve()
                _assert_safe_mount(hp)
                cmd.extend(["-v", f"{hp}:{guest}:ro"])
        boot = (
            "import shutil,sys,os;\n"
            "for _f in ['_wrap.py','%s'%s]:\n"
            "    shutil.copy('/input/'+_f,'/work/'+_f);\n"
            "os.execv(sys.executable,[sys.executable,'/work/_wrap.py'])\n"
        ) % (payload.name, "".join(",'%s'" % f for f in extra))
        cmd.extend([
            image,
            "env", "-i",
            "PATH=/usr/local/bin:/usr/bin:/bin",
            "LANG=C.UTF-8",
            "HOME=/work",
            "PYTHONDONTWRITEBYTECODE=1",
            "PYTHONIOENCODING=utf-8",
            "python", "-c", boot,
        ])
        t0 = time.monotonic()
        timed_out = False
        try:
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            try:
                out, err = p.communicate(timeout=wall_sec + 5)
            except subprocess.TimeoutExpired:
                timed_out = True
                # killpg on the docker CLI does NOT guarantee daemon-side teardown;
                # address the container by name as well (issue #15 GPT-6 blocker 2).
                for act in ((docker, "kill", cid), (docker, "rm", "-f", cid)):
                    try:
                        subprocess.run(act, capture_output=True, timeout=5)
                    except Exception:
                        pass
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except Exception:
                    p.kill()
                try:
                    out, err = p.communicate(timeout=3)
                except Exception:
                    out, err = "", "docker_wall_timeout"
        except Exception as e:
            return SandboxResult(False, "docker", 127, "", str(e), False, 0.0, "docker_spawn_failed")
        # Best-effort daemon-side teardown even on non-timeout oddities.
        try:
            subprocess.run([docker, "rm", "-f", cid], capture_output=True, timeout=5)
        except Exception:
            pass
        wall = time.monotonic() - t0
        rc = p.returncode if p.returncode is not None else -9
        return SandboxResult(
            ok=(not timed_out) and rc == 0,
            backend="docker",
            returncode=rc if not timed_out else -9,
            stdout=out or "",
            stderr=err or "",
            timed_out=timed_out,
            wall_sec=wall,
        )


def run_unshare(
    code: str,
    *,
    cpu_sec: int = DEFAULT_CPU_SEC,
    as_bytes: int = DEFAULT_AS_BYTES,
    wall_sec: float = DEFAULT_WALL_SEC,
) -> SandboxResult:
    unshare = _which("unshare")
    if not unshare:
        return SandboxResult(False, "unshare", 127, "", "unshare not found", False, 0.0, "no_unshare")
    flags = None
    for cand in (["-rn"], ["-n"]):
        probe = subprocess.run([unshare, *cand, "true"], capture_output=True, timeout=3)
        if probe.returncode == 0:
            flags = cand
            break
    if flags is None:
        return SandboxResult(
            False, "unshare", 127, "", "unshare net namespace denied", False, 0.0, "unshare_net_denied",
        )

    with tempfile.TemporaryDirectory(prefix="e_sandbox_") as td:
        work = Path(td)
        payload = _write_payload(work, code)
        wrapper = work / "_wrap.py"
        wrapper.write_text(_local_wrapper(payload.name, cpu_sec, as_bytes, audit=audit), encoding="utf-8")
        env = _scrubbed_env(home=str(work))
        cmd = [unshare, *flags, sys.executable, str(wrapper)]
        return _run_popen_killable(cmd, cwd=str(work), env=env, wall_sec=wall_sec, backend="unshare")


def run_local(
    code: str,
    *,
    cpu_sec: int = DEFAULT_CPU_SEC,
    as_bytes: int = DEFAULT_AS_BYTES,
    wall_sec: float = DEFAULT_WALL_SEC,
) -> SandboxResult:
    """Last-resort local runner: scrubbed env + rlimits + audit hook + killpg. NO net ns."""
    with tempfile.TemporaryDirectory(prefix="e_sandbox_") as td:
        work = Path(td)
        payload = _write_payload(work, code)
        wrapper = work / "_wrap.py"
        wrapper.write_text(_local_wrapper(payload.name, cpu_sec, as_bytes, audit=audit), encoding="utf-8")
        env = _scrubbed_env(home=str(work))
        res = _run_popen_killable(
            [sys.executable, str(wrapper)],
            cwd=str(work),
            env=env,
            wall_sec=wall_sec,
            backend="local",
        )
        res.detail = (res.detail + " no_net_ns").strip()
        return res


def run_sandboxed(code: str, *, prefer: Optional[str] = None, **kwargs) -> SandboxResult:
    info = detect_backends()
    order = []
    if prefer:
        order.append(prefer)
    if info.get("docker_ok"):
        order.append("docker")
    if info.get("unshare_net_ok"):
        order.append("unshare")
    order.append("local")

    seen = set()
    for name in order:
        if name in seen:
            continue
        seen.add(name)
        if name == "docker" and info.get("docker_ok"):
            return run_docker(code, **{k: kwargs[k] for k in (
                "image", "cpu_sec", "as_bytes", "wall_sec", "ro_binds"
            ) if k in kwargs})
        if name == "unshare" and info.get("unshare_net_ok"):
            return run_unshare(code, **{k: kwargs[k] for k in (
                "cpu_sec", "as_bytes", "wall_sec"
            ) if k in kwargs})
        if name == "local":
            return run_local(code, **{k: kwargs[k] for k in (
                "cpu_sec", "as_bytes", "wall_sec"
            ) if k in kwargs})
    return SandboxResult(False, "none", 127, "", "no backend", False, 0.0)


_HARMLESS = 'print("HARMLESS_OK", 1 + 1)\n'

_NEG_SHADOW = textwrap.dedent(
    """\
    try:
        data = open("/etc/shadow").read()
        print("SHADOW_LEAK", len(data))
    except Exception as e:
        print("SHADOW_DENIED", type(e).__name__)
    """
)

_NEG_ENV = textwrap.dedent(
    """\
    import os
    keys = [k for k in os.environ if any(s in k.upper() for s in ("KEY", "SECRET", "TOKEN", "PASSWORD", "AWS", "OPENAI"))]
    if keys:
        print("ENV_LEAK", ",".join(sorted(keys)))
    else:
        print("ENV_CLEAN")
    if "STRATA_TEST_SECRET" in os.environ:
        print("ENV_LEAK", "STRATA_TEST_SECRET")
    """
)

_NEG_WRITE = textwrap.dedent(
    """\
    import os
    target = "/tmp/e_sandbox_escape_%d" % os.getpid()
    tries = []
    for p in (target, "/etc/e_sandbox_should_not_exist", os.path.join(os.path.dirname(os.getcwd()) or "/", "escape.txt")):
        try:
            open(p, "w").write("pwn")
            tries.append("WROTE:" + p)
        except Exception as e:
            tries.append("DENIED:%s:%s" % (p, type(e).__name__))
    print("WRITE_RESULT", ";".join(tries))
    """
)

_NEG_NET = textwrap.dedent(
    """\
    import socket
    try:
        s = socket.socket()
        s.settimeout(1.5)
        s.connect(("1.1.1.1", 53))
        print("NET_OPEN")
    except Exception as e:
        print("NET_DENIED", type(e).__name__)
    """
)


def self_test(verbose: bool = True) -> int:
    info = detect_backends()
    if verbose:
        print("backends:", {k: v for k, v in info.items()})

    os.environ["STRATA_TEST_SECRET"] = "should-never-appear"
    failures = []

    prefer = "docker" if info.get("docker_ok") else ("unshare" if info.get("unshare_net_ok") else "local")
    if prefer == "local" and verbose:
        print("WARNING: no net namespace backend; NET negative test may be inconclusive")

    def run(label: str, code: str) -> SandboxResult:
        res = run_sandboxed(code, prefer=prefer, wall_sec=DEFAULT_WALL_SEC)
        if verbose:
            print(f"--- {label} backend={res.backend} rc={res.returncode} timeout={res.timed_out} wall={res.wall_sec:.2f}s")
            if res.stdout.strip():
                print("stdout:", res.stdout.strip()[:400])
            if res.stderr.strip():
                print("stderr:", res.stderr.strip()[:400])
        return res

    r = run("harmless", _HARMLESS)
    if not (r.ok and "HARMLESS_OK 2" in r.stdout):
        failures.append("harmless_failed")

    r = run("neg_shadow", _NEG_SHADOW)
    if "SHADOW_LEAK" in r.stdout:
        failures.append("shadow_leaked")
    elif "SHADOW_DENIED" not in r.stdout:
        failures.append("shadow_no_denial_marker")

    r = run("neg_env", _NEG_ENV)
    if "ENV_LEAK" in r.stdout or "STRATA_TEST_SECRET" in r.stdout:
        failures.append("env_leaked")
    elif "ENV_CLEAN" not in r.stdout:
        failures.append("env_clean_marker_missing")

    r = run("neg_write", _NEG_WRITE)
    if "WROTE:/etc/" in r.stdout:
        failures.append("wrote_etc")
    if "WROTE:" in r.stdout and "escape.txt" in r.stdout:
        failures.append("wrote_outside_cwd_parent")

    r = run("neg_net", _NEG_NET)
    if r.backend in ("docker", "unshare", "bwrap", "firejail"):
        if "NET_OPEN" in r.stdout:
            failures.append("network_open")
        elif "NET_DENIED" not in r.stdout:
            failures.append("network_no_denial_marker")
    else:
        if verbose:
            print("SKIP strict net assert on backend", r.backend)
        if "NET_OPEN" in r.stdout:
            failures.append("network_open_on_local_backend")

    os.environ.pop("STRATA_TEST_SECRET", None)

    if failures:
        print("SELFTEST FAIL:", ", ".join(failures))
        return 1
    print("SELFTEST PASS backend=%s" % prefer)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Category-E sandbox runner (issue #15 P0)")
    ap.add_argument("--self-test", action="store_true", help="run harmless + negative controls")
    ap.add_argument("--detect", action="store_true", help="print backend probe and exit")
    ap.add_argument("--code-file", type=str, help="run a Python file inside the sandbox")
    ap.add_argument("--prefer", choices=("docker", "unshare", "local"), default=None)
    ap.add_argument("--wall", type=float, default=DEFAULT_WALL_SEC)
    args = ap.parse_args(argv)

    if args.detect:
        print(detect_backends())
        return 0
    if args.self_test:
        return self_test(verbose=True)
    if args.code_file:
        code = Path(args.code_file).read_text(encoding="utf-8")
        res = run_sandboxed(code, prefer=args.prefer, wall_sec=args.wall)
        sys.stdout.write(res.stdout)
        sys.stderr.write(res.stderr)
        if res.timed_out:
            return 124
        return res.returncode
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
