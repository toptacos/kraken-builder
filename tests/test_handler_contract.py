"""Every handler must obey the exit-code half of docs/CONTRACT.md.

    Non-zero exit is a transport failure. Application failures use
    "ok": false and exit 0.

Two handlers got this backwards. Both wrote a correct v1 body --

    {"v":1,"id":"1","ok":false,"error":{"code":"missing_config", ...}}

-- and then exited 1, so core treated it as a broken transport, discarded the
body, and raised. A user asking "why did berth fail?" got a RuntimeError and a
stack trace instead of "no project config".

The per-repo suites never caught it because they call the handler directly and
read stdout. Nothing checked the exit code against the body it had just
written, which is exactly the contract's whole point.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from kraken.core.runner import DEFAULT_TIMEOUT_SEC

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent

# Probed actions. Each handler is asked for these until one produces a JSON
# body; the first body that says ok:false is the interesting case.
PROBE_ACTIONS = ("ping", "status", "plan", "list", "get", "run", "fetch")


def handler_dirs() -> list[Path]:
    found = sorted(WORKSPACE.glob("kraken-tentacle-*"))
    found += sorted((ROOT / "examples" / "tentacles").iterdir())
    return [d for d in found if d.is_dir() and (d / "tentacle.yaml").exists()]


def handler_binaries(d: Path) -> list[list[str]]:
    spec = (d / "tentacle.yaml").read_text()
    out = []
    for suffix, argv in ((".sh", ["bash"]), (".py", [sys.executable])):
        for candidate in (d / f"handler{suffix}",):
            if candidate.exists():
                out.append(argv + [str(candidate)])
    assert spec  # manifest is the reason this dir is a tentacle
    return out


def probe(argv: list[str], action: str) -> tuple[int, dict | None, str]:
    request = json.dumps(
        {"v": 1, "id": "1", "op": "invoke", "action": action, "payload": {}}
    )
    try:
        proc = subprocess.run(
            argv, input=request.encode(), capture_output=True, timeout=25
        )
    except subprocess.TimeoutExpired:
        return 124, None, "timeout"
    raw = proc.stdout.decode("utf-8", "replace").strip()
    body = None
    if raw.startswith("{"):
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = None
    return proc.returncode, body, raw


@pytest.mark.parametrize("tdir", handler_dirs(), ids=lambda d: d.name)
def test_handler_exit_code_agrees_with_its_body(tdir: Path):
    """A handler that writes "ok": false has delivered a valid response and
    must exit 0. Exiting non-zero makes core throw the body away."""
    offences = []
    for argv in handler_binaries(tdir):
        for action in PROBE_ACTIONS:
            rc, body, _raw = probe(argv, action)
            if rc == 0 or body is None:
                continue
            if body.get("ok") is False:
                offences.append(
                    f"{Path(argv[-1]).name} action={action} exited {rc} after writing "
                    f"ok:false ({body.get('error')})"
                )
                break
    assert not offences, "exit code contradicts the body it wrote:\n  " + "\n  ".join(
        offences
    )


@pytest.mark.parametrize("tdir", handler_dirs(), ids=lambda d: d.name)
def test_every_declared_action_answers_with_one_json_object(tdir: Path):
    """Core decodes one JSON object from stdout. A handler that answers with
    nothing, or with prose, is a transport failure at run time."""
    import re

    actions: list[str] = []
    in_actions = False
    for raw in (tdir / "tentacle.yaml").read_text().splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("actions:"):
            in_actions = True
            inline = line.split(":", 1)[1].strip()
            if inline.startswith("["):
                actions = [
                    a.strip().strip("\"'")
                    for a in inline.strip("[]").split(",")
                    if a.strip()
                ]
                break
            continue
        if in_actions:
            if line[:1] in (" ", "\t") and line.strip().startswith("- "):
                actions.append(line.strip()[2:].strip().strip("\"'"))
            elif line[:1] not in (" ", "\t"):
                break

    binaries = handler_binaries(tdir)
    if not binaries:
        pytest.skip("no handler.sh or handler.py")

    bad = []
    for action in actions:
        for argv in binaries:
            rc, body, raw = probe(argv, action)
            if body is None:
                # A traceback is a crash, not an answer. Name the action.
                if "Traceback" in raw or rc not in (0, 1, 2):
                    bad.append(
                        f"{Path(argv[-1]).name} {action}: rc={rc} and no JSON body"
                    )
    assert not bad, "\n  ".join(bad)


def test_manifest_timeout_sec_is_honoured_and_clamped():
    """timeout_sec used to be dead config: invoke_binary defaulted to 30 and no
    caller passed anything, so an arm that declared 20s got 30 and one that
    declared 120 could never spend its budget."""
    from kraken.core.runner import (
        DEFAULT_TIMEOUT_SEC,
        MAX_TIMEOUT_SEC,
        tentacle_timeout,
    )

    assert tentacle_timeout({}) == DEFAULT_TIMEOUT_SEC
    assert tentacle_timeout({"timeout_sec": 20}) == 20
    assert tentacle_timeout({"timeout_sec": 5}) == 5
    # A manifest cannot buy an unbounded run.
    assert tentacle_timeout({"timeout_sec": 99999}) == MAX_TIMEOUT_SEC
    assert tentacle_timeout({"timeout_sec": 0}) == 1
    assert tentacle_timeout({"timeout_sec": -5}) == 1
    # Junk falls back rather than exploding mid-run.
    assert tentacle_timeout({"timeout_sec": "soon"}) == DEFAULT_TIMEOUT_SEC
    assert tentacle_timeout({"timeout_sec": None}) == DEFAULT_TIMEOUT_SEC


def test_every_declared_timeout_is_usable_by_its_handler():
    """A handler that sets its own subprocess timeout above core's can never
    use it -- core kills the process first. Catch that at review time."""
    offenders = []
    for tdir in handler_dirs():
        manifest = (tdir / "tentacle.yaml").read_text()
        declared = None
        for line in manifest.splitlines():
            if line.strip().startswith("timeout_sec:"):
                declared = int(line.split(":", 1)[1].strip())
        for suffix in (".sh", ".py"):
            h = tdir / f"handler{suffix}"
            if not h.exists() or suffix != ".py":
                continue
            src = h.read_text()
            for n, line in enumerate(src.splitlines(), 1):
                if "timeout=" not in line:
                    continue
                digits = "".join(c for c in line.split("timeout=")[1] if c.isdigit())
                if not digits:
                    continue
                budget = int(digits)
                ceiling = declared if declared is not None else DEFAULT_TIMEOUT_SEC
                if budget > ceiling:
                    offenders.append(
                        f"{tdir.name}/handler{suffix}:{n} timeout={budget} exceeds "
                        f"core's {ceiling}s -- core kills it first"
                    )
    assert not offenders, "\n  ".join(offenders)
