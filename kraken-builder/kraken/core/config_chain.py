"""Resolve, validate, and explain the .kraken config chain.

`load_config` keeps its original signature and behaviour — the existing 167
tests depend on it — and this module layers on top:

  * provenance, so `kraken config explain` can say which file a key came from
  * validation against `config_schema`, with the offending file and key
  * environment overrides, for the small set of settings where a variable is
    the right tool
  * the full default set as the base, so a partial file is always complete

Scopes, weakest to strongest: system → user → project (closest dir wins).
Merge is per key, deep for maps, and a list is replaced rather than appended:
overriding a list should mean "this is the list", not "these too".
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from kraken.core import config_schema as cs
from kraken.core.paths import config_chain, user_kraken


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in overlay.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a mapping")
    return data


def load_config(start: Path | None = None) -> dict[str, Any]:
    """Merged config, complete. Kept signature-compatible on purpose."""
    merged: dict[str, Any] = {"version": 1, "tentacles": [], "notify": "local"}
    for directory in config_chain(start):
        merged = _deep_merge(merged, load_yaml(directory / "config.yaml"))
    return merged


# --- provenance -------------------------------------------------------------


@dataclass
class Origin:
    """Where a key's effective value came from."""

    scope: str  # "default" | "system" | "user" | "project" | "env"
    source: str  # path or variable name


def scope_of(directory: Path) -> str:
    system = os.environ.get("KRAKEN_SYSTEM_DIR", "/etc/kraken")
    if str(directory) == system:
        return "system"
    if directory == user_kraken():
        return "user"
    return "project"


def resolve(start: Path | None = None) -> tuple[dict[str, Any], dict[str, Origin]]:
    """Merged config plus, for each top-level key, where it came from."""
    merged = cs.defaults()
    origins: dict[str, Origin] = {k: Origin("default", "schema") for k in merged}

    for directory in config_chain(start):
        path = directory / "config.yaml"
        data = load_yaml(path)
        if not data:
            continue
        scope = scope_of(directory)
        for key, value in data.items():
            if key not in cs.BY_KEY:
                # Reported by validate_config; not configuration.
                continue
            current = merged.get(key)
            if isinstance(current, dict) and isinstance(value, dict):
                merged[key] = _deep_merge(current, value)
            else:
                # A list replaces rather than appends: overriding a list means
                # "this is the list", not "these too".
                merged[key] = value
            origins[key] = Origin(scope, str(path))

    for key, env_value in _env_overrides().items():
        merged[key] = env_value
        origins[key] = Origin("env", _ENV_SOURCE[key])

    if isinstance(merged.get("notify"), str):
        base = cs.copy_value(cs.BY_KEY["notify"].default)
        base["channels"] = list(cs.NOTIFY_SHORTHAND.get(merged["notify"], ["stdout"]))
        merged["notify"] = base

    return merged, origins


#: Settings where an environment variable legitimately overrides the file.
_ENV_SOURCE = {
    "docker": "KRAKEN_DOCKER_CONFIG_URL",
    "telemetry": "KRAKEN_OFFLINE",
    "license": "KRAKEN_LICENSE_REMOTE",
}


def _env_overrides() -> dict[str, Any]:
    """Environment beats file, for the few settings where that is the point."""
    out: dict[str, Any] = {}

    url = os.environ.get("KRAKEN_DOCKER_CONFIG_URL")
    if url:
        base = cs.copy_value(cs.BY_KEY["docker"].default)
        base["provider"] = "url"
        base["config_url"] = url
        out["docker"] = base

    if os.environ.get("KRAKEN_OFFLINE") == "1":
        base = cs.copy_value(cs.BY_KEY["telemetry"].default)
        base["enabled"] = False
        out["telemetry"] = base

    if os.environ.get("KRAKEN_LICENSE_REMOTE") == "0":
        base = cs.copy_value(cs.BY_KEY["license"].default)
        base["remote"] = False
        out["license"] = base

    return out


# --- validation -------------------------------------------------------------


