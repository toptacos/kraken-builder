"""Live api.topta.co auth/dashboard/security E2E.

Reads BLOG_ADMIN_EMAIL / BLOG_ADMIN_PASSWORD from the environment
(or TopTacos/toptaco-creds.env). Never prints secrets or tokens.
Skip if creds missing.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import pytest

API = os.environ.get("BLOG_API_URL") or "https://api.topta.co"
UA = "KrakenLiveE2E/1.0"


def _load_creds() -> tuple[str, str]:
    email = os.environ.get("BLOG_ADMIN_EMAIL") or ""
    password = os.environ.get("BLOG_ADMIN_PASSWORD") or ""
    creds = Path("/Users/mcachran/Projects/Companies/TopTacos/toptaco-creds.env")
    if (not email or not password) and creds.exists():
        for line in creds.read_text().splitlines():
            if line.startswith("BLOG_ADMIN_EMAIL=") and not email:
                email = line.split("=", 1)[1].strip().strip('"')
            if line.startswith("BLOG_ADMIN_PASSWORD=") and not password:
                password = line.split("=", 1)[1].strip().strip('"')
    return email, password


def _json(method: str, path: str, payload=None, token: str | None = None, timeout=20):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode()
            parsed = json.loads(body) if body else {}
            return resp.status, parsed
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {"raw": raw[:200]}
        return e.code, parsed


@pytest.fixture(scope="module")
def creds():
    email, password = _load_creds()
    if not email or not password:
        pytest.skip("BLOG_ADMIN_EMAIL/PASSWORD not available")
    return email, password


def test_security_login_wrong_password(creds):
    email, _ = creds
    status, body = _json(
        "POST", "/api/login", {"email": email, "password": "wrong-password"}
    )
    assert status in (401, 422)
    blob = json.dumps(body)
    assert "token" not in blob.lower() or body.get("token") in (None, "")


def test_security_login_sql_injection():
    status, _ = _json("POST", "/api/login", {"email": "' OR 1=1 --", "password": "x"})
    assert status in (401, 422)


def test_security_me_without_token():
    status, _ = _json("GET", "/api/me")
    assert status == 401


def test_security_admin_stats_without_token():
    status, _ = _json("GET", "/api/v1/admin/dashboard/stats")
    assert status in (401, 403)


def test_security_subscriptions_without_token():
    status, _ = _json("GET", "/api/v1/billing/subscriptions")
    assert status in (401, 403)


def test_security_xss_email_rejected():
    status, _ = _json(
        "POST",
        "/api/login",
        {"email": "<script>alert(1)</script>@x.com", "password": "x"},
    )
    assert status in (401, 422)


def test_login_me_admin_and_logout(creds):
    email, password = creds
    status, body = _json(
        "POST",
        "/api/login",
        {"email": email, "password": password, "app_name": "kraken"},
    )
    assert status == 200, "login failed (status only; no body dump)"
    token = body.get("token")
    assert token and isinstance(token, str) and len(token) > 20
    user = body.get("user") or {}
    assert user.get("email") == email

    status, me = _json("GET", "/api/me", token=token)
    assert status == 200
    me_user = me.get("data") or me.get("user") or me
    assert me_user.get("email") == email

    status, stats = _json("GET", "/api/v1/admin/dashboard/stats", token=token)
    assert status in (200, 403)
    if status == 200:
        assert isinstance(stats, dict)

    status, subs = _json("GET", "/api/v1/billing/subscriptions", token=token)
    assert status in (200, 403)

    status, plans = _json("GET", "/api/v1/billing/plans/kraken", token=token)
    assert status == 200

    status, _ = _json("POST", "/api/logout", {}, token=token)
    assert status in (200, 204)

    status, _ = _json("GET", "/api/me", token=token)
    assert status == 401
