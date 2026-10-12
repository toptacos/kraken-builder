import json
from pathlib import Path

import pytest

from kraken.billing.client import BillingClient, log
from kraken.core.license import LicenseError


@pytest.fixture(autouse=True)
def _quiet_emit(monkeypatch):
    monkeypatch.setattr("kraken.billing.client.emit", lambda *a, **k: None)


def test_log_with_billing_log_env(capsys, monkeypatch):
    monkeypatch.setenv("KRAKEN_BILLING_LOG", "1")
    log("test_event", foo="bar")
    err = capsys.readouterr().err
    data = json.loads(err.strip())
    assert data["billing"] == "test_event"
    assert data["foo"] == "bar"


def test_log_with_notify_stdout_env(capsys, monkeypatch):
    monkeypatch.setenv("KRAKEN_NOTIFY_STDOUT", "1")
    log("test_event")
    err = capsys.readouterr().err
    assert "test_event" in err


def test_log_without_env_vars(capsys, monkeypatch):
    monkeypatch.delenv("KRAKEN_BILLING_LOG", raising=False)
    monkeypatch.delenv("KRAKEN_NOTIFY_STDOUT", raising=False)
    log("test_event")
    assert capsys.readouterr().err == ""


def test_log_calls_emit(monkeypatch):
    calls = []
    monkeypatch.setattr("kraken.billing.client.emit", lambda e, p: calls.append((e, p)))
    log("my_event", x=1)
    assert calls == [("billing.my_event", {"x": 1})]


def test_log_without_payload(monkeypatch):
    calls = []
    monkeypatch.setattr("kraken.billing.client.emit", lambda e, p: calls.append((e, p)))
    log("my_event")
    assert calls == [("billing.my_event", {})]


def test_client_init_with_explicit_api_base(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    client = BillingClient(api_base="https://example.com/")
    assert client.api_base == "https://example.com"


def test_client_init_from_store(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    store = tmp_path / ".kraken" / "keys"
    store.mkdir(parents=True)
    (store / "licenses.json").write_text(
        json.dumps({"api_base": "https://stored.example.com", "keys": {}})
    )
    client = BillingClient()
    assert client.api_base == "https://stored.example.com"


def test_client_init_default_api_base(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    client = BillingClient()
    assert client.api_base == "https://api.topta.co"


def test_client_init_store_with_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    store = tmp_path / ".kraken" / "keys"
    store.mkdir(parents=True)
    (store / "licenses.json").write_text(
        json.dumps({"keys": {"geo": {"key": "kk_test"}}})
    )
    client = BillingClient()
    assert client.api_base == "https://api.topta.co"


def test_client_status(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    client = BillingClient()
    store = client.status()
    assert store["keys"] == {}
    assert "api_base" in store


def test_client_set(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_LICENSE_OFFLINE", "1")
    client = BillingClient()
    result = client.set("weather-pro", "test-key")
    assert result["key"] == "test-key"
    assert result["verified"] is False


def test_client_upgrade(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setattr(
        "kraken.billing.client.upgrade",
        lambda t, plan="", email="": {"ok": True, "tentacle": t, "plan": plan},
    )
    client = BillingClient()
    result = client.upgrade("weather-pro", plan="beta", email="a@b.c")
    assert result["ok"] is True
    assert result["tentacle"] == "weather-pro"
    assert result["plan"] == "beta"


def test_client_verify_without_key_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    client = BillingClient()
    with pytest.raises(LicenseError):
        client.verify("missing")


def test_client_verify_with_key(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_LICENSE_OFFLINE", "1")
    monkeypatch.setattr(
        "kraken.billing.client.verify_remote",
        lambda t, k, b: {"ok": True, "tentacle": t},
    )
    client = BillingClient()
    client.set("weather-pro", "kk_test")
    result = client.verify("weather-pro")
    assert result["ok"] is True


def test_client_assert_premium_with_spec(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    calls = []
    monkeypatch.setattr(
        "kraken.billing.client.assert_licensed", lambda t, s: calls.append((t, s))
    )
    client = BillingClient()
    client.assert_premium("weather-pro", {"license": "premium"})
    assert calls == [("weather-pro", {"license": "premium"})]


def test_client_assert_premium_without_spec(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    calls = []
    monkeypatch.setattr(
        "kraken.billing.client.assert_licensed", lambda t, s: calls.append((t, s))
    )
    client = BillingClient()
    client.assert_premium("weather-pro")
    assert calls == [("weather-pro", None)]
