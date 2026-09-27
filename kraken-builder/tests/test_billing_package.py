import json
from pathlib import Path

from kraken.billing import BillingClient, LicenseError
from kraken.billing.hooks import after_install, on_denied
from kraken.core.license import is_premium


def test_free_spec_is_not_premium():
    assert is_premium({"license": "free"}) is False
    assert is_premium({"license": "premium"}) is True


def test_after_install_hook_free(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_BILLING_LOG", "1")
    out = after_install("geo", {"license": "free"})
    assert out["premium"] is False
    err = capsys.readouterr().err
    assert "after_install" in err
    assert "geo" in err


def test_denied_hook_logs(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_BILLING_LOG", "1")
    out = on_denied("weather-pro", "no key")
    assert out["ok"] is False
    assert "no key" in capsys.readouterr().err


def test_client_set_and_status(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_LICENSE_OFFLINE", "1")
    client = BillingClient(api_base="https://api.topta.co")
    client.set("weather-pro", "test-key")
    store = client.status()
    assert store["keys"]["weather-pro"]["key"] == "test-key"


def test_verify_without_key_raises(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    client = BillingClient()
    try:
        client.verify("missing")
        raise AssertionError("expected LicenseError")
    except LicenseError:
        pass


def test_billing_log_handler_ping():
    from pathlib import Path
    import subprocess
    import sys

    handler = (
        Path(__file__).resolve().parents[1]
        / "examples/tentacles/billing-log/handler.py"
    )
    env = dict(**__import__("os").environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    proc = subprocess.run(
        [sys.executable, str(handler)],
        input=json.dumps(
            {"v": 1, "id": "1", "action": "ping", "payload": {"target": "geo"}}
        ),
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    data = json.loads(proc.stdout)
    assert data["ok"] is True
    assert data["result"]["premium"] is False
