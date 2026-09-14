from pathlib import Path

import pytest

from kraken.core.cli import main
from kraken.core.license import LicenseError, set_key
from kraken.core.runner import run_named
from kraken.core.tentacle import install_local


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "tentacles" / "weather-pro"
GEO = ROOT / "examples" / "tentacles" / "geo"


def _install_stack(home: Path) -> None:
    install_local(GEO, home=home)
    install_local(SAMPLE, home=home)


def test_install_and_block_without_license(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    _install_stack(tmp_path)
    assert (tmp_path / ".kraken" / "tentacles" / "weather-pro" / "tentacle.yaml").exists()
    with pytest.raises(LicenseError):
        run_named(ROOT, "weather-pro", "forecast", {"zip": "27284"})


def test_install_and_run_offline(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_LICENSE_OFFLINE", "1")
    _install_stack(tmp_path)
    set_key("weather-pro", "demo-key", home=tmp_path)
    result = run_named(ROOT, "weather-pro", "forecast", {"zip": "27284"})
    assert result["ok"] is True
    assert result["result"]["zip"] == "27284"


def test_cli_tentacle_add_needs_geo(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["--root", str(ROOT), "tentacle", "add", str(SAMPLE)]) == 2
    assert "geo" in capsys.readouterr().out


def test_cli_tentacle_add_stack(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["--root", str(ROOT), "tentacle", "add", str(GEO)]) == 0
    capsys.readouterr()
    assert main(["--root", str(ROOT), "tentacle", "add", str(SAMPLE)]) == 0
    assert "weather-pro" in capsys.readouterr().out
