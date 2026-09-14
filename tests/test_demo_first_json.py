import json
from pathlib import Path

from kraken.core.cli import main
from kraken.core.doctor import inspect, next_actions
from kraken.core.vanilla import install_vanilla

ROOT = Path(__file__).resolve().parents[1]


def test_demo_returns_city_json(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    install_vanilla(ROOT, tmp_path)
    assert main(["--root", str(ROOT), "demo", "--ip", "1.1.1.1"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["result"]["city"]
    assert data["result"]["ip"] == "1.1.1.1"


def test_doctor_lists_next_actions(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    report = inspect(ROOT)
    assert "next" in report
    assert any("geo lookup" in step for step in report["next"])
    steps = next_actions(ROOT, [])
    assert "kraken tentacle add examples/tentacles/geo" in steps
    assert "https://kraken.topta.co/use-cases" in steps[-1]
