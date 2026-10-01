"""`kraken up` — turn a berth plan into a local compose + shared-network plan.

Core owns the docker network. berth only *plans*; it never starts a daemon.
This module reads the plan berth wrote, reconciles its network name with
``kraken.core.network``, and returns an executable plan. Nothing is started
unless the caller explicitly asks (``start=True``) and docker is present.

Policy: no daemon by default, no public ports added by core, no remote fetch.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

from kraken.core.network import normalize_network_name, resolve_docker
from kraken.core.paths import data_root

#: Arms that may own a compose plan. The first match wins.
PLAN_ARMS = ("berth", "board", "inlet")


class ComposeError(RuntimeError):
    """Raised when a plan cannot be read or is structurally invalid."""


def plan_dir(arm: str = "berth", home: Path | None = None) -> Path:
    """Where a CLI-mount arm stores its data. Mirrors the arm's own data_dir()."""
    return data_root(home) / arm


def find_plan(home: Path | None = None, arm: str | "None" = None) -> Path | None:
    """Locate a compose.yaml written by any planning arm."""
    order = [arm] if arm else list(PLAN_ARMS)
    for name in order:
        candidate = plan_dir(str(name), home) / "compose.yaml"
        if candidate.is_file():
            return candidate
    return None


def parse_compose(text: str, source: str = "<inline>") -> dict[str, Any]:
    """Parse a compose document into a normalized plan.

    Raises ComposeError on anything that is not a mapping with services.
    """
    try:
        raw = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        raise ComposeError(f"compose is not valid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise ComposeError("compose must be a mapping")
    services = raw.get("services") or {}
    if not isinstance(services, dict):
        raise ComposeError("compose services must be a mapping")
    networks = raw.get("networks") or {}
    if not isinstance(networks, dict):
        raise ComposeError("compose networks must be a mapping")

    network_name = ""
    for key, spec in networks.items():
        if isinstance(spec, dict) and spec.get("name"):
            network_name = str(spec["name"])
            break
        if key:
            network_name = str(key)
            break

    planned: list[dict[str, Any]] = []
    for svc, spec in sorted(services.items()):
        spec = spec if isinstance(spec, dict) else {"image": str(spec)}
        attached = spec.get("networks")
        if isinstance(attached, str):
            attached = [attached]
        elif isinstance(attached, dict):
            attached = sorted(str(x) for x in attached)
        elif isinstance(attached, (list, tuple)):
            attached = [str(x) for x in attached]
        else:
            attached = []
        planned.append(
            {
                "name": str(svc),
                "image": str(spec.get("image") or ""),
                "ports": [str(x) for x in (spec.get("ports") or [])],
                "networks": attached,
                "build": bool(spec.get("build")),
            }
        )

    return {
        "source": source,
        "network": normalize_network_name(network_name) if network_name else "",
        "network_driver": _driver_for(networks, network_name),
        "services": planned,
        "service_names": [s["name"] for s in planned],
    }


def _driver_for(networks: dict[str, Any], name: str) -> str:
    spec = networks.get(name) if name else None
    if isinstance(spec, dict):
        return str(spec.get("driver") or "bridge")
    return "bridge"


def _offline() -> bool:
    return os.environ.get("KRAKEN_OFFLINE") == "1"


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def up(
    payload: dict[str, Any] | None = None,
    root: Path | None = None,
    home: Path | None = None,
    start: bool = False,
) -> dict[str, Any]:
    """Plan (and optionally start) the shared `kraken` network from a berth plan.

    ``payload`` may carry ``compose`` (inline text), ``file`` (path to a
    compose.yaml), ``plan`` (path), or ``arm`` to pick a specific planning arm.
    """
    p = payload or {}
    source = "<inline>"
    text = ""

    if p.get("compose"):
        text = str(p["compose"])
    else:
        path_str = p.get("file") or p.get("plan") or p.get("path")
        if path_str:
            path = Path(str(path_str)).expanduser()
            if not path.is_file():
                raise ComposeError(f"no compose plan at {path}")
            text = path.read_text(encoding="utf-8")
            source = str(path)
        else:
            found = find_plan(home, p.get("arm"))
            if found is None:
                raise ComposeError(
                    "no compose plan found. run `kraken run berth up` first, "
                    "or pass payload.file"
                )
            text = found.read_text(encoding="utf-8")
            source = str(found)

    parsed = parse_compose(text, source)

    # Reconcile with core's docker policy so the plan and the network agree.
    net = resolve_docker({"network": parsed["network"] or None}, root=root)
    network = str(net["name"])
    driver = parsed["network_driver"]

    # A service attached to a differently-named network would not join ours.
    orphans = [
        s["name"]
        for s in parsed["services"]
        if s["networks"] and network not in s["networks"]
    ]

    plan: dict[str, Any] = {
        "ok": True,
        "verb": "up",
        "plan_source": source,
        "project": _project_name(text, source),
        "network": {"name": network, "driver": driver, "enabled": bool(net["enabled"])},
        "services": parsed["services"],
        "orphan_networks": orphans,
        "public_ports": [p_ for s in parsed["services"] for p_ in s["ports"]],
        "daemon": False,
        "offline": _offline(),
    }

    if orphans:
        plan["ok"] = False
        plan["error"] = {
            "code": "network_mismatch",
            "message": (
                f"services {', '.join(orphans)} are not on network '{network}'. "
                "set network.name in project.yaml"
            ),
        }
        return plan

    if not start:
        plan["next"] = [
            "kraken up --start   # runs docker compose up -d on the shared network",
        ]
        return plan

    if _offline():
        plan["ok"] = False
        plan["error"] = {"code": "offline", "message": "KRAKEN_OFFLINE=1 blocks start"}
        return plan

    if not _docker_available():
        plan["ok"] = False
        plan["error"] = {"code": "no_docker", "message": "docker not on PATH"}
        return plan

    result = _docker_compose_up(source, network, driver)
    plan.update(result)
    plan["daemon"] = bool(result.get("started"))
    return plan


def _project_name(text: str, source: str) -> str:
    try:
        raw = yaml.safe_load(text) or {}
    except yaml.YAMLError:
        raw = {}
    if isinstance(raw, dict):
        name = str(raw.get("name") or "").strip()
        if name:
            return name
    # Planning arms usually keep the project name beside the compose file.
    sibling = Path(source).parent / "project.json"
    if sibling.is_file():
        try:
            body = json.loads(sibling.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            body = {}
        if isinstance(body, dict) and str(body.get("name") or "").strip():
            return str(body["name"]).strip()
    return "kraken"


def _docker_compose_up(source: str, network: str, driver: str) -> dict[str, Any]:
    """Create the shared network if absent, then `docker compose up -d`."""
    exists = subprocess.run(
        ["docker", "network", "inspect", network],
        capture_output=True,
        check=False,
    )
    if exists.returncode != 0:
        created = subprocess.run(
            ["docker", "network", "create", "--driver", driver, network],
            capture_output=True,
            text=True,
            check=False,
        )
        if created.returncode != 0:
            return {
                "ok": False,
                "started": False,
                "error": {
                    "code": "network_create_failed",
                    "message": (created.stderr or "").strip()[:400]
                    or "docker network create failed",
                },
            }

    proc = subprocess.run(
        ["docker", "compose", "-f", source, "up", "-d"],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "ok": proc.returncode == 0,
        "started": proc.returncode == 0,
        "compose_stdout": (proc.stdout or "").strip()[-2000:],
        "compose_stderr": (proc.stderr or "").strip()[-1000:],
        "command": f"docker compose -f {source} up -d",
    }
