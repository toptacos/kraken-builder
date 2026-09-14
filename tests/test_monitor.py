from pathlib import Path

from kraken.core.cli import main
from kraken.core.runner import run_named


ROOT = Path(__file__).resolve().parents[1]


def test_monitor_snapshot(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = run_named(ROOT, "monitor", "snapshot", {"root": str(ROOT)})
    assert result["arm"] == "monitor"
    assert "snapshot" in result


def test_cli_monitor(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["--root", str(ROOT), "monitor"]) == 0
    assert "monitor" in capsys.readouterr().out
