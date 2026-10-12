#!/usr/bin/env python3
"""Benchmark the tentacle contract transport.

contract_sweep.py answers "is the contract honored" across every tentacle.
This answers the performance half: where does a single invocation's time
actually go, and what does each core helper cost before the spawn?

The v1 transport is one subprocess per invoke -- a JSON request on stdin, one
JSON object on stdout, exit 0 always. That design buys language freedom and
pays a process spawn per call, so the numbers below separate the three layers
that make up one invoke_binary():

    interpreter startup      python3 -c pass              (the floor)
    contract core overhead   encode + env + argv + decode
    full round trip          invoke_binary(echo handler)

In-process helpers are measured at four payload sizes (0 B, ~1 KB, ~64 KB,
1 MB) because that is the axis that actually moves: envelope bytes, not
control flow. The env helper is measured on both paths -- prepend (bare
checkout) and inherit (root already importable, the common case).

The subprocess layer is spawn-bound, so it is measured with spawn
statistics (min, mean, p50, p95, max) and the floor call is interleaved with
the real call so machine drift cancels out of the delta instead of passing
for overhead.

Usage:
    python3 scripts/bench_contract.py            # full run (~150 spawns)
    python3 scripts/bench_contract.py --quick    # ~25 spawns, coarser stats
"""

from __future__ import annotations

import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kraken.core.contract import (  # noqa: E402
    KINDS,
    PROTOCOL_VERSION,
    _ROOT,
    _argv,
    _subprocess_env,
    decode_response,
    encode_request,
    envelope,
    invoke_binary,
    unwrap,
)

ECHO_HANDLER = """\
import json, sys

req = json.load(sys.stdin)
sys.stdout.write(json.dumps({"v": 1, "id": req["id"], "ok": True, "result": {"echo": req["action"]}}))
"""


def payloads() -> list[tuple[str, dict]]:
    """Shapes straddling what tentacles actually exchange: an empty ping, a
    scrape's page blob, a board's scanned file list, and a media buffer big
    enough that stdout dominates the spawn."""
    return [
        ("empty", {}),
        ("1 KB", {"items": ["x" * 10] * 100}),
        ("64 KB", {"items": ["y" * 10] * 6400}),
        ("1 MB", {"items": ["z" * 10] * 100000}),
    ]


def micros(fn, iters: int) -> float:
    """Best us/op across 3 passes. A single pass on a shared mac reports
    scheduler noise, not cost."""
    best = float("inf")
    for _ in range(3):
        t0 = time.perf_counter_ns()
        for _ in range(iters):
            fn()
        best = min(best, (time.perf_counter_ns() - t0) / iters / 1000)
    return best


def in_process() -> None:
    one_kb = payloads()[1][1]
    rows = [
        ("encode_request 1 KB", micros(lambda: encode_request("ping", one_kb), 5000)),
        (
            "decode_response",
            micros(lambda: decode_response(b'{"ok": true, "result": {}}'), 5000),
        ),
        ("_argv(.py)", micros(lambda: _argv(Path("handler.py")), 5000)),
        ("envelope+unwrap", micros(lambda: unwrap(envelope("json", {"k": "v"})), 5000)),
    ]

    # Env helper, both paths. Prepend needs the root OFF the path; inherit
    # needs it ON. Measure each in its state, then restore.
    saved = os.environ.get("PYTHONPATH")
    stripped = [p for p in (saved or "").split(os.pathsep) if p and p != str(_ROOT)]
    try:
        os.environ["PYTHONPATH"] = os.pathsep.join(stripped)
        prepend = micros(_subprocess_env, 5000)
        os.environ["PYTHONPATH"] = os.pathsep.join(stripped + [str(_ROOT)])
        inherit = micros(_subprocess_env, 5000)
    finally:
        if saved is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = saved

    rows.insert(3, ("_subprocess_env prepend", prepend))
    rows.insert(4, ("_subprocess_env inherit", inherit))

    print("== in-process helpers (us/op, best of 3 passes) ==")
    width = max(len(n) for n, _ in rows) + 2
    print(f"{'helper':<{width}} {'us/op':>10}")
    print("-" * (width + 12))
    for name, us in rows:
        print(f"{name:<{width}} {us:>10.2f}")
    print()

    print("== envelope round trip by payload size (us/op) ==")
    print(f"{'payload':<10} {'encode':>10} {'decode':>10}")
    print("-" * 32)
    for label, payload in payloads():
        raw = encode_request("ping", payload)
        enc = micros(lambda p=payload: encode_request("ping", p), 300)
        dec = micros(lambda r=raw: decode_response(r), 300)
        print(f"{label:<10} {enc:>10.2f} {dec:>10.2f}")
    print()


def _spawn(env: dict[str, str] | None) -> float:
    t0 = time.perf_counter_ns()
    subprocess.run(
        [sys.executable, "-c", "pass"], capture_output=True, env=env, check=True
    )
    return (time.perf_counter_ns() - t0) / 1e6


def stats(times: list[float]) -> str:
    s = sorted(times)
    p95 = s[min(len(s) - 1, int(len(s) * 0.95))]
    return (
        f"min={s[0]:6.2f} mean={statistics.fmean(s):6.2f} "
        f"p50={statistics.median(s):6.2f} p95={p95:6.2f} max={s[-1]:6.2f} (ms)"
    )


def end_to_end(quick: bool) -> None:
    runs = 25 if quick else 150
    print(f"== end-to-end invoke_binary (echo handler, n={runs}, interleaved floor) ==")
    with tempfile.TemporaryDirectory(prefix="kraken-bench-") as td:
        handler = Path(td) / "handler.py"
        handler.write_text(ECHO_HANDLER)

        floor: list[float] = []
        full: list[float] = []
        deltas: list[float] = []
        for i in range(runs):
            f = _spawn(_subprocess_env())
            t0 = time.perf_counter_ns()
            invoke_binary(handler, "ping", payloads()[2][1], req_id=str(i))
            v = (time.perf_counter_ns() - t0) / 1e6
            floor.append(f)
            full.append(v)
            deltas.append(v - f)

        print(f"interpreter floor : {stats(floor)}")
        print(f"invoke_binary     : {stats(full)}")
        print(
            f"per-call delta    : mean={statistics.fmean(deltas):.2f}ms "
            f"p50={statistics.median(deltas):.2f}ms "
            f"(64 KB payload + whatever the handler does)"
        )
        print(f"serial throughput : {1000 / statistics.fmean(full):.0f} invokes/s")
        print()
        print("read: one binary tentacle costs one interpreter start. Contract")
        print("core (env prep + encode + argv + decode) sits in the envelope")
        print("micros above; the spawn is the lever, e.g. batch independent")
        print("work or keep a handler resident.")


def main() -> int:
    quick = "--quick" in sys.argv
    print(f"kraken contract benchmark  (python {sys.version.split()[0]})")
    print(f"protocol v{PROTOCOL_VERSION}  kinds={','.join(KINDS)}")
    print()
    in_process()
    end_to_end(quick)
    return 0


if __name__ == "__main__":
    sys.exit(main())
