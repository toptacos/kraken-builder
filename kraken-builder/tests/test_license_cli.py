from pathlib import Path

from kraken.core.cli import main


def test_license_set_and_status(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["license", "set", "weather-pro", "abc"]) == 0
    capsys.readouterr()
    assert main(["license", "status"]) == 0
    out = capsys.readouterr().out
    assert "weather-pro" in out
    assert "abc" in out


def test_verify_without_key(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["license", "verify", "missing"]) == 2
    assert "no local key" in capsys.readouterr().out
