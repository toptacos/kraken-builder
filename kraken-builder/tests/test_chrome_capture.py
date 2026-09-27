import json
from pathlib import Path

from kraken.core.license import set_key
from kraken.core.runner import run_named
from kraken.core.vanilla import install_vanilla

ROOT = Path(__file__).resolve().parents[1]


def test_chrome_capture_fixture_with_offline_license(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_LICENSE_OFFLINE", "1")
    monkeypatch.delenv("KRAKEN_CHROME", raising=False)
    install_vanilla(ROOT, tmp_path)
    from kraken.core.tentacle import install_local

    install_local(ROOT / "examples/tentacles/chrome-capture")
    set_key("chrome-capture", "test-key")
    out = run_named(ROOT, "chrome-capture", "probe", {"url": "https://kraken.topta.co"})
    assert out["ok"] is True
    assert out["result"]["engine"] == "fixture"
    assert out["result"]["mit"] is True


def test_chrome_capture_denied_without_key(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.delenv("KRAKEN_LICENSE_OFFLINE", raising=False)
    install_vanilla(ROOT, tmp_path)
    from kraken.core.license import LicenseError
    from kraken.core.tentacle import install_local

    install_local(ROOT / "examples/tentacles/chrome-capture")
    try:
        run_named(ROOT, "chrome-capture", "probe", {})
        raise AssertionError("expected LicenseError")
    except LicenseError:
        pass
