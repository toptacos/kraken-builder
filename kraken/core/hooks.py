"""Lifecycle hooks: core events that invoke other tentacles.

Hooks are not middleware and not compose-deps. They are side-effect tentacles.
A hook invoke never re-enters the hook runner (no hook→hook cycles).
"""

from __future__ import annotations

from typing import Any, Callable

from kraken.core.config import load_config
from kraken.core.notify import emit
from kraken.core.resolve import catalog
from kraken.core.tentacle import spec_by_name


HOOK_EVENTS = ("before_run", "after_run", "on_error", "after_install")


class HookAbort(RuntimeError):
    pass


def _matches(when: list[str] | str | None, target: str) -> bool:
    if not when:
        return True
    names = when if isinstance(when, list) else [when]
    return any(n in {"*", target} for n in names)


def collect_hooks(root, event: str, target: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    cfg = load_config(root).get("hooks") or {}
    items.extend(cfg.get(event) or [])
    spec = spec_by_name(root, target) or {}
    nodes = catalog(root)
    if target in nodes:
        spec = {**nodes[target].spec, **spec}
    declared = (spec.get("hooks") or {}).get(event) or []
    items.extend(declared)
    out: list[dict[str, Any]] = []
    for raw in items:
        if isinstance(raw, str):
            raw = {"tentacle": raw, "action": "ping"}
        if not _matches(raw.get("when"), target):
            continue
        if raw.get("tentacle") == target:
            continue
        out.append(raw)
    return out


def fire_hooks(
    root,
    event: str,
    target: str,
    context: dict[str, Any],
    invoke: Callable[..., dict[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for hook in collect_hooks(root, event, target):
        name = hook.get("tentacle")
        action = hook.get("action") or "ping"
        optional = bool(hook.get("optional", True))
        if not name:
            continue
        payload = {
            "hook": event,
            "target": target,
            "target_action": context.get("action"),
            "ok": context.get("ok"),
            "result": context.get("result"),
            "plan": context.get("plan"),
        }
        try:
            result = invoke(root, name, action, payload)
            results.append({"tentacle": name, "ok": True, "result": result})
            emit("hook", {"event": event, "tentacle": name, "target": target})
        except Exception as exc:  # missing, license, binary
            if optional:
                results.append({"tentacle": name, "ok": False, "skipped": True, "error": str(exc)})
                continue
            if event == "before_run":
                raise HookAbort(f"before_run hook '{name}' aborted {target}: {exc}") from exc
            results.append({"tentacle": name, "ok": False, "error": str(exc)})
        else:
            if event == "before_run" and result.get("ok") is False and not optional:
                raise HookAbort(
                    f"before_run hook '{name}' aborted {target}: {result.get('error') or result}"
                )
    return results
