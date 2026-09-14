"""Run each language fixture if the interpreter exists."""
import json
import shutil
from pathlib import Path

from kraken.core.contract import invoke_binary


ROOT = Path(__file__).resolve().parents[1]
POLY = ROOT / "examples" / "tentacles" / "polyglot"

CASES = [
    ("python3", ROOT / "examples" / "tentacles" / "echo-bin.py"),
    ("bash", POLY / "echo.sh"),
    ("node", POLY / "echo.js"),
    ("php", POLY / "echo.php"),
    ("ruby", POLY / "echo.rb"),
    ("perl", POLY / "echo.pl"),
    ("go", POLY / "echo.go"),
]


def test_each_language_speaks_v1():
    ran = 0
    for exe, path in CASES:
        if exe != "go" and not shutil.which(exe):
            continue
        if exe == "go" and not shutil.which("go"):
            continue
        out = invoke_binary(path, "ping", {"n": 1})
        assert out.get("ok") is True
        assert out.get("v") == 1 or (out.get("result") or {}).get("lang")
        ran += 1
    assert ran >= 2


def test_polyglot_workflow_still_folds():
    from kraken.core.cli import main

    assert main(["--root", str(ROOT), "workflow", "run", str(ROOT / "examples" / "workflows" / "polyglot-goal.yaml")]) == 0
