#!/bin/sh
# Check that the install script copies are in sync.
#
# Usage: scripts/check-installer.sh
# Exit 0 = in sync, exit 1 = drift detected.

set -eu

CANONICAL="$(dirname "$0")/../install.sh"
MONOREPO="${KRAKEN_MONOREPO:-$HOME/Projects/Companies/TopTacos/toptaco-monorepo/applications/kraken/public/install.sh}"

if [ ! -f "$CANONICAL" ]; then
  echo "check-installer: canonical install.sh not found at $CANONICAL" >&2
  exit 1
fi

if [ ! -f "$MONOREPO" ]; then
  echo "check-installer: monorepo install.sh not found at $MONOREPO" >&2
  echo "set KRAKEN_MONOREPO to the correct path" >&2
  exit 1
fi

# Compare everything after the "set -eu" line (skips header comments)
canonical_body="$(sed -n '/^set -eu$/,$p' "$CANONICAL" | tail -n +2)"
monorepo_body="$(sed -n '/^set -eu$/,$p' "$MONOREPO" | tail -n +2)"

if [ "$canonical_body" = "$monorepo_body" ]; then
  echo "ok: install scripts are in sync"
  exit 0
else
  echo "drift: install scripts differ" >&2
  echo "  canonical: $CANONICAL" >&2
  echo "  monorepo:  $MONOREPO" >&2
  echo "diff:" >&2
  echo "$canonical_body" > /tmp/kraken-canonical-install.sh
  echo "$monorepo_body" > /tmp/kraken-monorepo-install.sh
  diff /tmp/kraken-canonical-install.sh /tmp/kraken-monorepo-install.sh >&2 || true
  rm -f /tmp/kraken-canonical-install.sh /tmp/kraken-monorepo-install.sh
  exit 1
fi
