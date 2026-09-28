"""`kraken config` — show what is configured, and why.

Five subcommands:

    kraken config list              every setting, default, and effective value
    kraken config get <key>         one setting
    kraken config explain <key>     which file won, and what it overrides
    kraken config path              the chain of files, in order
    kraken config validate          check every file; exit 2 on problems
    kraken config init [--scope S]  write a commented example

Output is JSON like every other verb, so `kraken config get docker | jq` works.
Human-readable text is under "text" for anyone reading it directly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kraken.core import config_chain as cc
from kraken.core import config_schema as cs


def _setting_view(key: str, value: Any, origin: cc.Origin) -> dict[str, Any]:
    setting = cs.BY_KEY[key]
    view: dict[str, Any] = {
        "key": key,
        "type": setting.type_name(),
        "summary": setting.summary,
        "value": value,
        "default": setting.default,
        "changed": origin.scope != "default",
        "scope": origin.scope,
        "source": origin.source,
        "scopes": list(setting.scopes),
    }
    if setting.env:
        view["env"] = setting.env
    if setting.detail:
        view["detail"] = setting.detail
    return view


def _chain_view(start: Path | None = None) -> list[dict[str, Any]]:
    return [
        {"scope": scope, "path": str(path), "exists": exists}
        for scope, path, exists in cc.chain_files(start)
    ]


def cmd_list(args: Any, root: Path | None = None) -> tuple[dict[str, Any], int]:
    merged, origins = cc.resolve(root)
    settings = [_setting_view(k, merged[k], origins[k]) for k in merged]

    problems = cc.validate_config(root)
    lines = []
    for view in settings:
        mark = "*" if view["changed"] else " "
        lines.append(
            f"{mark} {view['key']:<12} {view['type']:<8} "
            f"[{view['scope']}] {json.dumps(view['value'])}"
        )
    if problems:
        lines.append("")
        lines.append(f"{len(problems)} problem(s):")
        lines.extend(f"  - {p}" for p in problems)

    return (
        {
            "ok": not problems,
            "verb": "config",
            "action": "list",
            "chain": _chain_view(root),
            "settings": settings,
            "valid": not problems,
            "problems": problems,
            "text": "\n".join(lines),
        },
        0 if not problems else 2,
    )


def cmd_get(args: Any, root: Path | None = None) -> tuple[dict[str, Any], int]:
    key = args.key
    if key not in cs.BY_KEY:
        known = ", ".join(cs.BY_KEY)
        return (
            {
                "ok": False,
                "verb": "config",
                "action": "get",
                "error": {"code": "unknown_key", "message": f"unknown setting {key!r}"},
                "known": list(cs.BY_KEY),
                "text": f"unknown setting {key!r}. Known: {known}",
            },
            2,
        )

    merged, origins = cc.resolve(root)
    view = _setting_view(key, merged[key], origins[key])
    return (
        {
            "ok": True,
            "verb": "config",
            "action": "get",
            "key": key,
            "value": view["value"],
            "setting": view,
            "text": f"{key} = {json.dumps(view['value'])}  ({view['scope']}: {view['source']})",
        },
        0,
    )


def cmd_explain(args: Any, root: Path | None = None) -> tuple[dict[str, Any], int]:
    key = args.key
    if key not in cs.BY_KEY:
        return (
            {
                "ok": False,
                "verb": "config",
                "action": "explain",
                "error": {"code": "unknown_key", "message": f"unknown setting {key!r}"},
            },
            2,
        )

    merged, origins = cc.resolve(root)
    setting = cs.BY_KEY[key]

    layers: list[dict[str, Any]] = []
    for scope, path, exists in cc.chain_files(root):
        if not exists:
            continue
        try:
            data = cc.load_yaml(path)
        except ValueError as exc:
            layers.append({"scope": scope, "path": str(path), "error": str(exc)})
            continue
        if key in data:
            layers.append({"scope": scope, "path": str(path), "value": data[key]})
    if os_offline_note(setting, key):
        layers.insert(
            0, {"scope": "env", "source": setting.env, "note": "overrides the file"}
        )

    lines = [f"{key}  (default {json.dumps(setting.default)})"]
    for layer in layers:
        where = layer.get("path", layer.get("source", "?"))
        value = (
            json.dumps(layer.get("value"))
            if "value" in layer
            else layer.get("note", "")
        )
        lines.append(f"  {layer['scope']:<8} {where}")
        if value:
            lines.append(f"           {value}")

    return (
        {
            "ok": True,
            "verb": "config",
            "action": "explain",
            "key": key,
            "effective": merged[key],
            "won_by": {"scope": origins[key].scope, "source": origins[key].source},
            "layers": layers,
            "text": "\n".join(lines),
        },
        0,
    )


def os_offline_note(setting: cs.Setting, key: str) -> bool:
    import os

    if key == "telemetry" and os.environ.get("KRAKEN_OFFLINE") == "1":
        return True
    if key == "license" and os.environ.get("KRAKEN_LICENSE_REMOTE") == "0":
        return True
    if key == "docker" and os.environ.get("KRAKEN_DOCKER_CONFIG_URL"):
        return True
    return False


def cmd_path(args: Any, root: Path | None = None) -> tuple[dict[str, Any], int]:
    chain = _chain_view(root)
    text = "\n".join(
        f"{'✓' if item['exists'] else '·'} {item['scope']:<8} {item['path']}"
        for item in chain
    )
    return (
        {"ok": True, "verb": "config", "action": "path", "chain": chain, "text": text},
        0,
    )


def cmd_validate(args: Any, root: Path | None = None) -> tuple[dict[str, Any], int]:
    problems = cc.validate_config(root)
    text = (
        "\n".join(f"  - {p}" for p in problems)
        if problems
        else f"ok — {len(cs.SETTINGS)} settings, {len(cc.chain_files(root))} file(s) in the chain"
    )
    return (
        {
            "ok": not problems,
            "verb": "config",
            "action": "validate",
            "valid": not problems,
            "problems": problems,
            "chain": _chain_view(root),
            "text": text,
        },
        0 if not problems else 2,
    )


def cmd_init(args: Any, root: Path | None = None) -> tuple[dict[str, Any], int]:
    from kraken.core.paths import system_kraken, user_kraken

    scope = args.scope
    if scope == "system":
        target = system_kraken() / "config.yaml"
    elif scope == "user":
        target = user_kraken() / "config.yaml"
    else:
        target = Path.cwd() / ".kraken" / "config.yaml"

    try:
        cc.write_example(target, scope)
        written = True
        error = None
    except FileExistsError as exc:
        written = False
        error = str(exc)
    except OSError as exc:
        written = False
        error = str(exc)

    problems = cc.validate_config(root) if written else []
    return (
        {
            "ok": written and not problems,
            "verb": "config",
            "action": "init",
            "scope": scope,
            "path": str(target),
            "written": written,
            "problems": problems,
            "error": {"code": "exists" if written is False else None, "message": error}
            if error
            else None,
            "text": (
                f"wrote {target}"
                if written and not problems
                else (
                    f"did not write {target}: {error}"
                    if error
                    else f"wrote {target} but it does not validate: {problems}"
                )
            ),
        },
        0 if written and not problems else 2,
    )
