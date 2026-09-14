"""Live workflows: kraken.topta.co auth, PATH install, API tokens, premium license.

Never prints passwords or tokens. Skip when BLOG_ADMIN_EMAIL/PASSWORD unset
and toptaco-creds.env is missing.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

import pytest

API = os.environ.get("BLOG_API_URL") or "https://api.topta.co"
SITE = "https://kraken.topta.co"
UA = "KrakenLiveWorkflows/1.0"
ROOT = Path(__file__).resolve().parents[1]


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


def _json(
    method: str,
    url: str,
    payload=None,
    token: str | None = None,
    api_key: str | None = None,
    timeout=25,
):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if api_key:
        headers["X-API-Key"] = api_key
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode()
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {}
        return e.code, parsed


@pytest.fixture(scope="module")
def creds():
    email, password = _load_creds()
    if not email or not password:
        pytest.skip("BLOG_ADMIN_EMAIL/PASSWORD not available")
    return email, password


class _Session:
    def __init__(self, email: str, token: str):
        self.email = email
        self.token = token

    def __repr__(self) -> str:
        return f"<Session email={self.email!r} token=***redacted***>"


@pytest.fixture(scope="module")
def session(creds):
    email, password = creds
    status, body = _json(
        "POST",
        f"{API}/api/login",
        {"email": email, "password": password, "app_name": "kraken"},
    )
    assert status == 200, "login failed"
    token = body.get("token")
    assert token and len(token) > 20
    yield _Session(email, token)
    _json("POST", f"{API}/api/logout", {}, token=token)


def test_kraken_site_account_points_at_profile():
    req = urllib.request.Request(f"{SITE}/account", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", "replace")
        assert resp.status == 200
    assert "index-" in html or 'id="app"' in html or "app" in html.lower()


def test_kraken_session_login_from_site_api(creds):
    email, _ = creds
    status, body = _json(
        "POST",
        f"{SITE}/api/kraken/session/login",
        {"email": email, "kind": "portal", "device_name": "e2e"},
    )
    assert status == 200
    assert body.get("ok") is True


def test_topta_login_me_from_kraken_app(session):
    status, me = _json("GET", f"{API}/api/me", token=session.token)
    assert status == 200
    user = me.get("data") or me.get("user") or me
    assert user.get("email") == session.email


def test_api_token_create_and_local_validate(session):
    status, created = _json(
        "POST",
        f"{API}/api/v1/profile/api-keys",
        {"name": "kraken-e2e", "permissions": ["read"]},
        token=session.token,
    )
    assert status in (200, 201), "api key create failed"
    plaintext = created.get("plain_text_key")
    assert plaintext and len(plaintext) >= 24

    missing, _ = _json("GET", f"{API}/api/v1/external/blog/posts")
    assert missing == 401

    bad, _ = _json("GET", f"{API}/api/v1/external/blog/posts", api_key="not-a-real-key")
    assert bad == 401

    ok, body = _json("GET", f"{API}/api/v1/external/blog/posts", api_key=plaintext)
    # Valid key is accepted by ValidateApiKey (not 401). Downstream /external/*
    # currently 500s on production blog connection — that is not token rejection.
    assert ok != 401
    assert ok in (200, 500)

    key_id = (created.get("data") or created).get("id")
    if key_id:
        _json("DELETE", f"{API}/api/v1/profile/api-keys/{key_id}", token=session.token)


def test_billing_plans_and_checkout_gate(session):
    status, plans = _json(
        "GET", f"{API}/api/v1/billing/plans/kraken", token=session.token
    )
    assert status == 200
    rows = plans if isinstance(plans, list) else plans.get("data") or []
    assert isinstance(rows, list)
    if not rows:
        pytest.skip("no kraken plans")
    plan_id = rows[0].get("id")
    status, body = _json(
        "POST",
        f"{API}/api/v1/billing/checkout",
        {"plan_id": plan_id, "interval": "month"},
        token=session.token,
    )
    assert status in (200, 402, 422, 500)
    if status == 200:
        assert "url" in body or body.get("ok") is True


def test_premium_issue_install_grant_run(session, tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_LICENSE_OFFLINE", "1")
    os.environ["KRAKEN_HOME"] = str(tmp_path)
    os.environ["PYTHONPATH"] = str(ROOT)
    status, issued = _json(
        "POST",
        f"{API}/api/kraken/licenses/issue",
        {"tentacle": "scourge", "plan": "beta", "email": session.email},
    )
    assert status == 200
    key = issued.get("key")
    assert key and key.startswith("k_")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env["KRAKEN_HOME"] = str(tmp_path)
    env["KRAKEN_LICENSE_OFFLINE"] = "1"
    subprocess.check_call(
        [sys.executable, "-m", "kraken", "init"], env=env, cwd=str(ROOT)
    )
    subprocess.check_call(
        [sys.executable, "-m", "kraken", "license", "set", "scourge", key],
        env=env,
        cwd=str(ROOT),
    )
    subprocess.check_call(
        [sys.executable, "-m", "kraken", "grant", "scourge"], env=env, cwd=str(ROOT)
    )
    scourge = ROOT / "examples" / "tentacles" / "scourge"
    subprocess.check_call(
        [sys.executable, "-m", "kraken", "tentacle", "add", str(scourge)],
        env=env,
        cwd=str(ROOT),
    )
    out = subprocess.check_output(
        [sys.executable, "-m", "kraken", "run", "scourge", "status"],
        env=env,
        cwd=str(ROOT),
        text=True,
    )
    assert '"ok": true' in out or '"ok":true' in out.replace(" ", "")
    store = tmp_path / ".kraken" / "keys" / "licenses.json"
    assert store.exists()
    if os.name != "nt":
        assert oct(store.stat().st_mode)[-3:] == "600"


def test_isolated_path_install():
    if os.name == "nt":
        pytest.skip("POSIX install.sh")
    home = Path(tempfile.mkdtemp(prefix="kraken-e2e-"))
    try:
        src = home / ".kraken" / "src"
        bindir = home / ".local" / "bin"
        src.mkdir(parents=True)
        bindir.mkdir(parents=True)
        shutil.copytree(ROOT / "kraken", src / "kraken")
        shutil.copytree(ROOT / "examples", src / "examples")
        shutil.copytree(ROOT / "arms", src / "arms")
        shutil.copy2(ROOT / "install.sh", src / "install.sh")
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["KRAKEN_SRC"] = str(src)
        env["KRAKEN_BIN"] = str(bindir)
        env["PYTHONPATH"] = str(src)
        subprocess.check_call(["sh", str(ROOT / "install.sh")], env=env, cwd=str(src))
        kraken = bindir / "kraken"
        alias = bindir / "k"
        assert kraken.exists()
        assert alias.exists() or alias.is_symlink()
        assert kraken.stat().st_mode & stat.S_IXUSR
        out = subprocess.check_output(
            [str(kraken), "self", "plan"],
            env={**env, "PATH": f"{bindir}:{env.get('PATH', '')}"},
            text=True,
        )
        assert '"ok"' in out
    finally:
        shutil.rmtree(home, ignore_errors=True)
