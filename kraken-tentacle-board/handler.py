#!/usr/bin/env python3
"""board tentacle. Project dashboard + local Jev/Ollama. No kraken.core import."""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

VERSION = "0.1.0"
PROTOCOL = 1


def home_root() -> Path:
    h = os.environ.get("KRAKEN_HOME") or str(Path.home())
    return Path(h) / ".kraken" / "data" / "board"


def find_project(start: Path | None = None) -> Path:
    cur = (start or Path(os.environ.get("KRAKEN_BOARD_ROOT") or Path.cwd())).resolve()
    for p in [cur, *cur.parents]:
        if (p / ".kraken" / "board.yaml").exists() or (p / "board.yaml").exists():
            return p
        if (p / ".git").exists():
            return p
    return cur


def config_path(root: Path) -> Path:
    a = root / ".kraken" / "board.yaml"
    b = root / "board.yaml"
    return a if a.exists() else b


def load_config(root: Path) -> dict[str, Any]:
    path = config_path(root)
    if not path.exists():
        return default_config(root)
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(text) or {}
    except Exception:
        data = json.loads(text) if text.strip().startswith("{") else {}
    if not isinstance(data, dict):
        data = {}
    base = default_config(root)
    base.update({k: v for k, v in data.items() if v is not None})
    if "panels" in data:
        base["panels"] = data["panels"]
    return base


def default_config(root: Path) -> dict[str, Any]:
    return {
        "name": root.name,
        "root": str(root),
        "ai": {
            "backend": os.environ.get("KRAKEN_BOARD_BACKEND") or "ollama",
            "model": os.environ.get("KRAKEN_BOARD_MODEL") or "llama3.2",
            "ollama_url": os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434",
            "llamacpp_url": os.environ.get("LLAMACPP_URL") or "http://127.0.0.1:8080",
            "jev": True,
            "offline": os.environ.get("KRAKEN_OFFLINE") == "1",
        },
        "panels": [
            {"id": "repo", "kind": "repo", "title": "repository"},
            {"id": "project", "kind": "project", "title": "project"},
            {"id": "ai", "kind": "ai", "title": "ai / jev"},
            {"id": "term", "kind": "terminal", "title": "terminal"},
        ],
    }


def ok(result: Any, ident: Any = None) -> dict:
    return {"v": PROTOCOL, "id": ident, "ok": True, "result": result}


def err(code: str, message: str, ident: Any = None) -> dict:
    return {"v": PROTOCOL, "id": ident, "ok": False, "error": {"code": code, "message": message}}


def git(root: Path, *args: str) -> tuple[int, str]:
    if not shutil.which("git"):
        return 127, "git not installed"
    proc = subprocess.run(
        ["git", *args],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    out = (proc.stdout or proc.stderr or "").strip()
    return proc.returncode, out


def panel_repo(root: Path) -> dict[str, Any]:
    code, branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    _, sha = git(root, "rev-parse", "--short", "HEAD")
    _, status = git(root, "status", "--porcelain")
    _, ahead = git(root, "status", "-sb")
    dirty = [ln for ln in status.splitlines() if ln.strip()]
    return {
        "kind": "repo",
        "branch": branch if code == 0 else None,
        "sha": sha if sha and code == 0 else None,
        "dirty": len(dirty),
        "files": dirty[:20],
        "short": ahead.splitlines()[0] if ahead else "",
        "git": code == 0,
    }


def panel_project(root: Path, cfg: dict[str, Any]) -> dict[str, Any]:
    markers = []
    for name in (
        "go.mod", "package.json", "pyproject.toml", "Cargo.toml",
        "Makefile", "Dockerfile", "tentacle.yaml", "composer.json",
    ):
        if (root / name).exists():
            markers.append(name)
    return {
        "kind": "project",
        "name": cfg.get("name") or root.name,
        "root": str(root),
        "markers": markers,
        "config": str(config_path(root)) if config_path(root).exists() else None,
    }


def which_ai() -> dict[str, Any]:
    ollama = bool(shutil.which("ollama"))
    llama = bool(shutil.which("llama-server") or shutil.which("llama-cli"))
    jev_bin = bool(shutil.which("jev"))
    jev_tentacle = bool(shutil.which("kraken"))
    return {
        "ollama": ollama,
        "llamacpp": llama,
        "jev_bin": jev_bin,
        "jev_tentacle": jev_tentacle,
        "offline": os.environ.get("KRAKEN_OFFLINE") == "1",
    }


def loopback_url(url: str) -> None:
    u = urllib.parse.urlparse(url)
    host = (u.hostname or "").lower()
    if u.scheme not in ("http", "https") or host not in ("127.0.0.1", "localhost", "::1"):
        raise PermissionError(f"ai url must be loopback, got {url}")


def http_json(url: str, body: dict | None = None, timeout: float = 8.0) -> dict[str, Any]:
    loopback_url(url)
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="GET" if body is None else "POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode() or "{}"
    return json.loads(raw)


def jev_get(data: Any, path: str) -> Any:
    cur = data
    if not path:
        return cur
    for part in path.strip(".").split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list) and part.isdigit():
            cur = cur[int(part)]
        else:
            return None
    return cur