def validate_config(start: Path | None = None) -> list[str]:
    """Every problem found, as human-readable lines. Empty means valid."""
    problems: list[str] = []
    supported = cs.SUPPORTED_VERSION

    for directory in config_chain(start):
        path = directory / "config.yaml"
        if not path.exists():
            continue
        scope = scope_of(directory)
        try:
            data = load_yaml(path)
        except ValueError as exc:
            problems.append(f"{path}: {exc}")
            continue

        version = data.get("version")
        if (
            isinstance(version, int)
            and not isinstance(version, bool)
            and version > supported
        ):
            problems.append(
                f"{path}: version {version} is newer than the supported {supported}. "
                "Upgrade Kraken, or comment the key out."
            )

        for key, value in data.items():
            if key in cs.RESERVED:
                continue
            setting = cs.BY_KEY.get(key)
            if setting is None:
                problems.append(
                    f"{path}: unknown setting {key!r}. "
                    f"Run `kraken config list` to see all {len(cs.SETTINGS)}."
                )
                continue
            if scope not in setting.scopes:
                problems.append(
                    f"{path}: {key!r} cannot be set at {scope} scope "
                    f"(allowed: {', '.join(setting.scopes)})"
                )
            if key == "notify" and isinstance(value, str):
                # Written by older installs as `notify: local`. Accepted and
                # normalised, so nobody's existing config breaks.
                if value not in cs.NOTIFY_SHORTHAND:
                    problems.append(
                        f"{path}: notify {value!r} is not a known shorthand. "
                        f"Use a map with channels, or one of "
                        f"{', '.join(sorted(cs.NOTIFY_SHORTHAND))}"
                    )
                continue
            if not cs.type_ok(setting.kind, value):
                problems.append(
                    f"{path}: {key!r} should be {setting.type_name()}, "
                    f"got {type(value).__name__}"
                )
                continue
            if setting.kind == "map":
                problems.extend(_nested_problems(path, key, value, setting))
            if key == "hooks" and isinstance(value, dict):
                problems.extend(_hook_problems(path, value))

    return problems


