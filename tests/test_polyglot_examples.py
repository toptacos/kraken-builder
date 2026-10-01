"""Run each language fixture if the interpreter exists."""

import json
import shutil
import tempfile
from pathlib import Path

from kraken.core.contract import invoke_binary
from kraken.core.tentacle import install_local


ROOT = Path(__file__).resolve().parents[1]
POLY = ROOT / "examples" / "tentacles" / "polyglot"

CASES = [
    ("python3", ROOT / "examples" / "tentacles" / "echo-bin.py"),
    ("bash", POLY / "echo-sh" / "echo.sh"),
    ("node", POLY / "echo-js" / "echo.js"),
    ("php", POLY / "echo-php" / "echo.php"),
    ("ruby", POLY / "echo-rb" / "echo.rb"),
    ("perl", POLY / "echo-pl" / "echo.pl"),
    ("go", POLY / "echo-go" / "echo.go"),
]


def _install_polyglot_tentacles(tmp_path: Path) -> None:
    """Install all polyglot tentacles to a temporary home."""
    for tentacle_dir in sorted(POLY.iterdir()):
        if tentacle_dir.is_dir():
            tentacle_yaml = tentacle_dir / "tentacle.yaml"
            if tentacle_yaml.exists():
                install_local(tentacle_yaml, home=tmp_path)


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


def test_polyglot_workflow_still_folds(tmp_path):
    from kraken.core.cli import main
    import os

    # Install polyglot tentacles to temp home
    _install_polyglot_tentacles(tmp_path)

    # Set KRAKEN_HOME to the temp path so the CLI uses it
    os.environ["KRAKEN_HOME"] = str(tmp_path)
    try:
        assert (
            main(
                [
                    "--root",
                    str(ROOT),
                    "workflow",
                    "run",
                    str(ROOT / "examples" / "workflows" / "polyglot-goal.yaml"),
                ]
            )
            == 0
        )
    finally:
        del os.environ["KRAKEN_HOME"]