def jev_set(data: Any, path: str, value: Any) -> Any:
    if not path:
        return value
    parts = path.strip(".").split(".")
    cur = data
    if not isinstance(cur, dict):
        cur = {}
        data = cur
    for part in parts[:-1]:
        nxt = cur.get(part) if isinstance(cur, dict) else None
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value
    return data


def jev_delete(data: Any, path: str) -> Any:
    parts = path.strip(".").split(".")
    cur = data
    for part in parts[:-1]:
        if not isinstance(cur, dict):
            return data
        cur = cur.get(part)
    if isinstance(cur, dict):
        cur.pop(parts[-1], None)
    return data


def jev_merge(data: Any, path: str, value: Any) -> Any:
    existing = jev_get(data, path)
    if isinstance(existing, dict) and isinstance(value, dict):
        merged = {**existing, **value}
        return jev_set(data, path, merged)
    return jev_set(data, path, value)


def apply_ops(data: Any, operations: list) -> Any:
    for op in operations or []:
        kind = (op.get("op") or op.get("action") or "get").lower()
        path = op.get("path") or ""
        if kind == "set":
            data = jev_set(data, path, op.get("value"))
        elif kind == "delete":
            data = jev_delete(data, path)
        elif kind == "merge":
            data = jev_merge(data, path, op.get("value") or {})
        elif kind == "get":
            op["_got"] = jev_get(data, path)
    return data