def _hook_problems(path: Path, hooks: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for event, entries in hooks.items():
        if event not in cs.HOOK_EVENTS:
            out.append(
                f"{path}: hooks.{event} is not an event. "
                f"Known: {', '.join(cs.HOOK_EVENTS)}"
            )
            continue
        if not isinstance(entries, list):
            out.append(f"{path}: hooks.{event} must be a list of hook entries")
            continue
        for i, entry in enumerate(entries):
            if isinstance(entry, str):
                continue
            if not isinstance(entry, dict):
                out.append(f"{path}: hooks.{event}[{i}] must be a mapping or a name")
                continue
            if not entry.get("tentacle"):
                out.append(f"{path}: hooks.{event}[{i}] needs a 'tentacle'")
    return out


def _nested_problems(
    path: Path, key: str, value: dict[str, Any], setting: cs.Setting
) -> list[str]:
    out: list[str] = []
    expected = cs.NESTED.get(key)
    if expected is None:
        # An open map (hooks) — validated separately by _hook_problems.
        return out
    for sub, sub_value in value.items():
        kind = expected.get(sub)
        if kind is None:
            out.append(
                f"{path}: unknown {key}.{sub}. "
                f"Known: {', '.join(sorted(expected)) or 'none'}"
            )
            continue
        if not cs.type_ok(kind, sub_value):
            out.append(
                f"{path}: {key}.{sub} should be {kind}, got {type(sub_value).__name__}"
            )

    if key == "policy":
        mode = value.get("default")
        if isinstance(mode, str) and mode not in cs.POLICY_DEFAULTS:
            out.append(
                f"{path}: policy.default must be one of "
                f"{', '.join(cs.POLICY_DEFAULTS)}, got {mode!r}"
            )
    if key == "notify":
        channels = value.get("channels")
        if isinstance(channels, list):
            for channel in channels:
                if channel not in cs.NOTIFY_CHANNELS:
                    out.append(
                        f"{path}: notify.channels has unknown channel "
                        f"{channel!r}. Known: {', '.join(cs.NOTIFY_CHANNELS)}"
                    )
    if key == "docker":
        if value.get("public") is True:
            out.append(
                f"{path}: docker.public true would bind beyond loopback. "
                "Kraken refuses to publish a network; leave it false."
            )
        if value.get("enabled") is True and value.get("name") is None:
            out.append(f"{path}: docker.enabled is true but no name is set")
    return out


# --- files ------------------------------------------------------------------


def chain_files(start: Path | None = None) -> list[tuple[str, Path, bool]]:
    """(scope, path, exists) for each config file the chain consults."""
    out: list[tuple[str, Path, bool]] = []
    for directory in config_chain(start):
        path = directory / "config.yaml"
        out.append((scope_of(directory), path, path.exists()))
    return out


def write_example(path: Path, scope: str) -> Path:
    """Write a fully-commented example for the given scope."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"{path} already exists; not overwriting")
    path.write_text(example_yaml(scope), encoding="utf-8")
    return path


def example_yaml(scope: str) -> str:
    header = {
        "system": (
            "# Kraken SYSTEM configuration\n"
            "#\n"
            "# /etc/kraken/config.yaml — machine-wide defaults for everyone on\n"
            "# this host. Set a key here to pin it; a user or project config can\n"
            "# still override it, so this is a default, not a lock.\n"
            "#\n"
            "# Scope rules: every setting may be set at system scope except the\n"
            "# ones documented as user/project only. Validate with:\n"
            "#     kraken config validate\n"
        ),
        "user": (
            "# Kraken USER configuration\n"
            "#\n"
            "# $KRAKEN_HOME/.kraken/config.yaml — this person, this machine.\n"
            "# Overrides /etc/kraken/config.yaml; a project config in the\n"
            "# current directory overrides this.\n"
            "#\n"
            "# Everything here is a real setting: nothing is decorative.\n"
        ),
        "project": (
            "# Kraken PROJECT configuration\n"
            "#\n"
            "# <this-dir>/.kraken/config.yaml — travels with the project and\n"
            "# wins over both system and user config for anything run from\n"
            "# here. Keep it in version control: it holds no secrets. Secrets\n"
            "# live in keys/ under the user home and are never read from here.\n"
            "#\n"
            "# Commit this file. It is the point of project scope.\n"
        ),
    }[scope]

    body = [
        "",
        "version: 1",
        "",
        "# Where arms keep their data. Relative to the Kraken home.",
        "data_dir: data",
        "log_dir: logs",
        "cache_dir: cache",
        "key_dir: keys",
        "",
        "# Capability grants. Default deny: absent or false means off. A",
        "# commented-out line is NOT a grant — the resolver parses YAML.",
        "# Prefer `kraken grant <name> on` over editing this by hand.",
        "allow:",
        *[f"  {g}: false" for g in cs.KNOWN_GRANTS],
        "",
        "# What arms may do without being asked. Default-deny on purpose.",
        "policy:",
        f"  default: {'allow' if scope == 'system' else 'deny'}",
        "  grants: []",
        "  # An arbitrary label is namespaced to kraken_<label> so two projects",
        "  # cannot collide on one host.",
        "  network: kraken",
        "",
        "# Where arm events are announced. A channel whose environment variable",
        "# is unset is skipped rather than failing the run.",
        "notify:",
        "  channels:",
        "    - stdout",
        "  on_success: true",
        "  on_error: true",
        "",
        "# The shared Docker network. Disabled means Kraken starts no daemon.",
        "docker:",
        "  enabled: false",
        "  name: kraken",
        "  driver: bridge",
        "  public: false",
        "  provider: local",
        "",
        "# Arms to run around another arm's actions. Lower priority runs first.",
        "hooks: {}",
        "",
        "# Arms available at this scope. Installed arms are discovered anyway;",
        "# use this to pin order or declare dependencies.",
        "tentacles: []",
        "",
        "# Opt-in counters. Off unless enabled. KRAKEN_OFFLINE=1 forces off.",
        "telemetry:",
        "  enabled: false",
        "  events:",
        "    - install_ok",
        "    - demo_ok",
        "    - second_cmd",
        "",
        "# Premium-licence verification. 200 = a paid seat, 402 = buy one.",
        "license:",
        "  api_base: https://api.topta.co",
        "  remote: true",
        "",
    ]
    return header + "\n".join(body)
