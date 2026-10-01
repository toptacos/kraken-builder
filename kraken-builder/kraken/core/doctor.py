"""kraken doctor — layout, protocol, graph, licenses, next actions."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import kraken
from kraken.core.contract import PROTOCOL_VERSION
from kraken.core.license import load_store
from kraken.core.paths import layout_dirs, ensure_user_layout
from kraken.core.resolve import CORE_VERSION, ResolveError, catalog, resolve
from kraken.core.tentacle import discover_installed


POINTER = Path.home() / ".kraken" / "source"


def _git(root: Path, *argv: str) -> str:
    """Short git answer, or '' when this is not a usable checkout.

    A submodule checkout with a moved parent has a .git *file* pointing at a
    gitdir that no longer exists. That must degrade to '' and not raise, or
    `kraken doctor` breaks on exactly the machines that need it.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(root), *argv],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def _same_dir(a: str | Path, b: str | Path) -> bool:
    """True when two paths name the same directory.

    A string compare is not enough. On macOS `/tmp` is a symlink to
    `/private/tmp`, so a pointer written by install.sh reads back as a
    different string from the tree python imported — and every fresh install
    reported itself stale.
    """
    try:
        return Path(a).resolve() == Path(b).resolve()
    except OSError:
        return False


def install_checks() -> list[dict[str, Any]]:
    """Which kraken is actually running, and what is competing with it.

    `kraken` is a launcher, not a binary: something on PATH decides which
    source tree wins. When that goes wrong the traceback names a missing
    module and nothing else, so the whole path is reported here.
    """
    checks: list[dict[str, Any]] = []

    def ok(name: str, detail: str, passed: bool = True) -> None:
        checks.append({"name": name, "ok": passed, "detail": detail})

    pkg = Path(kraken.__file__).resolve().parent
    root = pkg.parent
    ok("install.source", str(root), (root / "kraken" / "core" / "cli.py").is_file())

    commit = _git(root, "rev-parse", "--short", "HEAD")
    if commit:
        dirty = _git(root, "status", "--porcelain")
        ok("install.revision", f"{commit}{' (dirty)' if dirty else ''}")
    else:
        # Normal for a Homebrew or pip install — neither is a git checkout.
        # Only reported, so `doctor` stays meaningful outside a dev clone.
        ok("install.revision", "not a git checkout (packaged install)")

    # A pip console script bakes its checkout path into an editable finder.
    # When that path dies, `import kraken` fails while the dist-info still
    # claims a healthy install.
    # A pip console script bakes its checkout path into an editable finder.
    # When that path dies, `import kraken` fails while the dist-info still
    # claims a healthy install. Finding one here means a console script likely
    # exists on PATH and may sit ahead of the launcher.
    stale = sorted(
        {str(d) for e in sys.path if e for d in Path(e).glob("kraken_cli-*.dist-info")}
    )
    if stale:
        ok(
            "install.pip_kraken_cli",
            f"{', '.join(stale)} — a pip kraken-cli is installed; run "
            "`python3 -m pip uninstall kraken-cli` so its console script "
            "cannot shadow the launcher",
            passed=False,
        )
    else:
        ok("install.pip_kraken_cli", "none")

    try:
        pointed = POINTER.read_text().strip()
    except OSError:
        pointed = ""
    if not pointed:
        # Normal for a packaged install. `KRAKEN_SRC` may also have been set
        # deliberately, so a mismatch is a note and not a failure.
        ok("install.pointer", f"absent ({POINTER})")
    elif pointed == str(root) or _same_dir(pointed, root):
        ok("install.pointer", f"{POINTER} → {root}")
    else:
        ok(
            "install.pointer",
            f"stale — {POINTER} → {pointed}, but this run used {root}. "
            f"Re-run install.sh or set KRAKEN_SRC",
        )

    on_path = {name: shutil.which(name) for name in ("kraken", "k")}
    found = {n: str(Path(p).resolve()) for n, p in on_path.items() if p}
    missing = [n for n, p in on_path.items() if not p]
    if found:
        detail = ", ".join(f"{n} → {p}" for n, p in sorted(found.items()))
        ok(
            "install.on_path",
            detail + (f" (not found: {', '.join(missing)})" if missing else ""),
        )
    else:
        ok("install.on_path", "kraken is not on PATH — run install.sh", passed=False)

    return checks


def next_actions(
    root: Path,
    installed: list[str] | None = None,
    checks: list[dict[str, Any]] | None = None,
) -> list[str]:
    names = set(installed or [])
    if not names:
        names = {str(s.get("name")) for s in discover_installed()}
        names.update(catalog(root))
    steps: list[str] = []
    if any(not c["ok"] for c in (checks or []) if c["name"].startswith("install.")):
        steps.append("repair: KRAKEN_SRC=<path to checkout> sh ./install.sh")
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

    checks.extend(install_checks())

    for folder in (*layout_dirs().values(), "tentacles"):
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
        "next": next_actions(root, list(nodes), checks),
    }
