from pathlib import Path

from kraken.core.contract import invoke_binary
from kraken.core.grant import grant


H = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "tentacles"
    / "expose"
    / "handler.py"
)


def test_expose_denies_without_grant(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    out = invoke_binary(H, "plan", {"host": "panel.kraken.localhost"})
    assert out["ok"] is False
    assert "grant" in out["result"]["error"]


def test_expose_loopback_after_grant(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    grant("expose", True)
    out = invoke_binary(H, "plan", {"host": "app.kraken.localhost", "port": 18181})
    assert out["ok"] is True
    assert out["result"]["bind"].startswith("127.0.0.1")
    assert not out["result"]["bind"].startswith("0.0.0.0")
    assert out["result"]["public"] is False
    assert out["result"]["host"].endswith(".kraken.localhost")
