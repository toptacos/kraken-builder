"""kraken doctor — layout, protocol, graph, licenses, next actions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kraken.core.contract import PROTOCOL_VERSION
from kraken.core.license import load_store
from kraken.core.paths import ensure_user_layout
from kraken.core.resolve import CORE_VERSION, ResolveError, catalog, resolve
from kraken.core.tentacle import discover_installed


def next_actions(root: Path, installed: list[str] | None = None) -> list[str]:
    names = set(installed or [])
    if not names:
        names = {str(s.get("name")) for s in discover_installed()}
        names.update(catalog(root))
    steps: list[str] = []
    if "geo" not in names:
        steps.append("kraken tentacle add examples/tentacles/geo")
    steps.append('kraken run geo lookup --payload \'{"ip":"1.1.1.1"}\'')
    if "filesort" not in names:
        steps.append("kraken tentacle add examples/tentacles/filesort")
    steps.append('kraken run filesort scan --payload \'{"path":"."}\'')
    steps.append("kraken grant expose")
    steps.append(
        'kraken run expose plan --payload \'{"host":"panel.kraken.localhost"}\''
    )
    steps.append("docs: https://kraken.topta.co/use-cases")
    return steps


def inspect(root: Path) -> dict[str, Any]:
    home = ensure_user_layout()
    checks: list[dict[str, Any]] = []

    def ok(name: str, detail: str, passed: bool = True) -> None:
        checks.append({"name": name, "ok": passed, "detail": detail})

    for folder in ("data", "logs", "tentacles", "cache", "keys"):
        path = home / folder
        ok(f"layout.{folder}", str(path), path.is_dir())

    ok("protocol", str(PROTOCOL_VERSION))
    ok("core", CORE_VERSION)
    store = load_store()
    ok("licenses.keys", str(len(store.get("keys") or {})))

    nodes = catalog(root)
    ok("catalog", f"{len(nodes)} tentacles")
    for name in nodes:
        try:
            plan = resolve(root, name)
            ok(f"plan.{name}", " → ".join(plan.order))
        except ResolveError as exc:
            ok(f"plan.{name}", str(exc), passed=False)

    return {
        "ok": all(c["ok"] for c in checks),
        "home": str(home),
        "checks": checks,
        "next": next_actions(root, list(nodes)),
    }
