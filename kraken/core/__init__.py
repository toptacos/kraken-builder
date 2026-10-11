"""Public surface of kraken.core.

The re-exports are lazy on purpose (PEP 562). Importing one core module used
to execute this __init__, which pulled license (urllib), loader (yaml),
runner, and tentacle for every entry point -- so `kraken --help` paid for a
thread pool and an HTTP client it would never touch. Each name is resolved on
first use instead: `from kraken.core import run_named` and `import
kraken.core; kraken.core.LicenseError` both still work, and the import cost
lands on the command that needs it.
"""

from __future__ import annotations

import importlib
from typing import Any

_LAZY: dict[str, str] = {
    "load_arms": "kraken.core.loader",
    "Registry": "kraken.core.registry",
    "WorkflowQueue": "kraken.core.queue",
    "run_named": "kraken.core.runner",
    "list_all": "kraken.core.runner",
    "install_local": "kraken.core.tentacle",
    "assert_licensed": "kraken.core.license",
    "LicenseError": "kraken.core.license",
}

__all__ = list(_LAZY)


def __getattr__(name: str) -> Any:
    module = _LAZY.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(importlib.import_module(module), name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LAZY))
