"""Declare-only tentacle dependency graph.

One installed version per name. Language packages stay inside the binary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kraken.core.config import load_config
from kraken.core.contract import PROTOCOL_VERSION
from kraken.core.loader import load_arms
from kraken.core.semver import satisfies
from kraken.core.tentacle import discover_installed

CORE_VERSION = "0.1.1"


class ResolveError(ValueError):
    pass


@dataclass
class Node:
    name: str
    version: str
    spec: dict[str, Any]
    kind: str


@dataclass
class Plan:
    root: str
    order: list[str] = field(default_factory=list)
    nodes: dict[str, Node] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    optional_missing: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "order": self.order,
            "nodes": {
                k: {"version": n.version, "kind": n.kind} for k, n in self.nodes.items()
            },
            "optional_missing": self.optional_missing,
        }


def _requires(spec: dict[str, Any]) -> dict[str, Any]:
    raw = spec.get("requires") or {}
    if not isinstance(raw, dict):
        return {}
    return raw


def _tentacle_reqs(spec: dict[str, Any]) -> dict[str, str]:
    reqs = _requires(spec).get("tentacles") or spec.get("depends_on") or {}
    if isinstance(reqs, list):
        return {str(name): "*" for name in reqs}
    if not isinstance(reqs, dict):
        return {}
    out: dict[str, str] = {}
    for name, bound in reqs.items():
        out[str(name)] = "optional" if bound is True else str(bound)
    return out


def catalog(root) -> dict[str, Node]:
    nodes: dict[str, Node] = {}
    for arm in load_arms([root / "arms"]):
        nodes[arm.name] = Node(arm.name, arm.version, arm.raw, "in-process")
    for spec in (load_config(root).get("tentacles") or []) + discover_installed():
        name = spec.get("name")
        if not name or name in nodes:
            continue
        nodes[str(name)] = Node(
            str(name), str(spec.get("version") or "0.0.0"), spec, "binary"
        )
    return nodes


def _check_static(node: Node) -> None:
    req = _requires(node.spec)
    proto = req.get("protocol", node.spec.get("protocol", PROTOCOL_VERSION))
    try:
        proto_i = int(proto)
    except (TypeError, ValueError):
        proto_i = PROTOCOL_VERSION
    if proto_i > PROTOCOL_VERSION:
        raise ResolveError(
            f"{node.name} needs protocol {proto_i}; core speaks {PROTOCOL_VERSION}"
        )
    core_bound = req.get("core")
    if core_bound and not satisfies(CORE_VERSION, str(core_bound)):
        raise ResolveError(f"{node.name} needs core {core_bound}; have {CORE_VERSION}")


def resolve(root, name: str) -> Plan:
    nodes = catalog(root)
    if name not in nodes:
        raise ResolveError(f"arm not loaded: {name}")

    plan = Plan(root=name)
    visiting: set[str] = set()
    done: set[str] = set()

    def walk(current: str, trail: list[str]) -> None:
        if current in done:
            return
        if current in visiting:
            cycle = " -> ".join([*trail, current])
            raise ResolveError(f"dependency cycle: {cycle}")
        node = nodes[current]
        _check_static(node)
        visiting.add(current)
        for dep, bound in _tentacle_reqs(node.spec).items():
            optional = str(bound).strip().lower() == "optional"
            if dep not in nodes:
                if optional:
                    plan.optional_missing.append(dep)
                    continue
                raise ResolveError(
                    f"{current} requires missing tentacle '{dep}' ({bound})"
                )
            installed = nodes[dep].version
            if not optional and not satisfies(installed, bound):
                raise ResolveError(
                    f"{current} requires {dep} {bound}; installed {installed}"
                )
            walk(dep, trail + [current])
        visiting.remove(current)
        done.add(current)
        plan.nodes[current] = node
        plan.order.append(current)

    walk(name, [])
    return plan
