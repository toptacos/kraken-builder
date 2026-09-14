from pathlib import Path

from kraken.core.contract import invoke_binary


H = Path(__file__).resolve().parents[1] / "examples" / "tentacles" / "panel" / "handler.py"


def test_panel_status_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    st = invoke_binary(H, "status", {})
    assert st["ok"] is True
    assert st["result"]["bind"].startswith("127.0.0.1")
    assert "config" in st["result"]["paths"]
    assert st["result"]["resources"]["cpu_count"]


def test_panel_ui_and_contact(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    ui = invoke_binary(H, "ui", {})
    assert Path(ui["result"]["path"]).exists()
    bad = invoke_binary(H, "contact", {"email": "nope"})
    assert bad["ok"] is False
    good = invoke_binary(H, "contact", {"email": "a@b.co", "body": "hi", "scope": "work"})
    assert good["ok"] is True
    assert good["result"]["sent"] is False
    assert "api.topta.co" in good["result"]["url"]
    assert good["result"]["json"]["scope"] == "work"
