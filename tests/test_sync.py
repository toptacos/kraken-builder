from kraken.core.cli import main
from kraken.core.sync import load_session, login, pin, set_push
from kraken.core.vanilla import VANILLA


def test_account_local(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert login("dev@example.com", "laptop")["ok"] is True
    sess = load_session()
    assert sess["logged_in"] is True
    assert pin("pi", "127.0.0.1")["pinboard"]["pi"] == "127.0.0.1"
    assert set_push(True, "tok")["push"]["opt_in"] is True


def test_account_cli(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["account", "login", "a@b.co"]) == 0
    assert main(["account", "status"]) == 0
    out = capsys.readouterr().out
    assert "a@b.co" in out


def test_group_key_join(tmp_path, monkeypatch):
    from kraken.core.sync import join_group, new_group

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    created = new_group()
    assert created["group_key"].startswith("kg_")
    phone = tmp_path / "phone"
    phone.mkdir()
    monkeypatch.setenv("KRAKEN_HOME", str(phone))
    joined = join_group(created["group_key"], "phone")
    assert joined["group_key"] == created["group_key"]


def test_stale_and_nic_alert():
    from kraken.core.sync import touch_device

    sess = {
        "device_id": "dev-1",
        "devices": [{"id": "dev-1", "name": "old", "last_seen_epoch": 1, "nic": "nic_aaaa"}],
    }
    touch_device(sess, "old")
    assert "stale_device_returned" in sess["alerts"]
    assert "nic_changed" in sess["alerts"]
    assert sess["devices"][0]["nic"].startswith("nic_")


def test_vanilla_names():
    assert "filesort" in VANILLA
    assert "pi-net" in VANILLA
