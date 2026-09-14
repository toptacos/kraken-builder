from pathlib import Path

from kraken.core.cli import main
from kraken.core.workflow import interpolate, load_workflow, run_workflow


ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / "examples" / "workflows" / "polyglot-goal.yaml"


def test_interpolate_path():
    data = {"seed": {"result": {"zip": "27284"}}}
    assert interpolate("$seed.result.zip", data) == "27284"
    assert interpolate({"x": "$seed"}, data)["x"]["result"]["zip"] == "27284"


def test_polyglot_workflow():
    spec = load_workflow(WF)
    out = run_workflow(ROOT, spec)
    assert out["ok"] is True
    blob = str(out["results"]["fanout"])
    for lang in ("bash", "javascript", "php", "ruby", "perl", "go"):
        assert lang in blob


def test_cli_workflow(capsys):
    assert main(["--root", str(ROOT), "workflow", "run", str(WF)]) == 0
    assert "polyglot-goal" in capsys.readouterr().out
