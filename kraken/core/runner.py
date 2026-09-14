"""Resolve an arm: in-process, then .kraken config, then installed tentacles."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kraken.core.config import load_config
from kraken.core.contract import invoke_binary
from kraken.core.license import assert_licensed
from kraken.core.loader import load_arms
from kraken.core.hooks import HookAbort, fire_hooks
from kraken.core.notify import emit
from kraken.core.registry import Registry
from kraken.core.resolve import resolve
from kraken.core.tentacle import discover_installed, spec_by_name

_IN_HOOK = False


def in_process_registry(root: Path) -> Registry:
    registry = Registry()
    registry.load_all(load_arms([root / "arms"]))
    return registry


def _resolve_binary(root: Path, spec: dict[str, Any]) -> Path:
    raw = spec.get("binary")
    if not raw:
        raise FileNotFoundError(f"tentacle {spec.get('name')} has no binary")
    path = Path(str(raw))
    if path.is_absolute():
        return path
    bases = [root, Path.cwd()]
    if spec.get("_root"):
        bases.insert(0, Path(spec["_root"]))
    for base in bases:
        candidate = (base / path).resolve()
        if candidate.exists():
            return candidate
    return (root / path).resolve()


def _invoke_one(
    root: Path, name: str, action: str, payload: dict[str, Any] | None
) -> dict[str, Any]:
    registry = in_process_registry(root)
    if name in registry.names():
        assert_licensed(name, registry.get(name).raw)
        return registry.run(name, action, payload)
    spec = spec_by_name(root, name)
    if spec:
        assert_licensed(name, spec)
        binary = _resolve_binary(root, spec)
        if not binary.exists():
            raise FileNotFoundError(f"tentacle binary missing: {binary}")
        return invoke_binary(binary, action, payload)
    raise KeyError(f"arm not loaded: {name}")


def _default_action(root: Path, name: str) -> str:
    registry = in_process_registry(root)
    if name in registry.names():
        actions = registry.get(name).actions
        return actions[0] if actions else "ping"
    spec = spec_by_name(root, name) or {}
    actions = spec.get("actions") or ["ping"]
    return str(actions[0])


def run_named(
    root: Path,
    name: str,
    action: str,
    payload: dict[str, Any] | None = None,
    compose: bool = False,
) -> dict[str, Any]:
    global _IN_HOOK
    plan = resolve(root, name)
    body = dict(payload or {})
    ctx = {"action": action, "plan": plan.order}
    if not _IN_HOOK:
        fire_hooks(root, "before_run", name, ctx, _invoke_one)
    if compose and len(plan.order) > 1:
        deps: dict[str, Any] = {}
        for dep in plan.order[:-1]:
            deps[dep] = _invoke_one(root, dep, _default_action(root, dep), body)
        body["_deps"] = deps
    try:
        result = _invoke_one(root, name, action, body)
    except Exception as exc:
        if not _IN_HOOK:
            fire_hooks(
                root,
                "on_error",
                name,
                {**ctx, "ok": False, "result": str(exc)},
                _invoke_one,
            )
        raise
    emit("run", {"name": name, "action": action, "ok": bool(result.get("ok", True))})
    if not _IN_HOOK:
        _IN_HOOK = True
        try:
            hooks = fire_hooks(
                root,
                "after_run",
                name,
                {**ctx, "ok": True, "result": result},
                _invoke_one,
            )
            if hooks and isinstance(result, dict):
                result = dict(result)
                result["_hooks"] = hooks
                patch = _hook_patch(hooks)
                spec = spec_by_name(root, name) or {}
                actions = spec.get("actions") or []
                if patch and "finish" in actions and action != "finish":
                    finished = _invoke_one(
                        root,
                        name,
                        "finish",
                        {
                            **(payload or {}),
                            "raw": result.get("result"),
                            "patch": patch,
                        },
                    )
                    result["result"] = finished.get("result", finished)
                    result["finished"] = True
        finally:
            _IN_HOOK = False
    return result


def _hook_patch(hooks: list[dict[str, Any]]) -> dict[str, Any]:
    patch: dict[str, Any] = {}
    for hook in hooks:
        blob = hook.get("result") or {}
        inner = blob.get("result") if isinstance(blob.get("result"), dict) else blob
        if isinstance(inner, dict) and isinstance(inner.get("patch"), dict):
            patch.update(inner["patch"])
    return patch


def list_all(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    registry = in_process_registry(root)
    for name in registry.names():
        arm = registry.get(name)
        seen.add(arm.name)
        rows.append(
            {
                "name": arm.name,
                "version": arm.version,
                "actions": arm.actions,
                "kind": "in-process",
                "license": arm.raw.get("license") or "free",
                "platforms": arm.raw.get("platforms") or ["any"],
                "needs_docker": bool(arm.raw.get("needs_docker")),
            }
        )
    for spec in (load_config(root).get("tentacles") or []) + discover_installed():
        name = spec.get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        rows.append(
            {
                "name": name,
                "version": spec.get("version", ""),
                "actions": spec.get("actions") or [],
                "kind": "binary",
                "binary": spec.get("binary"),
                "license": spec.get("license") or "free",
                "platforms": spec.get("platforms") or ["any"],
                "needs_docker": bool(spec.get("needs_docker")),
            }
        )
    return rows
