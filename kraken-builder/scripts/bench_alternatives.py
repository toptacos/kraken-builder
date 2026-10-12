#!/usr/bin/env python3
"""Benchmark Kraken against the alternatives on the three axes that matter
for "small footprint": wall time, peak memory, and installed size.

Kraken claims the "typed `make` that can run any language" slot
(docs/COMPARE.md), so its closest neighbors are the small command runners --
make and go-task -- plus the JS runtime floor (node) because tentacles may
be JS, and bash for the shell-tentacle floor. This is deliberately not
n8n-vs-Kraken: those solve a different problem and timing them against each
other would be theater.

Method notes:
- Workloads are matched per tool: start, do the minimum useful work, print
  one JSON line, exit.
- Every tool is measured once per iteration, round-robin, so a load spike on
  this machine hits all of them in the same iteration instead of whichever
  tool happened to run during it. Min over iterations is reported.
- Peak RSS comes from os.wait4 on the direct child, not RUSAGE_CHILDREN (that
  is a process-wide high-water mark and would report the first big child for
  everyone after it).
- kraken's `run` is executed from a neutral cwd, without the repo's own
  project-scope config, so it measures what a user's box pays -- no demo
  hooks, one tentacle process.

Usage:
    python3 scripts/bench_alternatives.py [--runs N]
"""

from __future__ import annotations

import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

ECHO_TENTACLE = """\
import json, sys

req = json.load(sys.stdin)
sys.stdout.write(json.dumps({"ok": True, "arm": "bench", "echo": {"action": req["action"]}}))
"""

TENTACLE_YAML = """\
name: bench
version: 0.1.0
runtime: binary
binary: handler.py
actions: [ping]
"""


def run_once(
    argv: list[str], env: dict[str, str] | None = None, cwd: Path | None = None
) -> tuple[float, float, int]:
    """(wall ms, peak RSS MB, exit code) for one child, via fork + wait4."""
    out_r, out_w = os.pipe()
    t0 = time.perf_counter_ns()
    pid = os.fork()
    if pid == 0:  # child
        try:
            os.dup2(out_w, 1)
            os.dup2(out_w, 2)
            os.close(out_r)
            os.close(out_w)
            if cwd:
                os.chdir(cwd)
            os.execvpe(argv[0], argv, env if env is not None else os.environ)
        except BaseException:
            pass
        os._exit(127)
    os.close(out_w)
    while os.read(out_r, 65536):
        pass
    os.close(out_r)
    _, status, rusage = os.wait4(pid, 0)
    dt = (time.perf_counter_ns() - t0) / 1e6
    rc = os.waitstatus_to_exitcode(status)
    return dt, rusage.ru_maxrss / (1024 * 1024), rc


def build_cases(tdir: Path, env: dict[str, str]) -> list[dict[str, Any]]:
    (tdir / "handler.py").write_text(ECHO_TENTACLE)
    (tdir / "tentacle.yaml").write_text(TENTACLE_YAML)
    # Install into the temp home so the measured path is the real one:
    # installed tentacle, discovered from $KRAKEN_HOME.
    subprocess.run(
        [sys.executable, "-m", "kraken", "tentacle", "add", str(tdir)],
        capture_output=True,
        env=env,
        cwd=tdir,
        check=True,
    )
    (tdir / "Makefile").write_text("ping:\n\t@echo '{\"ok\": true}'\n")
    cases = [
        {
            "label": "kraken --help (parse)",
            "argv": [sys.executable, "-m", "kraken", "--help"],
            "env": env,
        },
        {
            "label": "kraken run bench ping",
            "argv": [sys.executable, "-m", "kraken", "run", "bench", "ping"],
            "env": env,
            "cwd": tdir,
        },
        {"label": "make ping", "argv": ["make", "-s", "ping"], "env": env, "cwd": tdir},
        {
            "label": "node -e echo",
            "argv": ["node", "-e", "console.log(JSON.stringify({ok:true}))"],
            "env": env,
        },
        {
            "label": "bash -c echo",
            "argv": ["bash", "-c", "echo '{\"ok\": true}'"],
            "env": env,
        },
    ]
    tf = tdir / "Taskfile.yaml"
    tf.write_text("version: '3'\ntasks:\n  ping:\n    cmds: [echo '{\"ok\": true}']\n")
    if shutil.which("task"):
        smoke = run_once(["task", "--taskfile", str(tf), "ping"], env, tdir)
        if smoke[2] == 0:
            cases.append(
                {
                    "label": "task ping",
                    "argv": ["task", "--taskfile", str(tf), "ping"],
                    "env": env,
                    "cwd": tdir,
                }
            )
        else:
            print(f"(go-task skipped: it fails its own smoke test here, rc={smoke[2]})")
    return cases


