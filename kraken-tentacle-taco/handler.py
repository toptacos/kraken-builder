#!/usr/bin/env python3
"""taco — premium local gamification. Inbound events, no vendor crawl."""
from __future__ import annotations

import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from connectors import parse as parse_channel  # noqa: E402

VERSION = "0.1.0"
PROTOCOL = 1
DENIED = ("/keys", "keys/", "licenses.json", "kraken_catalog", "catalog.json")
KINDS = {"pr", "loc", "security", "taco", "custom"}
GATED = {
    "init", "after_install", "oauth", "host", "set-policy",
    "event", "ingest", "give", "redeem", "clear",
}

DEFAULT_POLICY = {
    "org": "local",
    "unit": "taco",
    "checks": {
        "pr": {"tacos": 3, "note": "merged pull request"},
        "loc": {"tacos": 1, "per": 100, "note": "net lines accepted"},
        "security": {"tacos": 8, "note": "security issue closed"},
        "taco": {"tacos": 1, "note": "peer grant, cap 5/day"},
        "custom": {"tacos": 0, "note": "instance-defined"},
    },
    "peer_cap_per_day": 5,
    "limits": {
        "taco": {"per_hour": 3, "per_day": 5},
        "pr": {"per_day": 20},
        "loc": {"per_day": 50},
        "security": {"per_day": 20},
        "custom": {"per_day": 20},
    },
    "rules": [
        {"id": "deny_self", "type": "deny_self"},
        {"id": "kinds", "type": "allow_kinds", "kinds": ["pr", "loc", "security", "taco", "custom"]},
    ],
    "rewards": [
        {"id": "sticker", "cost": 10, "title": "sticker pack"},
        {"id": "lunch", "cost": 40, "title": "team lunch credit"},
    ],
    "channels": ["local"],
    "hosting": {"mode": "local", "anon": True, "url": ""},
}


def ok(ident, result):
    return {"v": PROTOCOL, "id": ident, "ok": True, "result": result}


def err(ident, code, message):
    return {"v": PROTOCOL, "id": ident, "ok": False, "error": {"code": code, "message": message}}


def data_dir(payload: dict) -> Path:
    if payload.get("dir"):
        p = Path(str(payload["dir"]))
    else:
        h = os.environ.get("KRAKEN_HOME") or str(Path.home())
        p = Path(h) / ".kraken" / "data" / "taco"
    text = str(p).replace("\\", "/").lower()
    if any(d in text for d in DENIED):
        raise PermissionError("forbidden path")
    p.mkdir(parents=True, exist_ok=True)
    return p


def store_path(payload: dict) -> Path:
    return data_dir(payload) / "ledger.json"


def load(payload: dict) -> dict:
    p = store_path(payload)
    if not p.exists():
        return {"policy": json.loads(json.dumps(DEFAULT_POLICY)), "users": {}, "events": [], "redemptions": []}
    return json.loads(p.read_text(encoding="utf-8"))


def save(st: dict, payload: dict) -> None:
    p = store_path(payload)
    p.write_text(json.dumps(st, indent=2), encoding="utf-8")
    os.chmod(p, 0o600)


def user_row(st: dict, name: str) -> dict:
    if name not in st["users"]:
        st["users"][name] = {"name": name, "tacos": 0, "given_today": 0, "day": ""}
    return st["users"][name]


def _parse_at(raw: str) -> datetime | None:
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def _limit_block(st: dict, kind: str) -> dict:
    limits = st["policy"].get("limits") or {}
    block = dict(limits.get(kind) or {})
    if kind == "taco" and st["policy"].get("peer_cap_per_day") is not None:
        block["per_day"] = int(st["policy"]["peer_cap_per_day"])
    return block


def _count_kind(st: dict, *, kind: str, actor: str | None, since: datetime) -> int:
    n = 0
    for ev in st.get("events") or []:
        if ev.get("kind") != kind:
            continue
        at = _parse_at(str(ev.get("at") or ""))
        if at is None or at < since:
            continue
        if actor and ev.get("note", "").startswith("from:"):
            if ev.get("note") != f"from:{actor}":
                continue
        elif actor and ev.get("user") != actor:
            continue
        n += 1
    return n


