import os
from pathlib import Path

from kraken.core.contract import invoke_binary
from kraken.core.scopes import active_catalog, set_scope, use_scope


CA = (
    Path(__file__).resolve().parents[1] / "examples" / "tentacles" / "ca" / "handler.py"
)


def test_org_scope_key_stays_local(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    out = set_scope("work", key="kk_test_org", sites=["panel"])
    assert out["ok"] is True
    store = tmp_path / ".kraken" / "keys" / "scopes.json"
    assert store.exists()
    if os.name != "nt":
        assert oct(store.stat().st_mode)[-3:] == "600"
    cat = active_catalog()
    assert cat["active"] == "work"
    assert "kk_test_org" not in str(cat)
    switched = use_scope("global")
    assert switched["active"] == "global"


def test_ca_is_tentacle_plan(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    out = invoke_binary(CA, "plan", {"host": "panel.kraken.localhost"})
    assert out["ok"] is True
    assert "data/ca" in out["result"]["dir"].replace("\\", "/")
    assert Path(out["result"]["cert"]).exists()
    assert out["result"]["public"] is False
