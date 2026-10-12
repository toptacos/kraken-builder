import json
import os
import time
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib import error

import pytest

from kraken.core.sync import (
    DEFAULT_API,
    SANCTUM_TOKEN,
    STALE_SECS,
    _now,
    host_signals,
    join_group,
    load_session,
    login,
    login_with_sanctum,
    logout,
    new_group,
    nic_fingerprint,
    pin,
    remote_register,
    save_session,
    set_push,
    touch_device,
)


def test_now_returns_iso_format():
    result = _now()
    assert "T" in result
    assert result.endswith("Z")


def test_nic_fingerprint_format():
    result = nic_fingerprint()
    assert result.startswith("nic_")
    assert len(result) == 20


def test_nic_fingerprint_consistency():
    assert nic_fingerprint() == nic_fingerprint()


def test_host_signals_basic():
    result = host_signals()
    assert result["on"] is True


def test_host_signals_with_battery(tmp_path, monkeypatch):
    bat_dir = tmp_path / "BAT0"
    bat_dir.mkdir()
    (bat_dir / "capacity").write_text("85")
    (bat_dir / "status").write_text("Charging")
    with patch("kraken.core.sync.Path") as mock_path:
        mock_path.return_value = tmp_path
        result = host_signals()
    assert result["on"] is True


def test_touch_device_new_device():
    sess = {}
    result = touch_device(sess, "laptop")
    assert result["id"] == sess["device_id"]
    assert result["name"] == "laptop"
    assert result["kind"] == "cli"
    assert result["nic"].startswith("nic_")
    assert "last_seen" in result
    assert "last_seen_epoch" in result
    assert "signals" in result
    assert sess["alerts"] == []


def test_touch_device_existing_device():
    did = str(uuid.uuid4())
    sess = {
        "device_id": did,
        "devices": [
            {"id": did, "name": "old", "kind": "cli", "nic": nic_fingerprint()}
        ],
    }
    result = touch_device(sess, "new_name")
    assert result["name"] == "new_name"
    assert len(sess["devices"]) == 1
    assert sess["alerts"] == []


def test_touch_device_stale_returned():
    did = str(uuid.uuid4())
    sess = {
        "device_id": did,
        "devices": [
            {
                "id": did,
                "name": "old",
                "nic": nic_fingerprint(),
                "last_seen_epoch": int(time.time()) - STALE_SECS - 100,
            }
        ],
    }
    touch_device(sess, "old")
    assert "stale_device_returned" in sess["alerts"]


def test_touch_device_nic_changed():
    did = str(uuid.uuid4())
    sess = {
        "device_id": did,
        "devices": [
            {
                "id": did,
                "name": "old",
                "nic": "nic_different",
                "last_seen_epoch": int(time.time()),
            }
        ],
    }
    touch_device(sess, "old")
    assert "nic_changed" in sess["alerts"]


def test_touch_device_new_on_group():
    did1 = str(uuid.uuid4())
    did2 = str(uuid.uuid4())
    sess = {
        "device_id": did2,
        "devices": [{"id": did1, "name": "other", "kind": "cli"}],
    }
    touch_device(sess, "laptop")
    assert "new_device_on_group" in sess["alerts"]
    assert len(sess["devices"]) == 2


def test_touch_device_custom_kind():
    sess = {}
    result = touch_device(sess, "phone", kind="mobile")
    assert result["kind"] == "mobile"


def test_session_path_creates_dirs(tmp_path):
    from kraken.core.sync import _session_path

    path = _session_path(tmp_path)
    assert path.name == "session.json"
    assert path.parent.name == "keys"
    assert path.parent.exists()


def test_session_path_with_kraken_name(tmp_path):
    from kraken.core.sync import _session_path

    kraken_dir = tmp_path / ".kraken"
    kraken_dir.mkdir()
    path = _session_path(kraken_dir)
    assert path.parent.name == "keys"
    assert path.parent.parent == kraken_dir


def test_load_session_file_not_exists(tmp_path):
    result = load_session(tmp_path)
    assert result == {
        "v": 1,
        "logged_in": False,
        "devices": [],
        "pinboard": {},
        "push": {"opt_in": False},
    }


