from pathlib import Path

from kraken.core.hooks import collect_hooks
from kraken.core.instance import (
    create_instance,
    export_bundle,
    import_bundle,
    list_instances,
)
from kraken.core.cli import main


ROOT = Path(__file__).resolve().parents[1]


def test_hooks_sort_by_priority(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    cfg = tmp_path / ".kraken"
    cfg.mkdir()
    (cfg / "config.yaml").write_text(
        "version: 1\n"
        "hooks:\n"
        "  after_run:\n"
        "    - tentacle: late\n"
        "      action: ping\n"
        "      priority: 50\n"
        "    - tentacle: early\n"
        "      action: ping\n"
        "      priority: 1\n"
    )
    monkeypatch.chdir(tmp_path)
    names = [h["tentacle"] for h in collect_hooks(tmp_path, "after_run", "geo")]
    assert names[:2] == ["early", "late"]


def test_instance_create_export_skips_keys(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    from kraken.core.instance import instances_root

    monkeypatch.setattr("kraken.core.instance.user_home", lambda: tmp_path)
    created = create_instance("laptop", "Travel box")
    assert created["ok"] is True
    keys = tmp_path / ".kraken" / "instances" / "laptop" / ".kraken" / "keys"
    keys.mkdir(parents=True, exist_ok=True)
    (keys / "licenses.json").write_text('{"keys":{"secret":{"key":"do-not-export"}}}')
    blob = export_bundle("laptop")
    assert b"do-not-export" not in blob
    rows = list_instances()
    assert any(r["name"] == "laptop" for r in rows)
    archive = tmp_path / "laptop.kraken.tgz"
    archive.write_bytes(blob)
    imported = import_bundle(archive, "pi")
    assert imported["ok"] is True
    assert not (
        tmp_path / ".kraken" / "instances" / "pi" / ".kraken" / "keys" / "licenses.json"
    ).exists()


def test_cli_instance_new(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setattr("kraken.core.instance.user_home", lambda: tmp_path)
    assert main(["instance", "new", "desk", "--label", "Office"]) == 0
    out = capsys.readouterr().out
    assert "desk" in out
    assert main(["instance", "list"]) == 0
