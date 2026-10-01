"""The Kraken configuration schema.

One table describing every setting Kraken understands: its type, default,
which scopes may set it, and what it does. Everything else reads this —
`kraken config` for output and documentation, `validate_config` for
rejection, and the docs — so a setting cannot exist in the YAML without also
being documented, typed, and checked.

Distinct from `schema.py`, which describes an *arm manifest* (arm.yaml).

Scopes, weakest to strongest:

    system   /etc/kraken/config.yaml            machine-wide defaults
    user     $KRAKEN_HOME/.kraken/config.yaml   this person
    project  <dir>/.kraken/config.yaml walking up from the cwd

Later scopes win per key. `scopes` on a setting says which of the three may
set it; it is not a separate storage class.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Scope = Literal["system", "user", "project"]

SCOPES: tuple[Scope, ...] = ("system", "user", "project")

ALL: tuple[Scope, ...] = SCOPES


@dataclass(frozen=True)
class Setting:
    key: str
    kind: Literal["str", "int", "bool", "list", "map"]
    default: Any
    summary: str
    scopes: tuple[Scope, ...] = ALL
    env: str | None = None
    detail: str = ""

    def type_name(self) -> str:
        return {
            "str": "string",
            "int": "integer",
            "bool": "boolean",
            "list": "list",
            "map": "map",
        }[self.kind]


# Ordered the way the docs read: identity, layout, behaviour, then effects.
SETTINGS: tuple[Setting, ...] = (
    Setting(
        "version",
        "int",
        1,
        "Config schema version. Not the CLI version.",
        detail=(
            "Bumped only when a key changes meaning or a new required key is "
            "added. An unknown version is reported by `kraken config "
            "validate` rather than silently ignored."
        ),
    ),
    Setting(
        "data_dir",
        "str",
        "data",
        "Directory under the Kraken home where arms keep their data.",
        detail=(
            "Relative to $KRAKEN_HOME/.kraken. Changing it after arms have "
            "written data leaves that data behind rather than moving it, so "
            "migrate it yourself or leave the default."
        ),
    ),
    Setting(
        "log_dir",
        "str",
        "logs",
        "Directory under the Kraken home for arm logs.",
    ),
    Setting(
        "cache_dir",
        "str",
        "cache",
        "Directory under the Kraken home for regenerable data.",
        detail="Safe to delete. Nothing in here is a source of truth.",
    ),
    Setting(
        "key_dir",
        "str",
        "keys",
        "Directory under the Kraken home for 0600 secrets.",
        detail=(
            "Never uploaded, never printed. `keeps` owns the contents and "
            "refuses to sync them."
        ),
    ),
    Setting(
        "notify",
        "map",
        {"channels": ["stdout"], "on_success": True, "on_error": True},
        "Where arm events are announced.",
        detail=(
            "channels: any of stdout, webhook, ntfy. A channel whose "
            "environment variable is unset is skipped rather than failing "
            "the run. Prefer stdout: the others are outbound, so 'local' "
            "means stdout only."
        ),
    ),
    Setting(
        "allow",
        "map",
        {k: False for k in ("tunnel", "remote_config", "scourge", "llm", "expose")},
        "Capability grants. Default deny: absent or false means off.",
        detail=(
            "Managed by `kraken grant <name> on|off`, which edits the user "
            "config. Honoured at every scope, so a project can lock a "
            "capability off. A commented-out line is not a grant — the "
            "resolver parses YAML, it does not search the text."
        ),
    ),
    Setting(
        "policy",
        "map",
        {"default": "deny", "grants": [], "network": "kraken"},
        "What arms may do without being asked.",
        detail=(
            "default: deny or allow. grants: capabilities arms may use. "
            "network: shared Docker network name, namespaced under kraken_ "
            "when it is an arbitrary label. A grant is still recorded in "
            "$KRAKEN_HOME/.kraken/grants.json — this is the declarative "
            "source, not a way around default-deny."
        ),
    ),
    Setting(
        "docker",
        "map",
        {
            "enabled": False,
            "name": "kraken",
            "driver": "bridge",
            "public": False,
            "isolated": False,
            "provider": "local",
            "config_url": "",
        },
        "The optional shared Docker network.",
        detail=(
            "enabled defaults to false: Kraken runs no daemon unless asked. "
            "public true would bind beyond loopback. config_url is an "
            "outbound fetch and is skipped entirely under KRAKEN_OFFLINE=1."
        ),
        env="KRAKEN_DOCKER_CONFIG_URL",
    ),
    Setting(
        "hooks",
        "map",
        {},
        "Arms to run around another arm's actions.",
        detail=(
            "Keyed by event: after_install, after_up, before_run, after_run, "
            "before_remove. Each value is a list of "
            "{tentacle, action, when, priority}. 'when' filters by target "
            "arm; lower priority runs first. A hook naming its own target is "
            "skipped, so a cycle cannot form."
        ),
    ),
    Setting(
        "tentacles",
        "list",
        [],
        "Arms available at this scope.",
        detail=(
            "Each entry: {name, kind, binary|actions, needs_docker, "
            "requires, grant, plan}. Arms installed under tentacles/ are "
            "discovered automatically, so use this to pin order, declare "
            "dependencies, or register a binary that is not on disk."
        ),
    ),
    Setting(
        "telemetry",
        "map",
        {"enabled": False, "events": ["install_ok", "demo_ok", "second_cmd"]},
        "Opt-in usage counters.",
        detail=(
            "Off unless enabled. Never sends argv, paths, or file contents. "
            "KRAKEN_OFFLINE=1 forces this off regardless of what the file "
            "says."
        ),
        env="KRAKEN_OFFLINE",
    ),
    Setting(
        "license",
        "map",
        {"api_base": "https://api.topta.co", "remote": True, "offline": False},
        "Premium-licence verification.",
        detail=(
            "remote false keeps verification local, which is what the test "
            "suite does. The answer is two-state: 200 means a paid seat, "
            "402 means buy one. offline true under KRAKEN_LICENSE_OFFLINE=1 "
            "short-circuits to a fixture."
        ),
        env="KRAKEN_LICENSE_REMOTE",
    ),
)

BY_KEY: dict[str, Setting] = {s.key: s for s in SETTINGS}

#: Highest config schema version this build understands.
SUPPORTED_VERSION: int = 1

#: Sub-key types inside the map settings, so a typo in a nested key is caught.
NESTED: dict[str, dict[str, str]] = {
    "docker": {
        "enabled": "bool",
        "name": "str",
        "driver": "str",
        "public": "bool",
        "isolated": "bool",
        "provider": "str",
        "config_url": "str",
    },
    "policy": {"default": "str", "grants": "list", "network": "str"},
    "allow": {
        "tunnel": "bool",
        "remote_config": "bool",
        "scourge": "bool",
        "llm": "bool",
        "expose": "bool",
    },
    # hooks is deliberately absent: it is an open map keyed by event name.
    # Event names are checked against HOOK_EVENTS instead.
    "notify": {"channels": "list", "on_success": "bool", "on_error": "bool"},
    "telemetry": {"enabled": "bool", "events": "list"},
    "license": {"api_base": "str", "remote": "bool", "offline": "bool"},
}

NOTIFY_CHANNELS = ("stdout", "webhook", "ntfy")
POLICY_DEFAULTS = ("deny", "allow")

#: Capabilities that `allow` may set. Kept here so the schema and the grant
#: module cannot disagree.
KNOWN_GRANTS = ("tunnel", "remote_config", "scourge", "llm", "expose")

#: Events a hook may be attached to. Anything else is a typo that would
#: silently never fire.
HOOK_EVENTS = (
    "after_install",
    "after_up",
    "before_run",
    "after_run",
    "before_remove",
)

#: Legacy shorthand still accepted for `notify`, written by older installs.
NOTIFY_SHORTHAND = {"local": ["stdout"], "stdout": ["stdout"], "none": []}

#: Top-level keys we recognise but deliberately do not manage.
RESERVED = ("name", "description", "_comment")


def defaults() -> dict[str, Any]:
    """A complete default config — every key present, no surprises."""
    return {s.key: copy_value(s.default) for s in SETTINGS}


def copy_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: copy_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [copy_value(v) for v in value]
    return value


def type_ok(kind: str, value: Any) -> bool:
    if kind == "str":
        return isinstance(value, str)
    if kind == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "bool":
        return isinstance(value, bool)
    if kind == "list":
        return isinstance(value, list)
    if kind == "map":
        return isinstance(value, dict)
    return False
