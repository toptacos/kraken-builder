"""Optional billing package. MIT core runs without this.

Install extra: pip install 'kraken-cli[billing]'  (same tree today).
Env:
  KRAKEN_API_BASE          default https://api.topta.co
  KRAKEN_LICENSE_OFFLINE=1 skip remote verify
  KRAKEN_LICENSE_REMOTE=1  force POST /api/kraken/licenses/verify
  KRAKEN_NOTIFY_STDOUT=1   verbose JSON lines on stderr via notify
  KRAKEN_BILLING_LOG=1     extra billing logs even without notify stdout

Hooks this package listens for (optional tentacle):
  after_install  — no-op unless tentacle.license is premium
  on_error       — if LicenseError, emit billing.denied

Free tentacles never call home. This package only talks to api.topta.co
when a premium tentacle is asserted and remote verify is on.
"""

from kraken.billing.client import BillingClient, log
from kraken.core.license import (
    LicenseError,
    assert_licensed,
    load_store,
    set_key,
    upgrade,
    verify_remote,
)

__all__ = [
    "BillingClient",
    "LicenseError",
    "assert_licensed",
    "load_store",
    "set_key",
    "upgrade",
    "verify_remote",
    "log",
]
