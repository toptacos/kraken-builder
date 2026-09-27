from pathlib import Path

from kraken.core.runner import run_named
from kraken.core.tentacle import install_local


ROOT = Path(__file__).resolve().parents[1]


def _add(tmp, name):
    install_local(ROOT / "examples" / "tentacles" / name, home=tmp)


def test_openmeteo_and_ipwhere_offline(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_OFFLINE", "1")
    _add(tmp_path, "openmeteo")
    _add(tmp_path, "ipwhere")
    w = run_named(ROOT, "openmeteo", "forecast", {"lat": 36.12, "lon": -80.07})
    assert w["ok"] is True
    assert w["result"]["source"] == "fixture"
    assert run_named(ROOT, "ipwhere", "lookup", {"ip": "1.1.1.1"})["result"]["source"] == "fixture"


def test_zip_quakes_countries_offline(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_OFFLINE", "1")
    for name in ("zippopotam", "quakes", "countries"):
        _add(tmp_path, name)
    z = run_named(ROOT, "zippopotam", "lookup", {"zip": "27284"})
    assert z["result"]["zip"] == "27284"
    assert run_named(ROOT, "quakes", "feed", {})["ok"] is True
    assert run_named(ROOT, "countries", "lookup", {"name": "united states"})["result"]["source"] == "fixture"
