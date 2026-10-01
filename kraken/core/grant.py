"""User-facing permission grants. Default deny.

Grants are declared as `allow:` in config.yaml, at any scope. Resolution
parses YAML rather than searching the file text: a commented-out line is not a
grant. The previous implementation grepped for the literal string
`"expose: true"` anywhere in the file, so a line reading

    # expose: true

granted the capability. In a default-deny system that is a security bug — an
operator writing down "I do not want this" silently enabled it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kraken.core.paths import ensure_user_layout, user_kraken

from kraken.core.config_schema import KNOWN_GRANTS

#: Capabilities that can be granted. Anything else is rejected by `kraken grant`.
KNOWN = KNOWN_GRANTS


def _cfg(home: Path | None = None) -> Path:
    return ensure_user_layout(home) / "config.yaml"


def read_allow(home: Path | None = None, start: Path | None = None) -> dict[str, bool]:
    """Effective grants. Missing means False, at every scope.

    Reads the whole chain so a project can deny or grant, not just the user
    config. A later scope's explicit value wins; absence is never consent.
    """
    import yaml

    from kraken.core.paths import config_chain

    out = {k: False for k in KNOWN}
    for directory in config_chain(start):
        path = directory / "config.yaml"
        if not path.is_file():
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        if not isinstance(data, dict):
            continue
        allow = data.get("allow")
        if not isinstance(allow, dict):
            continue
        for name, value in allow.items():
            if name in out:
                out[name] = value is True
    return out


def grant(name: str, yes: bool = True, home: Path | None = None) -> dict[str, Any]:
    """Flip one grant in the user config, preserving everything else.

    Round-trips through YAML rather than editing text, so a grant cannot
    corrupt the file or leave a half-written line behind.
    """
    import yaml

    if name not in KNOWN:
        return {"ok": False, "error": f"unknown grant {name}", "known": list(KNOWN)}

    path = _cfg(home)
    data: dict[str, Any] = {}
    if path.exists():
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if isinstance(loaded, dict):
                data = loaded
        except yaml.YAMLError as exc:
            return {
                "ok": False,
                "error": f"{path} is not valid YAML, refusing to rewrite it: {exc}",
            }

    allow = data.get("allow")
    if not isinstance(allow, dict):
        allow = {}
    allow[name] = bool(yes)
    data["allow"] = allow

    ordered: dict[str, Any] = {}
    for key in ("version", "allow"):
        if key in data:
            ordered[key] = data.pop(key)
    ordered.update(data)

    header = (
        "# Kraken grants. Default deny: a capability is off unless it is\n"
        f"# true here. Managed by `kraken grant {name} on|off`.\n"
    )
    path.write_text(
        header + yaml.safe_dump(ordered, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return {"ok": True, "grant": name, "allowed": bool(yes), "config": str(path)}
