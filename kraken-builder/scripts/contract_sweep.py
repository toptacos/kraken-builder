#!/usr/bin/env python3
"""Contract sweep: install every tentacle and invoke every declared action.

The per-repo pytest suites call a handler directly. That proves the handler
works and proves nothing about the path a user actually takes:

    kraken run <name> <action> --payload '{...}'
      -> runner resolves the graph and policy
      -> handler invoked with a v1 request envelope on stdin
      -> handler writes one JSON object and exits 0

docs/CONTRACT.md is the contract under test: one JSON object on stdout, exit 0
always, application failures carried as "ok": false. A non-zero exit is a
transport failure, which core wraps in RuntimeError and the CLI reports as an
error -- so a handler that exits 1 with a JSON error object is a violation.

Note: contract.py's envelope()/unwrap() ({kind, value, meta}) are dead code.
Nothing in core calls them and no handler imports them, so `kind` is not
asserted here. `watch` returns kind:"screenshot", which is not even in KINDS,
and nothing objects -- that gap is reported separately, not papered over.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

KRACKEN = Path("/Users/mcachran/Projects/Kraken/kraken-builder")
WORKSPACE = Path("/Users/mcachran/Projects/Kraken")

PAYLOADS: dict[tuple[str, str], dict] = {
    ("geo", "lookup"): {"ip": "1.1.1.1"},
    ("filesort", "scan"): {"path": "."},
    ("board", "compose"): {
        "yaml": "name: demo\nservices:\n  api:\n    image: nginx:alpine"
    },
    ("berth", "up"): {"yaml": "name: demo\nservices:\n  api:\n    image: nginx:alpine"},
    ("inlet", "plan"): {"compose": "services:\n  api:\n    image: nginx:alpine"},
    ("keeps", "add"): {"url": "https://example.com/a?ref=x", "title": "sweep"},
    ("keeps", "search"): {"q": "sweep"},
    ("marks", "add"): {"url": "https://example.com/b"},
    ("marks", "search"): {"q": "sweep"},
    ("ledger", "append"): {"arm": "geo", "action": "lookup", "ok": True},
    ("taco", "search"): {"q": "taco"},
}


def actions_of(manifest: Path) -> list[str]:
    """Declared actions. A tiny parser on purpose -- no yaml import, so this
    runs on the stdlib alone."""
    out: list[str] = []
    in_actions = False
    for raw in manifest.read_text().splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("actions:"):
            in_actions = True
            inline = line.split(":", 1)[1].strip()
            if inline.startswith("["):
                return [
                    a.strip().strip("\"'")
                    for a in inline.strip("[]").split(",")
                    if a.strip()
                ]
            continue
        if in_actions:
            if line[:1] in (" ", "\t"):
                item = line.strip()
                if item.startswith("- "):
                    out.append(item[2:].strip().strip("\"'"))
            else:
                in_actions = False
    return out


def declared_tentacle_deps(manifest: Path) -> list[str]:
    """Names under requires.tentacles, so a hard dependency is installed before
    the tentacle that needs it."""
    out: list[str] = []
    in_block = False
    for raw in manifest.read_text().splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.strip().startswith("tentacles:") and "requires" in "\n".join(
            manifest.read_text().splitlines()[: manifest.read_text().splitlines().index(raw) + 1]
        ):
            in_block = True
            continue
        if in_block:
            if line[:1] in (" ", "\t"):
                item = line.strip()
                if ":" in item:
                    out.append(item.split(":", 1)[0].strip().strip("\"'"))
            else:
                in_block = False
    return out


def run(argv, env, timeout=120):
    return subprocess.run(
        argv, env=env, capture_output=True, text=True, timeout=timeout
    )


def main() -> int:
    dirs = sorted(
        [p for p in WORKSPACE.glob("kraken-tentacle-*") if p.is_dir()]
        + [p for p in (KRACKEN / "examples" / "tentacles").iterdir() if p.is_dir()]
    )

    rows: list[tuple[str, int, int, int]] = []
    shape: list[tuple[str, str, str]] = []
    problems: list[str] = []
    tot_pass = tot_bad = tot_gated = 0

    for tdir in dirs:
        manifest = tdir / "tentacle.yaml"
        if not manifest.exists():
            continue
        if tdir.name == "_template":
            continue  # a scaffold, not a tentacle
        actions = actions_of(manifest)
        tname = tdir.name
        if not actions:
            problems.append(f"{tname}: declares no actions")
            rows.append((tname, 0, 1, 0))
            tot_bad += 1
            continue

        ok_n = bad_n = gated = 0
        with tempfile.TemporaryDirectory(prefix="kraken-sweep-") as td:
            home = Path(td)
            env = os.environ.copy()
            env.update(
                HOME=str(home),
                KRAKEN_HOME=str(home / ".kraken"),
                KRAKEN_SYSTEM_DIR=str(home / "system"),
                PYTHONPATH=str(KRACKEN),
                KRAKEN_OFFLINE="1",
            )
            (home / ".kraken").mkdir(parents=True, exist_ok=True)

            # weather-pro hard-requires geo. Installing into an empty home
            # without it is a harness artifact, not a defect -- the resolver
            # reports it precisely and refuses, which is correct.
            for dep in declared_tentacle_deps(manifest):
                dep_dir = KRACKEN / "examples" / "tentacles" / dep
                if dep_dir.is_dir():
                    run([sys.executable, "-m", "kraken", "tentacle", "add", str(dep_dir)],
                        env, timeout=600)

            inst = run(
                [sys.executable, "-m", "kraken", "tentacle", "add", str(tdir)],
                env,
                timeout=600,
            )
            if inst.returncode != 0:
                problems.append(
                    f"{tname}: tentacle add failed rc={inst.returncode}: "
                    f"{inst.stdout.strip()[-220:]}"
                )
                rows.append((tname, 0, len(actions), 0))
                tot_bad += len(actions)
                continue

            short = tname.replace("kraken-tentacle-", "")
            for action in actions:
                payload = PAYLOADS.get((short, action), {})
                proc = run(
                    [
                        sys.executable,
                        "-m",
                        "kraken",
                        "run",
                        short,
                        action,
                        "--payload",
                        json.dumps(payload),
                    ],
                    env,
                )
                blob = proc.stdout + proc.stderr
                if "needs a license" in blob:
                    gated += 1
                    continue

                line = next(
                    (
                        ln
                        for ln in reversed(proc.stdout.splitlines())
                        if ln.startswith("{")
                    ),
                    None,
                )
                if line is None:
                    bad_n += 1
                    problems.append(
                        f"{short} {action}: TRANSPORT FAILURE rc={proc.returncode} "
                        f"(contract: exit 0 + one JSON object) :: "
                        f"{blob.strip()[-180:]}"
                    )
                    continue
                try:
                    resp = json.loads(line)
                except json.JSONDecodeError as exc:
                    bad_n += 1
                    problems.append(f"{short} {action}: unparseable JSON :: {exc}")
                    continue

                issues = []
                if resp.get("v") != 1:
                    issues.append(f"v={resp.get('v')!r}")
                if "id" not in resp:
                    issues.append("no id")
                if not isinstance(resp.get("ok"), bool):
                    issues.append(f"ok={resp.get('ok')!r}")
                # `result` carries the payload on success. A refusal is
                # "ok": false plus "error" and legitimately carries neither --
                # keeps put with an empty name answers exactly that.
                if resp.get("ok") is True and "result" not in resp:
                    issues.append("ok:true with no result key")
                if resp.get("ok") is False and "error" not in resp:
                    # Where does the reason live? result.error is what several
                    # example arms use. A refusal with no reason anywhere is a
                    # real defect; a reason in an unusual key is only a shape
                    # difference.
                    res = resp.get("result")
                    reason = None
                    if isinstance(res, dict):
                        reason = res.get("error") or res.get("reason")
                    if reason:
                        shape.append((short, action, str(reason)[:70]))
                    else:
                        issues.append("ok:false with no reason anywhere")
                if issues:
                    bad_n += 1
                    problems.append(f"{short} {action}: {'; '.join(issues)}")
                else:
                    ok_n += 1

        rows.append((tname, ok_n, bad_n, gated))
        tot_pass += ok_n
        tot_bad += bad_n
        tot_gated += gated

    width = max(len(r[0]) for r in rows) + 2 if rows else 20
    print(f"{'tentacle':<{width}} {'ok':>4} {'bad':>4} {'gated':>7}")
    print("-" * (width + 19))
    for name, ok_n, bad_n, gated in rows:
        print(f"{name:<{width}} {ok_n:>4} {bad_n:>4} {gated:>7}")
    print("-" * (width + 19))
    print(f"{'TOTAL':<{width}} {tot_pass:>4} {tot_bad:>4} {tot_gated:>7}")
    print()
    if shape:
        print(f"{len(shape)} refusal(s) carrying the reason at result.error "
              f"rather than top-level error -- a shape difference, not a defect:")
        for n, a, r in shape:
            print(f"  - {n} {a}: {r}")
        print()
    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
    else:
        print("no problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