def _dir_size(path: Path) -> float:
    total = 0
    for p in path.rglob("*"):
        try:
            if p.is_file() or p.is_symlink():
                total += p.stat().st_size
        except OSError:
            continue
    return total / (1024 * 1024)


def main() -> int:
    runs = 25
    if "--runs" in sys.argv:
        runs = int(sys.argv[sys.argv.index("--runs") + 1])

    home = Path(tempfile.mkdtemp(prefix="kraken-bench-alt-"))
    env = dict(os.environ)
    env.update(KRAKEN_HOME=str(home), KRAKEN_OFFLINE="1", PYTHONPATH=str(ROOT))

    with tempfile.TemporaryDirectory(prefix="kraken-bench-t-") as td:
        tdir = Path(td)
        cases = build_cases(tdir, env)

        times: dict[str, list[float]] = {c["label"]: [] for c in cases}
        rss: dict[str, list[float]] = {c["label"]: [] for c in cases}
        # Round-robin: each iteration runs every tool once, so machine load
        # is shared across tools within an iteration.
        for _ in range(runs):
            for c in cases:
                dt, mb, rc = run_once(c["argv"], c["env"], c.get("cwd"))
                assert rc == 0, (c["label"], rc)
                times[c["label"]].append(dt)
                rss[c["label"]].append(mb)

    print(f"== wall time (ms), peak RSS (MB); min of {runs} round-robin iterations ==")
    w = max(len(k) for k in times) + 2
    print(f"{'command':<{w}} {'min':>8} {'p50':>8} {'p95':>8} {'RSS MB':>8}")
    print("-" * (w + 28))
    for label in times:
        ts = sorted(times[label])
        p95 = ts[max(0, int(len(ts) * 0.95) - 1)]
        print(
            f"{label:<{w}} {ts[0]:>8.1f} {statistics.median(ts):>8.1f} "
            f"{p95:>8.1f} {min(rss[label]):>8.1f}"
        )
    print()
    print("== installed size (MB) ==")
    source = _dir_size(ROOT / "kraken")
    # Mirror Formula/kraken-cli.rb: kraken + arms + examples/tentacles,
    # minus the hello-world demo's vendored toolchains.
    libexec = source + _dir_size(ROOT / "arms") + _dir_size(ROOT / "install.sh")
    libexec += _dir_size(ROOT / "requirements.txt")
    for f in (ROOT / "examples/tentacles").iterdir():
        if f.name == "hello-world":
            continue
        libexec += _dir_size(f) if f.is_dir() else f.stat().st_size / (1024 * 1024)
    make_bin = Path(shutil.which("make") or "/usr/bin/make").stat().st_size / (
        1024 * 1024
    )
    for name, mb in [
        ("kraken source (core+CLI)", source),
        ("kraken as brew installs it", libexec),
        ("make binary", make_bin),
    ]:
        print(f"{name:<32} {mb:>8.1f}")
    print()
    print("runtime dependency: python3 >= 3.11 + pyyaml (one dep, MIT)")
    print("a tentacle brings its own runtime and adds nothing to that list.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
