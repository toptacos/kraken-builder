"""The CLI↔API license contract: 200 = seat, 402 = buy a seat.

Runs against a loopback stub so the suite stays offline, and asserts the two
statuses the CLI can actually act on. A 403 or 404 from the API would be
indistinguishable from a broken endpoint, so both are treated as failures here.
"""

from __future__ import annotations

import http.server
import json
import threading
from pathlib import Path

import pytest

from kraken.core.license import LicenseError, verify_remote

ROOT = Path(__file__).resolve().parents[1]

#: The API answers only these two for a well-formed verify request.
CONTRACT_STATUSES = {200, 402}


class _Handler(http.server.BaseHTTPRequestHandler):
    """Serves the status the test asked for via a class attribute."""

    status = 402
    body: dict = {}

    def do_POST(self) -> None:  # noqa: N802 — stdlib naming
        length = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(length)
        payload = json.dumps(type(self).body).encode()
        self.send_response(type(self).status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args) -> None:
        pass


@pytest.fixture
def api():
    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


def _set(status: int, body: dict) -> None:
    _Handler.status = status
    _Handler.body = body


def test_200_returns_the_seat(api):
    _set(200, {"ok": True, "tentacle": "taco", "expires_at": "2027-01-01T00:00:00Z"})
    out = verify_remote("taco", "k_live", api_base=api)
    assert out["ok"] is True
    assert out["tentacle"] == "taco"


def test_402_raises_an_actionable_error(api):
    _set(
        402,
        {
            "ok": False,
            "error": {"code": "payment_required", "message": "license expired"},
        },
    )
    with pytest.raises(LicenseError) as exc:
        verify_remote("taco", "k_lapsed", api_base=api)
    message = str(exc.value)
    assert "paid seat" in message
    assert "license expired" in message
    assert "kraken.topta.co/pricing" in message


def test_402_without_a_json_body_still_guides_the_user(api):
    _set(402, {})
    with pytest.raises(LicenseError) as exc:
        verify_remote("taco", "k_nobody", api_base=api)
    assert "kraken.topta.co/pricing" in str(exc.value)


def test_unexpected_status_is_not_mistaken_for_a_billing_problem(api):
    """A 500 is a broken API, not a sales problem. It must read differently."""
    _set(500, {"ok": False})
    with pytest.raises(LicenseError) as exc:
        verify_remote("taco", "k_live", api_base=api)
    assert "paid seat" not in str(exc.value)


def test_unreachable_api_names_the_host(api):
    """A closed port, not a bad path — the stub answers every path."""
    import socket

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    dead_port = sock.getsockname()[1]
    sock.close()

    with pytest.raises(LicenseError) as exc:
        verify_remote("taco", "k_live", api_base=f"http://127.0.0.1:{dead_port}")
    assert "unreachable" in str(exc.value)


def test_200_with_ok_false_is_still_a_rejection(api):
    _set(200, {"ok": False, "error": {"message": "nope"}})
    with pytest.raises(LicenseError):
        verify_remote("taco", "k_weird", api_base=api)


def test_default_api_base_is_the_hub():
    from kraken.core.license import DEFAULT_API

    assert DEFAULT_API == "https://api.topta.co"


def test_ping_and_help_stay_free_of_the_license_gate():
    """Premium gating must never block the free verbs."""
    from kraken.core.license import is_premium

    assert is_premium({"license": "free"}) is False
    assert is_premium({"license": "premium"}) is True
    assert is_premium({}) is False
