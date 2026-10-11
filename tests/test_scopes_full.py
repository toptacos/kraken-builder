import json
from pathlib import Path


def test_path_default(tmp_path, monkeypatch):
    from kraken.core.scopes import _path

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert _path(tmp_path) == tmp_path / ".kraken" / "keys" / "scopes.json"


def test_load_scopes_missing_file(tmp_path, monkeypatch):
    from kraken.core.scopes import load_scopes

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = load_scopes(tmp_path)
    assert result == {"active": "global", "orgs": {}}


def test_load_scopes_existing_file(tmp_path, monkeypatch):
    from kraken.core.scopes import load_scopes

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    keys_dir = tmp_path / ".kraken" / "keys"
    keys_dir.mkdir(parents=True)
    (keys_dir / "scopes.json").write_text(
        json.dumps({"active": "work", "orgs": {"work": {"key": "kk_x", "sites": []}}})
    )
    result = load_scopes(tmp_path)
    assert result["active"] == "work"
    assert result["orgs"]["work"]["key"] == "kk_x"


def test_load_scopes_adds_defaults(tmp_path, monkeypatch):
    from kraken.core.scopes import load_scopes

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    keys_dir = tmp_path / ".kraken" / "keys"
    keys_dir.mkdir(parents=True)
    (keys_dir / "scopes.json").write_text(json.dumps({}))
    result = load_scopes(tmp_path)
    assert result["active"] == "global"
    assert result["orgs"] == {}


def test_save_scopes(tmp_path, monkeypatch):
    from kraken.core.scopes import save_scopes

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    store = {"active": "global", "orgs": {}}
    path = save_scopes(store, home=tmp_path)
    assert path.exists()
    assert json.loads(path.read_text()) == store


def test_save_scopes_chmod_failure(tmp_path, monkeypatch):
    from kraken.core.scopes import save_scopes

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))

    def fake_chmod(self, mode):
        raise OSError("read-only")

    monkeypatch.setattr(Path, "chmod", fake_chmod)
    path = save_scopes({"active": "global", "orgs": {}}, home=tmp_path)
    assert path.exists()


def test_set_scope_with_key(tmp_path, monkeypatch):
    from kraken.core.scopes import set_scope

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = set_scope("work", key="kk_test", sites=["panel"], home=tmp_path)
    assert result["ok"] is True
    assert result["org"] == "work"
    assert result["active"] == "work"
    assert result["sites"] == ["panel"]


def test_set_scope_generates_key(tmp_path, monkeypatch):
    from kraken.core.scopes import set_scope, load_scopes

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = set_scope("work", home=tmp_path)
    assert result["ok"] is True
    store = load_scopes(tmp_path)
    assert store["orgs"]["work"]["key"].startswith("kk_")


def test_set_scope_without_sites(tmp_path, monkeypatch):
    from kraken.core.scopes import set_scope

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = set_scope("work", key="kk_x", home=tmp_path)
    assert result["sites"] == []


def test_set_scope_overwrites_existing(tmp_path, monkeypatch):
    from kraken.core.scopes import set_scope, load_scopes

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    set_scope("work", key="kk_old", home=tmp_path)
    set_scope("work", key="kk_new", home=tmp_path)
    store = load_scopes(tmp_path)
    assert store["orgs"]["work"]["key"] == "kk_new"


def test_use_scope_global(tmp_path, monkeypatch):
    from kraken.core.scopes import use_scope

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = use_scope("global", home=tmp_path)
    assert result["ok"] is True
    assert result["active"] == "global"
    assert result["sites"] == []


def test_use_scope_known_org(tmp_path, monkeypatch):
    from kraken.core.scopes import set_scope, use_scope

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    set_scope("work", key="kk_x", sites=["panel"], home=tmp_path)
    result = use_scope("work", home=tmp_path)
    assert result["ok"] is True
    assert result["active"] == "work"
    assert result["sites"] == ["panel"]


def test_use_scope_unknown_org(tmp_path, monkeypatch):
    from kraken.core.scopes import use_scope

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = use_scope("nonexistent", home=tmp_path)
    assert result["ok"] is False
    assert "unknown org" in result["error"]


def test_active_catalog_global(tmp_path, monkeypatch):
    from kraken.core.scopes import active_catalog

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = active_catalog(tmp_path)
    assert result["ok"] is True
    assert result["active"] == "global"
    assert result["filter"] is None
    assert "note" in result


def test_active_catalog_org_with_key(tmp_path, monkeypatch):
    from kraken.core.scopes import active_catalog, set_scope

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    set_scope("work", key="kk_x", sites=["panel"], home=tmp_path)
    result = active_catalog(tmp_path)
    assert result["ok"] is True
    assert result["active"] == "work"
    assert result["filter"] == ["panel"]
    assert result["has_key"] is True


def test_active_catalog_org_without_sites(tmp_path, monkeypatch):
    from kraken.core.scopes import active_catalog, set_scope

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    set_scope("work", key="kk_x", home=tmp_path)
    result = active_catalog(tmp_path)
    assert result["filter"] == []
    assert result["has_key"] is True


def test_active_catalog_defaults_to_global(tmp_path, monkeypatch):
    from kraken.core.scopes import active_catalog

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    keys_dir = tmp_path / ".kraken" / "keys"
    keys_dir.mkdir(parents=True)
    (keys_dir / "scopes.json").write_text(json.dumps({"orgs": {}}))
    result = active_catalog(tmp_path)
    assert result["active"] == "global"
