import os
from pathlib import Path

from kraken.core.runner import run_named
from kraken.core.tentacle import install_local


ROOT = Path(__file__).resolve().parents[1]


def test_wx_fetch_sucker_finish(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_OFFLINE", "1")
    os.environ["KRAKEN_OFFLINE"] = "1"
    install_local(ROOT / "examples" / "tentacles" / "wx-units")
    install_local(ROOT / "examples" / "tentacles" / "wx")
    out = run_named(ROOT, "wx", "forecast", {"lat": 36.85, "lon": -76.29})
    assert out.get("ok") is True
    assert out.get("finished") is True
    result = out.get("result") or {}
    assert result.get("temperature_c") == 20.0
    assert result.get("temperature_f") == 68.0
    assert result.get("finished") is True
    assert "F" in (result.get("summary") or "")
    hooks = out.get("_hooks") or []
    assert any(h.get("tentacle") == "wx-units" and h.get("ok") for h in hooks)