def test_load_session_file_exists(tmp_path):
    data = {"v": 1, "logged_in": True, "email": "test@example.com"}
    session_file = tmp_path / ".kraken" / "keys" / "session.json"
    session_file.parent.mkdir(parents=True)
    session_file.write_text(json.dumps(data))
    result = load_session(tmp_path)
    assert result["email"] == "test@example.com"


def test_save_session(tmp_path):
    data = {"v": 1, "logged_in": True}
    path = save_session(data, tmp_path)
    assert path.exists()
    loaded = json.loads(path.read_text())
    assert loaded["logged_in"] is True


def test_save_session_chmod_oserror(tmp_path):
    data = {"v": 1}
    with patch.object(Path, "chmod", side_effect=OSError):
        path = save_session(data, tmp_path)
    assert path.exists()


def test_login_fresh(tmp_path):
    result = login("user@example.com", "laptop", tmp_path)
    assert result["ok"] is True
    assert result["mode"] == "local"
    assert result["email"] == "user@example.com"
    assert result["device_id"]
    assert result["group_key"].startswith("kg_")
    assert result["nic"].startswith("nic_")


def test_login_preserves_existing(tmp_path):
    first = login("user@example.com", "laptop", tmp_path)
    second = login("other@example.com", "desktop", tmp_path)
    assert second["device_id"] == first["device_id"]
    assert second["group_key"] == first["group_key"]