def call_jev_ai(action: str, payload: dict) -> dict[str, Any] | None:
    if not shutil.which("kraken"):
        return None
    req = json.dumps({"v": 1, "action": action, "payload": payload})
    proc = subprocess.run(
        ["kraken", "run", "jev-ai", action, "--payload", json.dumps(payload)],
        input=req,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    lines = [ln for ln in (proc.stdout or "").splitlines() if ln.startswith("{")]
    if not lines:
        return None
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return None


def infer_local(cfg: dict[str, Any], prompt: str) -> dict[str, Any]:
    ai = cfg.get("ai") or {}
    if ai.get("offline") or os.environ.get("KRAKEN_OFFLINE") == "1":
        return {
            "backend": "fixture",
            "model": ai.get("model"),
            "text": f"[offline] would analyze: {prompt[:200]}",
            "live": False,
        }
    backend = (ai.get("backend") or "ollama").lower()
    model = ai.get("model") or "llama3.2"
    if backend in ("jev-ai", "jev"):
        remote = call_jev_ai("infer", {"prompt": prompt, "model": model, "backend": "ollama"})
        if remote and remote.get("ok"):
            return {"backend": "jev-ai", "live": True, "raw": remote.get("result")}
    if backend == "llamacpp":
        try:
            body = http_json(
                (ai.get("llamacpp_url") or "http://127.0.0.1:8080").rstrip("/") + "/completion",
                {"prompt": prompt, "n_predict": 128, "temperature": 0.2},
            )
            return {"backend": "llamacpp", "live": True, "text": body.get("content") or body}
        except Exception as exc:
            return {"backend": "llamacpp", "live": False, "error": str(exc)}
    try:
        url = (ai.get("ollama_url") or "http://127.0.0.1:11434").rstrip("/") + "/api/generate"
        body = http_json(url, {"model": model, "prompt": prompt, "stream": False})
        return {"backend": "ollama", "model": model, "live": True, "text": body.get("response")}
    except Exception as exc:
        return {"backend": "ollama", "live": False, "error": str(exc), "text": f"[local fallback] {prompt[:160]}"}


def panel_ai(cfg: dict[str, Any]) -> dict[str, Any]:
    avail = which_ai()
    return {"kind": "ai", "available": avail, "config": cfg.get("ai") or {}}


def panel_term(root: Path) -> dict[str, Any]:
    return {
        "kind": "terminal",
        "cwd": str(root),
        "shell": os.environ.get("SHELL") or ("cmd.exe" if os.name == "nt" else "/bin/sh"),
        "hint": "board does not spawn a PTY; use your outer shell. snapshot only.",
    }


def collect(root: Path, cfg: dict[str, Any]) -> dict[str, Any]:
    panels = []
    for spec in cfg.get("panels") or default_config(root)["panels"]:
        kind = (spec.get("kind") or spec.get("id") or "").lower()
        if kind == "repo":
            body = panel_repo(root)
        elif kind == "project":
            body = panel_project(root, cfg)
        elif kind in ("ai", "jev"):
            body = panel_ai(cfg)
        elif kind in ("term", "terminal"):
            body = panel_term(root)
        else:
            body = {"kind": kind, "note": "unknown panel"}
        body["id"] = spec.get("id") or kind
        body["title"] = spec.get("title") or body["id"]
        panels.append(body)
    return {
        "arm": "board",
        "name": cfg.get("name"),
        "root": str(root),
        "config": str(config_path(root)) if config_path(root).exists() else None,
        "panels": panels,
    }


def box(title: str, lines: list[str], width: int = 34) -> list[str]:
    title = title[: width - 4]
    top = "┌─ " + title + " " + "─" * max(1, width - len(title) - 4) + "┐"
    bot = "└" + "─" * width + "┘"
    out = [top]
    for ln in lines[:8]:
        s = ln[:width]
        out.append("│" + s.ljust(width) + "│")
    while len(out) < 10:
        out.append("│" + " " * width + "│")
    out.append(bot)
    return out


def render(snap: dict[str, Any]) -> str:
    cols: list[list[str]] = []
    for p in snap.get("panels") or []:
        kind = p.get("kind")
        if kind == "repo":
            lines = [
                f"branch {p.get('branch') or '-'}",
                f"sha    {p.get('sha') or '-'}",
                f"dirty  {p.get('dirty')}",
                (p.get("short") or "")[:32],
            ]
        elif kind == "project":
            lines = [str(p.get("name")), " ".join(p.get("markers") or [])[:32], str(p.get("root"))[-32:]]
        elif kind == "ai":
            av = p.get("available") or {}
            lines = [
                f"ollama {av.get('ollama')}",
                f"llama  {av.get('llamacpp')}",
                f"jev    {av.get('jev_bin')}",
                f"offline {av.get('offline')}",
            ]
        elif kind == "terminal":
            lines = [str(p.get("cwd"))[-32:], str(p.get("shell"))]
        else:
            lines = [json.dumps(p)[:32]]
        cols.append(box(str(p.get("title") or kind), lines))
    if not cols:
        return "(no panels)"
    height = max(len(c) for c in cols)
    rows = []
    header = f" board · {snap.get('name')} "
    rows.append(header)
    for i in range(height):
        rows.append(" ".join(c[i] if i < len(c) else " " * 36 for c in cols))
    return "\n".join(rows)


def write_init(root: Path) -> Path:
    dest = root / ".kraken" / "board.yaml"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return dest
    dest.write_text(
        f"""# board dashboard — project-local
name: {root.name}
ai:
  backend: ollama          # ollama | llamacpp | jev-ai
  model: llama3.2
  jev: true
panels:
  - id: repo
    kind: repo
    title: repository
  - id: project
    kind: project
    title: project
  - id: ai
    kind: ai
    title: ai / jev
  - id: term
    kind: terminal
    title: terminal
""",
        encoding="utf-8",
    )
    return dest


def analyze_prompt(root: Path, snap: dict[str, Any], question: str) -> str:
    repo = next((p for p in snap.get("panels") or [] if p.get("kind") == "repo"), {})
    proj = next((p for p in snap.get("panels") or [] if p.get("kind") == "project"), {})
    return (
        "You are a local project analyst. Open source stack only.\n"
        f"Project: {proj.get('name')} at {root}\n"
        f"Markers: {proj.get('markers')}\n"
        f"Git: {repo.get('short')} dirty={repo.get('dirty')} files={repo.get('files')}\n"
        f"Question: {question or 'Summarize health and safest next edit.'}\n"
        "Reply in short bullets."
    )


def dispatch(req: dict) -> dict:
    action = req.get("action") or "ping"
    payload = req.get("payload") or {}
    ident = req.get("id")
    start = Path(payload.get("root") or os.environ.get("KRAKEN_BOARD_ROOT") or Path.cwd())
    root = find_project(start)
    cfg = load_config(root)
    if action == "ping":
        return ok({
            "arm": "board",
            "version": VERSION,
            "protocol": PROTOCOL,
            "platform": f"{sys.platform}-{platform.machine()}",
            "root": str(root),
        }, ident)
    if action == "init":
        path = write_init(root)
        return ok({"arm": "board", "wrote": str(path), "root": str(root)}, ident)
    if action in ("status", "snapshot", "layout"):
        snap = collect(root, cfg)
        if action == "layout":
            snap["frame"] = render(snap)
        return ok(snap, ident)
    if action == "repo":
        return ok({"arm": "board", **panel_repo(root)}, ident)
    if action == "project":
        return ok({"arm": "board", **panel_project(root, cfg)}, ident)
    if action == "open":
        snap = collect(root, cfg)
        frame = render(snap)
        return ok({**snap, "frame": frame, "interactive": False}, ident)
    if action == "ai":
        prompt = payload.get("prompt") or payload.get("q") or "status"
        result = infer_local(cfg, str(prompt))
        return ok({"arm": "board", "ai": result, "available": which_ai()}, ident)
    if action == "analyze":
        snap = collect(root, cfg)
        prompt = analyze_prompt(root, snap, str(payload.get("prompt") or payload.get("q") or ""))
        result = infer_local(cfg, prompt)
        return ok({"arm": "board", "analysis": result, "snapshot": snap}, ident)
    if action == "apply":
        grant = root / ".kraken" / "grants" / "apply"
        if os.environ.get("KRAKEN_BOARD_APPLY") != "1" and not grant.exists():
            return err("no_grant", "apply requires .kraken/grants/apply or KRAKEN_BOARD_APPLY=1", ident)
        target = Path(payload.get("file") or (root / ".kraken" / "data" / "board" / "workspace.json"))
        if payload.get("file"):
            target = (root / payload["file"]).resolve()
            try:
                target.relative_to(root.resolve())
            except ValueError:
                return err("path_escape", "file must stay inside the project", ident)
        data: Any = {}
        if target.exists():
            raw = target.read_text(encoding="utf-8")
            data = json.loads(raw) if raw.strip() else {}
        elif payload.get("data") is not None:
            data = payload["data"]
        data = apply_ops(data, payload.get("operations") or [])
        if payload.get("save", True):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return ok({"arm": "board", "file": str(target), "data": data, "jev": True}, ident)
    if action == "finish":
        raw = dict(payload.get("raw") or {"arm": "board"})
        raw.update(payload.get("patch") or {})
        raw["finished"] = True
        return ok(raw, ident)
    if action == "clear":
        dest = home_root()
        if dest.exists():
            for p in dest.glob("*"):
                if p.is_file():
                    p.unlink()
        return ok({"cleared": True}, ident)
    return err("unknown_action", f"unknown action {action}", ident)


def main() -> int:
    raw = sys.stdin.read()
    req = json.loads(raw) if raw.strip() else {"action": "ping", "payload": {}}
    json.dump(dispatch(req), sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
