from pathlib import Path

from kraken.core.cli import main
from kraken.core.license import LicenseError, set_key, upgrade


ROOT = Path(__file__).resolve().parents[1]


def test_upgrade_stores_key(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))

    def fake_issue(tentacle, plan="beta", email="", api_base=None):
        return {"ok": True, "key": "beta-testkey", "plan": plan}

    monkeypatch.setattr("kraken.core.license.issue_remote", fake_issue)
    out = upgrade("weather-pro", plan="beta", email="dev@topta.co", home=tmp_path)
    assert out["ok"] is True
    assert out["key"] == "beta-testkey"


def test_cli_upgrade(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setattr(
        "kraken.core.license.issue_remote",
        lambda *a, **k: {"ok": True, "key": "beta-cli"},
    )
    assert main(["license", "upgrade", "weather-pro", "--plan", "beta"]) == 0
    assert "beta-cli" in capsys.readouterr().out


def test_upgrade_fail(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))

    def boom(*a, **k):
        raise LicenseError("issue API unreachable")

    monkeypatch.setattr("kraken.core.license.issue_remote", boom)
    try:
        upgrade("weather-pro", home=tmp_path)
        assert False
    except LicenseError:
        pass