def test_login_uses_env_api_base(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_API_BASE", "https://custom.api.co")
    result = login("user@example.com", "laptop", tmp_path)
    assert result["ok"] is True
    sess = load_session(tmp_path)
    assert sess["api"] == "https://custom.api.co"


def test_login_default_api(tmp_path, monkeypatch):
    monkeypatch.delenv("KRAKEN_API_BASE", raising=False)
    login("user@example.com", "laptop", tmp_path)
    sess = load_session(tmp_path)
    assert sess["api"] == DEFAULT_API


def test_login_with_sanctum_success(tmp_path):
    result = login_with_sanctum(
        "sanctum_tok_123", "user@example.com", "laptop", tmp_path
    )
    assert result["ok"] is True
    assert result["mode"] == "sanctum"
    assert result["email"] == "user@example.com"
    sess = load_session(tmp_path)
    assert sess["auth_mode"] == "sanctum"
    assert sess["token"] == "sanctum_tok_123"


def test_login_with_sanctum_empty_token(tmp_path):
    result = login_with_sanctum("", "user@example.com", home=tmp_path)
    assert result["ok"] is False
    assert "error" in result


def test_login_with_sanctum_whitespace_token(tmp_path):
    result = login_with_sanctum("   ", "user@example.com", home=tmp_path)
    assert result["ok"] is False
    assert "error" in result


def test_login_with_sanctum_preserves_email(tmp_path):
    login("existing@example.com", "laptop", tmp_path)
    result = login_with_sanctum("tok", "", "laptop", tmp_path)
    assert result["email"] == "existing@example.com"


def test_new_group(tmp_path):
    result = new_group(tmp_path)
    assert result["ok"] is True
    assert result["group_key"].startswith("kg_")
    assert result["device_id"]
    assert result["nic"].startswith("nic_")


def test_join_group_success(tmp_path):
    result = join_group("kg_abc123def456", "phone", tmp_path)
    assert result["ok"] is True
    assert result["group_key"] == "kg_abc123def456"
    assert result["nic"].startswith("nic_")


def test_join_group_invalid_prefix(tmp_path):
    result = join_group("invalid_key", "phone", tmp_path)
    assert result["ok"] is False
    assert "error" in result


def test_join_group_too_short(tmp_path):
    result = join_group("kg_shor", "phone", tmp_path)
    assert result["ok"] is False
    assert "error" in result


def test_join_group_strips_whitespace(tmp_path):
    result = join_group("  kg_abc123def456  ", "phone", tmp_path)
    assert result["ok"] is True
    assert result["group_key"] == "kg_abc123def456"


def test_logout(tmp_path):
    login("user@example.com", "laptop", tmp_path)
    result = logout(tmp_path)
    assert result["ok"] is True
    assert result["logged_in"] is False
    sess = load_session(tmp_path)
    assert sess["logged_in"] is False
    assert sess["token"] == ""


def test_pin(tmp_path):
    result = pin("server", "192.168.1.1", tmp_path)
    assert result["ok"] is True
    assert result["pinboard"]["server"] == "192.168.1.1"
    sess = load_session(tmp_path)
    assert sess["pinboard"]["server"] == "192.168.1.1"


def test_pin_overwrite(tmp_path):
    pin("key", "old_value", tmp_path)
    result = pin("key", "new_value", tmp_path)
    assert result["pinboard"]["key"] == "new_value"


def test_set_push_opt_in(tmp_path):
    result = set_push(True, "push_token_123", "web", tmp_path)
    assert result["ok"] is True
    assert result["push"]["opt_in"] is True
    assert result["push"]["token"] == "push_token_123"
    assert result["push"]["kind"] == "web"


def test_set_push_opt_out(tmp_path):
    result = set_push(False, home=tmp_path)
    assert result["ok"] is True
    assert result["push"]["opt_in"] is False


def test_remote_register_local_only(tmp_path, monkeypatch):
    monkeypatch.delenv("KRAKEN_SYNC_REMOTE", raising=False)
    result = remote_register({"api": DEFAULT_API})
    assert result["ok"] is True
    assert result["mode"] == "local-only"


def test_remote_register_success(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_SYNC_REMOTE", "1")
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"ok": true, "synced": true}'
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("kraken.core.sync.request.urlopen", return_value=mock_resp):
        result = remote_register(
            {
                "api": DEFAULT_API,
                "email": "test@example.com",
                "device_id": "dev-1",
                "device_name": "laptop",
                "token": "tok_123",
                "pinboard": {"key": "val"},
                "push": {"opt_in": True},
            }
        )
    assert result["ok"] is True
    assert result["synced"] is True


def test_remote_register_url_error(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_SYNC_REMOTE", "1")
    with patch(
        "kraken.core.sync.request.urlopen",
        side_effect=error.URLError("connection refused"),
    ):
        result = remote_register({"api": DEFAULT_API, "token": "tok"})
    assert result["ok"] is False
    assert result["mode"] == "local"
    assert "error" in result


def test_remote_register_http_error(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_SYNC_REMOTE", "1")
    with patch(
        "kraken.core.sync.request.urlopen",
        side_effect=error.HTTPError(
            DEFAULT_API, 500, "Server Error", hdrs=None, fp=None
        ),
    ):
        result = remote_register({"api": DEFAULT_API, "token": "tok"})
    assert result["ok"] is False
    assert result["mode"] == "local"


def test_remote_register_timeout(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_SYNC_REMOTE", "1")
    with patch(
        "kraken.core.sync.request.urlopen",
        side_effect=TimeoutError("timed out"),
    ):
        result = remote_register({"api": DEFAULT_API, "token": "tok"})
    assert result["ok"] is False
    assert result["mode"] == "local"


def test_remote_register_uses_sanctum_token(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_SYNC_REMOTE", "1")
    monkeypatch.setattr("kraken.core.sync.SANCTUM_TOKEN", "sanctum_tok")
    mock_req = MagicMock()
    with patch(
        "kraken.core.sync.request.Request", return_value=mock_req
    ) as mock_req_cls:
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"ok": true}'
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("kraken.core.sync.request.urlopen", return_value=mock_resp):
            remote_register({"api": DEFAULT_API, "token": "local_tok"})
    call_kwargs = mock_req_cls.call_args
    assert call_kwargs[1]["headers"]["Authorization"] == "Bearer sanctum_tok"


def test_remote_register_empty_response(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_SYNC_REMOTE", "1")
    mock_resp = MagicMock()
    mock_resp.read.return_value = b""
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("kraken.core.sync.request.urlopen", return_value=mock_resp):
        result = remote_register({"api": DEFAULT_API, "token": "tok"})
    assert result == {}


def test_remote_register_trailing_slash_api(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_SYNC_REMOTE", "1")
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"ok": true}'
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("kraken.core.sync.request.urlopen", return_value=mock_resp):
        result = remote_register({"api": "https://api.example.com/", "token": "tok"})
    assert result["ok"] is True
