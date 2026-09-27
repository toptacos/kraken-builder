from pathlib import Path

from kraken.core.contract import invoke_binary


ROOT = Path(__file__).resolve().parents[1]


def _h(name: str) -> Path:
    return ROOT / "examples" / "tentacles" / name / "handler.py"


def test_notes_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    put = invoke_binary(_h("notes"), "put", {"name": "jump", "body": "box-a"})
    assert put["ok"] is True
    got = invoke_binary(_h("notes"), "get", {"name": "jump"})
    assert got["result"]["body"] == "box-a"
    hits = invoke_binary(_h("notes"), "search", {"q": "box"})
    assert "jump" in hits["result"]["hits"]


def test_tunnel_requires_host():
    bad = invoke_binary(_h("tunnel"), "plan", {})
    assert bad["ok"] is False
    good = invoke_binary(_h("tunnel"), "plan", {"host": "127.0.0.1", "local_port": 18080})
    assert good["ok"] is True
    assert good["result"]["bind"] == "127.0.0.1"
    assert "127.0.0.1:18080" in " ".join(good["result"]["argv"])


def test_llm_plan_ro_mounts(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    out = invoke_binary(_h("llm"), "plan", {"enabled": False, "ingest": ["notes"]})
    assert out["ok"] is True
    assert out["result"]["network"] == "kraken_llm"
    assert any(m.endswith(":ro") for m in out["result"]["mounts"])
    assert "127.0.0.1:11434" in out["result"]["bind"]
