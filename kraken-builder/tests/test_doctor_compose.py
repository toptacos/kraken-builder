from pathlib import Path

from kraken.core.cli import main
from kraken.core.doctor import inspect
from kraken.core.license import set_key
from kraken.core.lockfile import load_lock
from kraken.core.runner import run_named
from kraken.core.tentacle import install_local


ROOT = Path(__file__).resolve().parents[1]


def test_doctor_ok(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    report = inspect(ROOT)
    assert "checks" in report
    assert any(c["name"] == "protocol" for c in report["checks"])


def test_cli_doctor(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    code = main(["--root", str(ROOT), "doctor"])
    out = capsys.readouterr().out
    assert "protocol" in out
    assert code in (0, 2)


def test_lockfile_and_compose(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_LICENSE_OFFLINE", "1")
    install_local(ROOT / "examples" / "tentacles" / "geo", home=tmp_path)
    install_local(ROOT / "examples" / "tentacles" / "weather-pro", home=tmp_path)
    set_key("weather-pro", "k", home=tmp_path)
    lock = load_lock(tmp_path)
    assert "geo" in lock["tentacles"]
    result = run_named(ROOT, "weather-pro", "forecast", {"zip": "27284"}, compose=True)
    assert result["result"]["deps"]["geo"]["ok"] is True


def test_git_url_parser():
    from kraken.core.tentacle import _git_url

    assert _git_url("github.com/acme/geo").startswith("https://github.com/")
    assert _git_url("/tmp/not-a-repo") is None