def enforce(st: dict, *, kind: str, user: str, actor: str | None = None) -> str | None:
    now = datetime.now(timezone.utc)
    block = _limit_block(st, kind)
    who = actor or user
    if block.get("per_hour") is not None:
        if _count_kind(st, kind=kind, actor=who if kind == "taco" else user, since=now.replace(minute=0, second=0, microsecond=0)) >= int(block["per_hour"]):
            return "per_hour"
    if block.get("per_day") is not None:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if _count_kind(st, kind=kind, actor=who if kind == "taco" else user, since=start) >= int(block["per_day"]):
            return "per_day"
    for rule in st["policy"].get("rules") or []:
        rtype = rule.get("type")
        if rtype == "deny_self" and actor and actor == user:
            return "deny_self"
        if rtype == "allow_kinds":
            allowed = {str(x) for x in (rule.get("kinds") or [])}
            if allowed and kind not in allowed:
                return "kind_denied"
        if rtype == "hour_window":
            start = int(rule.get("start") or 0)
            end = int(rule.get("end") or 24)
            hour = now.hour
            if not (start <= hour < end):
                return "hour_window"
    return None


def award(st: dict, user: str, kind: str, amount: int | None, note: str) -> dict:
    policy = st["policy"]["checks"].get(kind) or st["policy"]["checks"]["custom"]
    tacos = amount if amount is not None else int(policy.get("tacos") or 0)
    if tacos < 0:
        tacos = 0
    clean = (note or "")[:200]
    lowered = clean.lower()
    if any(tok in lowered for tok in ("token=", "secret=", "bearer ", "sk-", "xoxb-", "ghp_")):
        clean = "redacted"
    row = user_row(st, user)
    row["tacos"] += tacos
    ev = {
        "at": datetime.now(timezone.utc).isoformat(),
        "user": user,
        "kind": kind,
        "tacos": tacos,
        "note": clean,
    }
    st["events"].append(ev)
    return ev


def licensed(payload: dict) -> bool:
    if (os.environ.get("KRAKEN_LICENSE") or "").lower() in {"premium", "1", "true"}:
        return True
    if str(payload.get("license") or "").lower() == "premium":
        return True
    home = Path(os.environ.get("KRAKEN_HOME") or Path.home())
    for candidate in (
        home / ".kraken" / "license" / "taco.json",
        home / ".kraken" / "license.json",
    ):
        if candidate.exists():
            try:
                body = json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if str(body.get("license") or body.get("tier") or "").lower() == "premium":
                return True
    return False


