"""Validate every sites/*.yaml against the site-tentacle contract.

A new site must be a new file, not a new droplet. That only holds if the
schema is enforced somewhere, so this is the enforcement point.

Run: python3 scripts/validate_sites.py [sites_dir]
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

#: Hosts the vision doc requires. Adding a face means adding a file here.
REQUIRED = {"kraken", "tacos", "music", "blog", "discgolf", "profile", "portfolio"}

MOUNTS = {"cli", "site", "both"}
LICENSES = {"free", "premium", "metered"}

#: Keys whose value must never be a literal secret.
FORBIDDEN_KEYS = {
    "token",
    "secret",
    "password",
    "client_secret",
    "api_key",
    "private_key",
    "license_key",
    "webhook_secret",
}

FORBIDDEN_VALUES = ("sk-", "ghp_", "xoxb-", "xoxp-", "AKIA", "-----BEGIN")


def validate_file(path: Path) -> list[str]:
    """Return a list of problems. Empty means valid."""
    problems: list[str] = []
    name = path.stem

    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return [f"{name}: not valid YAML: {exc}"]

    if not isinstance(doc, dict):
        return [f"{name}: top level must be a mapping"]

    if not doc.get("name"):
        problems.append(f"{name}: missing name")
    elif doc["name"] != name:
        problems.append(f"{name}: name '{doc['name']}' does not match filename")

    if not doc.get("host"):
        problems.append(f"{name}: missing host")
    elif doc["host"] != f"{name}.topta.co":
        problems.append(f"{name}: host '{doc['host']}' should be {name}.topta.co")

    mount = doc.get("mount")
    if mount not in MOUNTS:
        problems.append(f"{name}: mount must be one of {sorted(MOUNTS)}, got {mount!r}")

    if doc.get("license") not in LICENSES:
        problems.append(f"{name}: license must be one of {sorted(LICENSES)}")

    api = doc.get("api")
    if not isinstance(api, dict) or not api.get("collection"):
        problems.append(f"{name}: api.collection is required")

    if mount in ("cli", "both") and not doc.get("cli"):
        problems.append(f"{name}: mount={mount} requires a cli block")

    problems.extend(_scan_secrets(name, doc))
    return problems


def _scan_secrets(name: str, node: object, trail: str = "") -> list[str]:
    """Site yaml is public config. Refuse anything that smells like a secret."""
    problems: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{trail}.{key}" if trail else str(key)
            if str(key).lower() in FORBIDDEN_KEYS:
                problems.append(f"{name}: key {here} must not appear in sites/*.yaml")
            problems.extend(_scan_secrets(name, value, here))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            problems.extend(_scan_secrets(name, value, f"{trail}[{i}]"))
    elif isinstance(node, str):
        for needle in FORBIDDEN_VALUES:
            if needle in node:
                problems.append(
                    f"{name}: value at {trail} looks like a secret ({needle})"
                )
    return problems


def validate_dir(sites_dir: Path) -> list[str]:
    problems: list[str] = []
    files = sorted(sites_dir.glob("*.yaml")) + sorted(sites_dir.glob("*.yml"))
    if not files:
        return [f"{sites_dir}: no site yaml found"]

    seen: dict[str, str] = {}
    for path in files:
        problems.extend(validate_file(path))
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(doc, dict):
            host = str(doc.get("host") or "")
            if host and host in seen:
                problems.append(
                    f"{path.stem}: host {host} already claimed by {seen[host]}"
                )
            elif host:
                seen[host] = path.stem

    have = {p.stem for p in files}
    for missing in sorted(REQUIRED - have):
        problems.append(f"missing required site yaml: {missing}.yaml")
    return problems


def main(argv: list[str]) -> int:
    sites_dir = (
        Path(argv[1])
        if len(argv) > 1
        else Path(__file__).resolve().parents[1] / "sites"
    )
    problems = validate_dir(sites_dir)
    if problems:
        for line in problems:
            print(f"FAIL {line}", file=sys.stderr)
        return 1
    count = len(list(sites_dir.glob("*.yaml")))
    print(f"ok {count} site tentacles validated in {sites_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
