import os
from pathlib import Path

from kraken.core.contract import envelope, unwrap
from kraken.core.runner import run_named
from kraken.core.tentacle import install_local


ROOT = Path(__file__).resolve().parents[1]


def test_envelope_kinds():
    e = envelope("text", "hello", url="https://example.com")
    assert unwrap(e)["kind"] == "text"
    assert unwrap({"x": 1})["kind"] == "json"


def test_browse_js_sucker_finish(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_OFFLINE", "1")
    os.environ["KRAKEN_OFFLINE"] = "1"
    install_local(ROOT / "examples" / "tentacles" / "save-text")
    install_local(ROOT / "examples" / "tentacles" / "browse-js")
    out = run_named(ROOT, "browse-js", "fetch", {"url": "https://example.com"})
    assert out.get("ok") is True
    assert out.get("finished") is True
    result = out.get("result") or {}
    assert result.get("kind") == "file"
    assert result.get("finished") is True
    hooks = out.get("_hooks") or []
    assert any(h.get("tentacle") == "save-text" and h.get("ok") for h in hooks)