def dispatch(req: dict) -> dict:
    action = req.get("action") or "ping"
    ident = req.get("id")
    p = req.get("payload") or {}
    if action in GATED and not licensed(p):
        return err(ident, "payment_required", "402 premium license required — https://kraken.topta.co/pricing")
    if action in ("", "ping"):
        return ok(ident, {
            "arm": "taco", "version": VERSION, "protocol": PROTOCOL,
            "license": "premium",
            "brand": "TopTaco",
            "site": "https://kraken.topta.co",
            "api": "https://api.topta.co",
            "tagline": "One binary. Many tentacles.",
            "platform": f"{sys.platform}-{platform.machine()}",
            "pulls_vendors": False,
            "init": True,
        })
    if action in ("init", "after_install"):
        try:
            st = load(p)
        except PermissionError as exc:
            return err(ident, "forbidden", str(exc))
        answers = p.get("answers") or {}
        prompts = [
            {"key": "org", "label": "Organization name", "default": st["policy"].get("org") or "local"},
            {"key": "peer_cap_per_day", "label": "Peer tacos per day", "default": st["policy"].get("peer_cap_per_day") or 5},
            {"key": "per_hour", "label": "Peer tacos per hour", "default": (st["policy"].get("limits") or {}).get("taco", {}).get("per_hour") or 3},
            {"key": "channels", "label": "Inbound bots (comma: slack,gchat,teams)", "default": "slack,gchat,teams"},
        ]
        if not answers and not p.get("defaults"):
            return ok(ident, {
                "arm": "taco",
                "hook": action,
                "interactive": True,
                "prompts": prompts,
                "note": "kraken taco init — reply with payload.answers",
            })
        if p.get("defaults"):
            answers = {item["key"]: item["default"] for item in prompts}
        if "org" in answers:
            st["policy"]["org"] = str(answers["org"])
        if "peer_cap_per_day" in answers:
            try:
                st["policy"]["peer_cap_per_day"] = int(answers["peer_cap_per_day"])
                st["policy"].setdefault("limits", {}).setdefault("taco", {})["per_day"] = int(answers["peer_cap_per_day"])
            except (TypeError, ValueError):
                pass
        if "per_hour" in answers:
            try:
                st["policy"].setdefault("limits", {}).setdefault("taco", {})["per_hour"] = int(answers["per_hour"])
            except (TypeError, ValueError):
                pass
        if "channels" in answers:
            raw = answers["channels"]
            if isinstance(raw, str):
                st["policy"]["channels"] = [c.strip() for c in raw.split(",") if c.strip()]
            elif isinstance(raw, list):
                st["policy"]["channels"] = raw
        save(st, p)
        return ok(ident, {"arm": "taco", "hook": action, "configured": True, "policy": st["policy"], "interactive": False})
    if action == "oauth":
        try:
            st = load(p)
        except PermissionError as exc:
            return err(ident, "forbidden", str(exc))
        vendor = (p.get("vendor") or "").lower()
        urls = {
            "slack": "https://api.slack.com/apps",
            "gchat": "https://console.cloud.google.com/apis/api/chat.googleapis.com",
            "googlechat": "https://console.cloud.google.com/apis/api/chat.googleapis.com",
            "teams": "https://dev.teams.microsoft.com",
        }
        if vendor not in urls:
            return err(ident, "bad_vendor", "slack, gchat, or teams")
        if p.get("secret") or p.get("client_secret"):
            return err(ident, "forbidden", "do not store client secrets in taco; use keeps")
        apps = st.setdefault("oauth", {})
        rec = {"vendor": vendor, "client_id": p.get("client_id") or "", "url": urls[vendor]}
        apps[vendor] = rec
        save(st, p)
        return ok(ident, {"arm": "taco", "oauth": rec, "bot": f"python3 bots/loopback.py {vendor} 7421"})
    if action in ("help", "usage"):
        return ok(ident, {
            "arm": "taco",
            "site": "https://kraken.topta.co",
            "commands": {
                "init": "interactive setup",
                "give": "/kraken taco @user via payload.from/to",
                "event": "inbound pr|loc|security|custom",
                "ingest": "channel + vendor JSON",
                "score": "board or one user",
                "redeem": "debit a catalog reward",
                "host": "local | toptaco | third",
            },
            "chat": ["/kraken taco @user", "/tt taco @user"],
        })
    if action == "finish":
        raw = dict(p.get("raw") or {"arm": "taco"})
        raw.update(p.get("patch") or {})
        raw["finished"] = True
        raw.pop("token", None)
        raw.pop("secret", None)
        return ok(ident, raw)
    try:
        st = load(p)
    except PermissionError as exc:
        return err(ident, "forbidden", str(exc))

    if action == "policy":
        return ok(ident, {"arm": "taco", "license": "premium", "policy": st["policy"]})

    if action == "set-policy":
        incoming = p.get("policy") or {}
        if not isinstance(incoming, dict):
            return err(ident, "bad_policy", "policy must be an object")
        merged = st["policy"]
        for key in ("org", "unit", "peer_cap_per_day", "rewards", "channels", "checks", "hosting", "limits", "rules"):
            if key in incoming:
                merged[key] = incoming[key]
        st["policy"] = merged
        save(st, p)
        return ok(ident, {"arm": "taco", "policy": st["policy"]})

    if action == "ingest":
        channel = (p.get("channel") or "").lower()
        body = p.get("payload") or p.get("body") or {}
        if not isinstance(body, dict):
            return err(ident, "bad_payload", "payload must be an object")
        mapped = parse_channel(channel, body)
        if not mapped:
            return err(ident, "unmapped", f"no taco event for channel {channel}")
        if mapped.get("kind") == "taco" and mapped.get("from") and mapped.get("to"):
            blocked = enforce(st, kind="taco", user=mapped["to"], actor=mapped["from"])
            if blocked:
                return err(ident, "cap", blocked)
            ev = award(st, mapped["to"], "taco", 1, f"from:{mapped['from']}")
            save(st, p)
            return ok(ident, {"arm": "taco", "channel": channel, "event": ev})
        user = (mapped.get("user") or "").strip()
        if not user:
            return err(ident, "missing", "connector did not yield a user")
        kind = mapped.get("kind") or "custom"
        blocked = enforce(st, kind=kind, user=user)
        if blocked:
            return err(ident, "cap", blocked)
        ev = award(st, user, kind, mapped.get("tacos"), mapped.get("note") or channel)
        save(st, p)
        return ok(ident, {"arm": "taco", "channel": channel, "event": ev, "balance": st["users"][user]["tacos"]})

    if action == "event":
        kind = p.get("kind") or "custom"
        if kind not in KINDS:
            return err(ident, "bad_kind", f"kind must be one of {sorted(KINDS)}")
        user = (p.get("user") or "").strip()
        if not user:
            return err(ident, "missing", "user required")
        blocked = enforce(st, kind=kind, user=user)
        if blocked:
            return err(ident, "cap", blocked)
        ev = award(st, user, kind, p.get("tacos"), p.get("note") or kind)
        save(st, p)
        return ok(ident, {"arm": "taco", "event": ev, "balance": st["users"][user]["tacos"]})

    if action == "give":
        src = (p.get("from") or "").strip()
        dst = (p.get("to") or "").strip()
        if not src or not dst or src == dst:
            return err(ident, "bad_give", "from and to required and distinct")
        blocked = enforce(st, kind="taco", user=dst, actor=src)
        if blocked:
            return err(ident, "cap", blocked)
        ev = award(st, dst, "taco", 1, f"from:{src}")
        save(st, p)
        return ok(ident, {"arm": "taco", "event": ev, "from": src, "to": dst})

    if action == "score":
        user = p.get("user")
        if user:
            row = st["users"].get(user) or {"name": user, "tacos": 0}
            return ok(ident, {"arm": "taco", "user": row})
        board = sorted(st["users"].values(), key=lambda r: (-r.get("tacos", 0), r.get("name", "")))
        return ok(ident, {"arm": "taco", "board": board})

    if action == "host":
        mode = (p.get("mode") or st["policy"].get("hosting", {}).get("mode") or "local").lower()
        if mode == "topta":
            mode = "toptaco"
        if mode not in {"local", "toptaco", "third"}:
            return err(ident, "bad_host", "mode must be local, toptaco, or third")
        url = p.get("url") or ""
        if mode == "third" and not str(url).startswith("https://"):
            return err(ident, "bad_host", "third party host must be https")
        hosting = {"mode": mode, "anon": bool(p.get("anon", True)), "url": url if mode == "third" else ""}
        st["policy"]["hosting"] = hosting
        save(st, p)
        return ok(ident, {
            "arm": "taco",
            "hosting": hosting,
            "pushed": False,
            "note": "local ledger is source of truth; remote is a later copy",
        })

    if action == "catalog":
        return ok(ident, {"arm": "taco", "rewards": st["policy"].get("rewards") or []})

    if action == "redeem":
        user = (p.get("user") or "").strip()
        rid = p.get("id")
        reward = next((r for r in st["policy"].get("rewards") or [] if r.get("id") == rid), None)
        if not user or not reward:
            return err(ident, "missing", "user and valid reward id required")
        row = user_row(st, user)
        cost = int(reward.get("cost") or 0)
        if row["tacos"] < cost:
            return err(ident, "broke", "not enough tacos")
        row["tacos"] -= cost
        rec = {"user": user, "id": rid, "cost": cost, "at": datetime.now(timezone.utc).isoformat()}
        st["redemptions"].append(rec)
        save(st, p)
        return ok(ident, {"arm": "taco", "redeemed": rec, "balance": row["tacos"]})

    if action == "clear":
        save({"policy": json.loads(json.dumps(DEFAULT_POLICY)), "users": {}, "events": [], "redemptions": []}, p)
        return ok(ident, {"cleared": True})

    return err(ident, "unknown_action", f"unknown action {action}")


def main() -> int:
    raw = sys.stdin.read()
    req = json.loads(raw) if raw.strip() else {"action": "ping"}
    json.dump(dispatch(req), sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
