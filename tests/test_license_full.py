"""Exhaustive tests for kraken.core.license: every function, every branch."""

from __future__ import annotations

import io
import json
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from kraken.core import license
from kraken.core.license import (
    DEFAULT_API,
    LicenseError,
    _store_path,
    assert_licensed,
    has_local_key,
    is_premium,
    issue_remote,
    load_store,
    save_store,
    set_key,
    upgrade,
    verify_remote,
)


class _FakeResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _fake_urlopen(payload):
    def _open(req, timeout=0):
        return _FakeResponse(payload)

    return _open


def _url_error(req, timeout=0):
    raise urllib.error.URLError("connection refused")


def test_store_path_under_home(tmp_path):
    assert _store_path(tmp_path) == tmp_path / ".kraken" / "keys" / "licenses.json"


def test_store_path_default_home(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert _store_path() == tmp_path / ".kraken" / "keys" / "licenses.json"


def test_load_store_missing_file_returns_defaults(tmp_path, monkeypatch):
    monkeypatch.delenv("KRAKEN_API_BASE", raising=False)
    store = load_store(tmp_path)
    assert store == {"api_base": DEFAULT_API, "keys": {}}


def test_load_store_missing_file_honours_env_api_base(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_API_BASE", "https://api.example.com")
    store = load_store(tmp_path)
    assert store["api_base"] == "https://api.example.com"


def test_load_store_existing_file_fills_defaults(tmp_path, monkeypatch):
    monkeypatch.delenv("KRAKEN_API_BASE", raising=False)
    save_store({"keys": {"taco": {"key": "k1"}}}, home=tmp_path)
    store = load_store(tmp_path)
    assert store["api_base"] == DEFAULT_API
    assert store["keys"] == {"taco": {"key": "k1"}}


def test_load_store_existing_file_keeps_api_base(tmp_path):
    save_store({"api_base": "https://api.example.com", "keys": {}}, home=tmp_path)
    store = load_store(tmp_path)
    assert store["api_base"] == "https://api.example.com"


def test_load_store_empty_file(tmp_path):
    path = _store_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")
    store = load_store(tmp_path)
    assert store["keys"] == {}
    assert store["api_base"] == DEFAULT_API


def test_load_store_invalid_json_raises(tmp_path):
    path = _store_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json")
    with pytest.raises(json.JSONDecodeError):
        load_store(tmp_path)


def test_load_store_default_home(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    store = load_store()
    assert store["keys"] == {}


def test_save_store_writes_json(tmp_path):
    path = save_store({"keys": {"taco": {"key": "k1"}}}, home=tmp_path)
    assert path == _store_path(tmp_path)
    assert json.loads(path.read_text()) == {"keys": {"taco": {"key": "k1"}}}
    assert path.read_text().endswith("}\n")


def test_save_store_chmod_oserror_is_swallowed(tmp_path, monkeypatch):
    def _boom(self, mode, *a, **k):
        raise OSError("chmod not supported")

    monkeypatch.setattr(Path, "chmod", _boom)
    path = save_store({"keys": {}}, home=tmp_path)
    assert path.exists()


def test_save_store_default_home(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    path = save_store({"keys": {}})
    assert path == tmp_path / ".kraken" / "keys" / "licenses.json"


def test_issue_remote_success(monkeypatch):
    seen = {}

    def _open(req, timeout=0):
        seen["url"] = req.full_url
        seen["timeout"] = timeout
        seen["body"] = json.loads(req.data)
        seen["headers"] = dict(req.headers)
        return _FakeResponse({"ok": True, "key": "k_live"})

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    out = issue_remote(
        "taco", plan="kraken-pro", api_base="https://api.example.com/", email="a@b.c"
    )
    assert out["key"] == "k_live"
    assert seen["url"] == "https://api.example.com/api/kraken/licenses/issue"
    assert seen["timeout"] == 8
    assert seen["body"] == {
        "tentacle": "taco",
        "plan": "kraken-pro",
        "email": "a@b.c",
        "product": "kraken",
    }
    assert seen["headers"].get("Content-type") == "application/json"
    assert seen["headers"].get("Accept") == "application/json"


def test_issue_remote_default_plan_and_env_api_base(monkeypatch):
    monkeypatch.setenv("KRAKEN_API_BASE", "https://api.env.example")
    seen = {}

    def _open(req, timeout=0):
        seen["url"] = req.full_url
        return _FakeResponse({"ok": True, "key": "k1"})

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    out = issue_remote("taco")
    assert out["ok"] is True
    assert seen["url"] == "https://api.env.example/api/kraken/licenses/issue"


def test_issue_remote_unknown_plan():
    with pytest.raises(LicenseError, match="unknown plan 'nope'"):
        issue_remote("taco", plan="nope")


def test_issue_remote_http_error(monkeypatch):
    def _open(req, timeout=0):
        raise urllib.error.HTTPError(
            req.full_url, 500, "Server Error", {}, io.BytesIO(b"boom")
        )

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    with pytest.raises(LicenseError, match="issue API 500"):
        issue_remote("taco")


def test_issue_remote_url_error(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", _url_error)
    with pytest.raises(LicenseError, match="issue API unreachable"):
        issue_remote("taco")


def test_issue_remote_not_ok(monkeypatch):
    monkeypatch.setattr(
        urllib.request, "urlopen", _fake_urlopen({"ok": False, "error": "denied"})
    )
    with pytest.raises(LicenseError, match="denied"):
        issue_remote("taco")


def test_issue_remote_ok_without_key(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen({"ok": True}))
    with pytest.raises(LicenseError, match="no key issued"):
        issue_remote("taco")


def test_issue_remote_not_ok_without_error(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen({"ok": False}))
    with pytest.raises(LicenseError, match="no key issued"):
        issue_remote("taco")


def test_upgrade_success(tmp_path, monkeypatch):
    def fake_issue(tentacle, plan="beta", email="", api_base=None):
        return {"ok": True, "key": "k_up", "plan": plan}

    monkeypatch.setattr(license, "issue_remote", fake_issue)
    out = upgrade("taco", plan="kraken-pro", email="a@b.c", home=tmp_path)
    assert out == {"ok": True, "tentacle": "taco", "plan": "kraken-pro", "key": "k_up"}
    store = load_store(tmp_path)
    assert store["keys"]["taco"]["key"] == "k_up"
    assert store["keys"]["taco"]["plan"] == "kraken-pro"
    assert store["keys"]["taco"]["verified"] is True


def test_upgrade_default_plan(tmp_path, monkeypatch):
    def fake_issue(tentacle, plan="beta", email="", api_base=None):
        return {"ok": True, "key": "k_beta", "plan": plan}

    monkeypatch.setattr(license, "issue_remote", fake_issue)
    out = upgrade("taco", home=tmp_path)
    assert out["plan"] == "beta"
    store = load_store(tmp_path)
    assert store["keys"]["taco"]["plan"] == "beta"
    assert store["keys"]["taco"]["verified"] is True


def test_upgrade_unknown_plan(tmp_path):
    with pytest.raises(LicenseError, match="unknown plan 'nope'"):
        upgrade("taco", plan="nope", home=tmp_path)


def test_upgrade_issue_failure_propagates(tmp_path, monkeypatch):
    def boom(tentacle, plan="beta", email="", api_base=None):
        raise LicenseError("issue API unreachable")

    monkeypatch.setattr(license, "issue_remote", boom)
    with pytest.raises(LicenseError, match="issue API unreachable"):
        upgrade("taco", home=tmp_path)


def test_set_key_strips_whitespace(tmp_path):
    entry = set_key("taco", "  k_padded  ", home=tmp_path)
    assert entry == {"key": "k_padded", "verified": False}
    store = load_store(tmp_path)
    assert store["keys"]["taco"]["key"] == "k_padded"
    assert store["keys"]["taco"]["verified"] is False


def test_set_key_overwrites_existing(tmp_path):
    set_key("taco", "k1", home=tmp_path)
    set_key("taco", "k2", home=tmp_path)
    store = load_store(tmp_path)
    assert store["keys"]["taco"]["key"] == "k2"


def test_set_key_default_home(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    set_key("taco", "k1")
    assert has_local_key("taco")


def test_is_premium_none_spec():
    assert is_premium(None) is False


def test_is_premium_empty_spec():
    assert is_premium({}) is False


def test_is_premium_free():
    assert is_premium({"license": "free"}) is False


def test_is_premium_premium():
    assert is_premium({"license": "premium"}) is True


def test_is_premium_case_insensitive():
    assert is_premium({"license": "PREMIUM"}) is True
    assert is_premium({"tier": "Pro"}) is True


def test_is_premium_paid_and_pro():
    assert is_premium({"tier": "paid"}) is True
    assert is_premium({"tier": "pro"}) is True


def test_is_premium_unknown_tier():
    assert is_premium({"license": "enterprise"}) is False


def test_is_premium_license_none_falls_back_to_tier():
    assert is_premium({"license": None, "tier": "premium"}) is True


def test_is_premium_empty_license_falls_back_to_tier():
    assert is_premium({"license": "", "tier": "paid"}) is True


def test_has_local_key_missing_store(tmp_path):
    assert has_local_key("taco", home=tmp_path) is False


def test_has_local_key_present(tmp_path):
    set_key("taco", "k1", home=tmp_path)
    assert has_local_key("taco", home=tmp_path) is True


def test_has_local_key_other_tentacle(tmp_path):
    set_key("taco", "k1", home=tmp_path)
    assert has_local_key("other", home=tmp_path) is False


def test_has_local_key_blank_key(tmp_path):
    save_store({"keys": {"taco": {"key": ""}}}, home=tmp_path)
    assert has_local_key("taco", home=tmp_path) is False


def test_verify_remote_success(monkeypatch):
    seen = {}

    def _open(req, timeout=0):
        seen["url"] = req.full_url
        seen["timeout"] = timeout
        seen["body"] = json.loads(req.data)
        return _FakeResponse({"ok": True, "tentacle": "taco"})

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    out = verify_remote("taco", "k1", api_base="https://api.example.com/", timeout=3)
    assert out["ok"] is True
    assert out["tentacle"] == "taco"
    assert seen["url"] == "https://api.example.com/api/kraken/licenses/verify"
    assert seen["timeout"] == 3
    assert seen["body"] == {"tentacle": "taco", "key": "k1", "product": "kraken"}


def test_verify_remote_env_api_base(monkeypatch):
    monkeypatch.setenv("KRAKEN_API_BASE", "https://api.env.example")
    seen = {}

    def _open(req, timeout=0):
        seen["url"] = req.full_url
        return _FakeResponse({"ok": True})

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    verify_remote("taco", "k1")
    assert seen["url"] == "https://api.env.example/api/kraken/licenses/verify"


def test_verify_remote_402_with_message(monkeypatch):
    body = json.dumps({"error": {"message": "license expired"}}).encode()

    def _open(req, timeout=0):
        raise urllib.error.HTTPError(
            req.full_url, 402, "Payment Required", {}, io.BytesIO(body)
        )

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    with pytest.raises(LicenseError) as exc:
        verify_remote("taco", "k1")
    msg = str(exc.value)
    assert "paid seat" in msg
    assert "license expired" in msg
    assert "kraken.topta.co/pricing" in msg


def test_verify_remote_402_with_invalid_json(monkeypatch):
    def _open(req, timeout=0):
        raise urllib.error.HTTPError(
            req.full_url, 402, "Payment Required", {}, io.BytesIO(b"not json")
        )

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    with pytest.raises(LicenseError, match="seat required"):
        verify_remote("taco", "k1")


def test_verify_remote_402_with_non_dict_json(monkeypatch):
    body = json.dumps("a bare string").encode()

    def _open(req, timeout=0):
        raise urllib.error.HTTPError(
            req.full_url, 402, "Payment Required", {}, io.BytesIO(body)
        )

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    with pytest.raises(LicenseError, match="seat required"):
        verify_remote("taco", "k1")


def test_verify_remote_402_error_not_a_dict(monkeypatch):
    body = json.dumps({"error": "plain string"}).encode()

    def _open(req, timeout=0):
        raise urllib.error.HTTPError(
            req.full_url, 402, "Payment Required", {}, io.BytesIO(body)
        )

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    with pytest.raises(LicenseError, match="seat required"):
        verify_remote("taco", "k1")


def test_verify_remote_402_without_message(monkeypatch):
    body = json.dumps({"error": {}}).encode()

    def _open(req, timeout=0):
        raise urllib.error.HTTPError(
            req.full_url, 402, "Payment Required", {}, io.BytesIO(body)
        )

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    with pytest.raises(LicenseError, match="seat required"):
        verify_remote("taco", "k1")


def test_verify_remote_http_error_other_code(monkeypatch):
    def _open(req, timeout=0):
        raise urllib.error.HTTPError(
            req.full_url, 500, "Server Error", {}, io.BytesIO(b"boom")
        )

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    with pytest.raises(LicenseError, match="license API 500 for taco"):
        verify_remote("taco", "k1")


def test_verify_remote_url_error(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", _url_error)
    with pytest.raises(LicenseError, match="unreachable"):
        verify_remote("taco", "k1")


def test_verify_remote_not_ok_with_message(monkeypatch):
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        _fake_urlopen({"ok": False, "error": {"message": "nope"}}),
    )
    with pytest.raises(LicenseError, match="nope"):
        verify_remote("taco", "k1")


def test_verify_remote_not_ok_without_message(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen({"ok": False}))
    with pytest.raises(LicenseError, match="license rejected"):
        verify_remote("taco", "k1")


def test_assert_licensed_free_spec_returns(tmp_path):
    assert_licensed("taco", None, home=tmp_path)
    assert_licensed("taco", {"license": "free"}, home=tmp_path)


def test_assert_licensed_premium_without_key(tmp_path):
    with pytest.raises(LicenseError, match="needs a license"):
        assert_licensed("taco", {"license": "premium"}, home=tmp_path)


def test_assert_licensed_premium_with_key_offline(tmp_path, monkeypatch):
    monkeypatch.delenv("KRAKEN_LICENSE_REMOTE", raising=False)
    monkeypatch.setenv("KRAKEN_LICENSE_OFFLINE", "1")
    set_key("taco", "k1", home=tmp_path)
    assert_licensed("taco", {"license": "premium"}, home=tmp_path)


def test_assert_licensed_premium_with_key_remote(tmp_path, monkeypatch):
    monkeypatch.delenv("KRAKEN_LICENSE_OFFLINE", raising=False)
    monkeypatch.setenv("KRAKEN_LICENSE_REMOTE", "1")
    seen = {}

    def fake_verify(tentacle, key, api_base=None, timeout=8):
        seen["tentacle"] = tentacle
        seen["key"] = key
        return {"ok": True}

    monkeypatch.setattr(license, "verify_remote", fake_verify)
    set_key("taco", "k1", home=tmp_path)
    assert_licensed("taco", {"license": "premium"}, home=tmp_path)
    assert seen["tentacle"] == "taco"
    assert seen["key"] == "k1"
    store = load_store(tmp_path)
    assert store["keys"]["taco"]["verified"] is True


def test_assert_licensed_premium_with_key_no_env_skips_remote(tmp_path, monkeypatch):
    monkeypatch.delenv("KRAKEN_LICENSE_OFFLINE", raising=False)
    monkeypatch.delenv("KRAKEN_LICENSE_REMOTE", raising=False)

    def boom(tentacle, key, api_base=None, timeout=8):
        raise AssertionError("verify_remote must not be called")

    monkeypatch.setattr(license, "verify_remote", boom)
    set_key("taco", "k1", home=tmp_path)
    assert_licensed("taco", {"license": "premium"}, home=tmp_path)


def test_assert_licensed_remote_verification_failure_propagates(tmp_path, monkeypatch):
    monkeypatch.delenv("KRAKEN_LICENSE_OFFLINE", raising=False)
    monkeypatch.setenv("KRAKEN_LICENSE_REMOTE", "1")

    def boom(tentacle, key, api_base=None, timeout=8):
        raise LicenseError("license rejected")

    monkeypatch.setattr(license, "verify_remote", boom)
    set_key("taco", "k1", home=tmp_path)
    with pytest.raises(LicenseError, match="license rejected"):
        assert_licensed("taco", {"license": "premium"}, home=tmp_path)
