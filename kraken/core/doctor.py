"""kraken doctor — layout, protocol, graph, licenses."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kraken.core.contract import PROTOCOL_VERSION
from kraken.core.license import load_store
from kraken.core.paths import ensure_user_layout
from kraken.core.resolve import CORE_VERSION, ResolveError, catalog, resolve


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
    }
