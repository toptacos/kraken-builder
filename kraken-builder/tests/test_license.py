import json
from pathlib import Path

import pytest

from kraken.core.license import LicenseError, assert_licensed, set_key
from kraken.core.runner import run_named


def test_free_tentacle_does_not_need_key(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert_licensed("echo", {"license": "free"})


def test_premium_without_key_fails(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with pytest.raises(LicenseError):
        assert_licensed("weather-pro", {"license": "premium"})


def test_premium_with_local_key_offline(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_LICENSE_OFFLINE", "1")
    set_key("weather-pro", "test-key", home=tmp_path)
    assert_licensed("weather-pro", {"license": "premium"}, home=tmp_path)


def test_echo_still_runs(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    root = Path(__file__).resolve().parents[1]
    result = run_named(root, "echo", "ping", {})
    assert result["ok"] is True
