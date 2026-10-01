from pathlib import Path
import tempfile

from kraken.core.cli import main
from kraken.core.tentacle import install_local
from kraken.core.workflow import interpolate, load_workflow, run_workflow


ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / "examples" / "workflows" / "polyglot-goal.yaml"
POLY = ROOT / "examples" / "tentacles" / "polyglot"


def _install_polyglot_tentacles(tmp_path: Path) -> None:
    """Install all polyglot tentacles to a temporary home."""
    for tentacle_dir in sorted(POLY.iterdir()):
        if tentacle_dir.is_dir():
            tentacle_yaml = tentacle_dir / "tentacle.yaml"
            if tentacle_yaml.exists():
                install_local(tentacle_yaml, home=tmp_path)


def test_interpolate_path():
    data = {"seed": {"result": {"zip": "27284"}}}
    assert interpolate("$seed.result.zip", data) == "27284"
    assert interpolate({"x": "$seed"}, data)["x"]["result"]["zip"] == "27284"


def test_polyglot_workflow(tmp_path):
    # Install polyglot tentacles to temp home
    _install_polyglot_tentacles(tmp_path)
    
    spec = load_workflow(WF)
    out = run_workflow(ROOT, spec, home=tmp_path)
    assert out["ok"] is True
    blob = str(out["results"]["fanout"])
    for lang in ("bash", "javascript", "php", "ruby", "perl", "go"):
        assert lang in blob


def test_cli_workflow(tmp_path, capsys):
    # Install polyglot tentacles to temp home
    _install_polyglot_tentacles(tmp_path)
    
    # Set KRAKEN_HOME to the temp path so the CLI uses it
    import os
    os.environ["KRAKEN_HOME"] = str(tmp_path)
    try:
        assert main(["--root", str(ROOT), "workflow", "run", str(WF)]) == 0
        assert "polyglot-goal" in capsys.readouterr().out
    finally:
        del os.environ["KRAKEN_HOME"]
