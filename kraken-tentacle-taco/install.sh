#!/bin/sh
# Local drop. Does not curl https://kraken.topta.co.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
DEST="${KRAKEN_HOME:-$HOME}/.kraken/tentacles/taco"
mkdir -p "$DEST"
# copy tree minus tests noise optional
cp -R "$ROOT/handler.py" "$ROOT/handler.sh" "$ROOT/tentacle.yaml" "$DEST/"
cp -R "$ROOT/connectors" "$ROOT/bots" "$ROOT/bin" "$ROOT/docs" "$ROOT/suckers" "$ROOT/workflows" "$ROOT/ui" "$DEST/" 2>/dev/null || true
mkdir -p "${KRAKEN_HOME:-$HOME}/.kraken/license"
if [ "${KRAKEN_LICENSE:-}" = "premium" ]; then
  printf '%s\n' '{"license":"premium","arm":"taco"}' > "${KRAKEN_HOME:-$HOME}/.kraken/license/taco.json"
  chmod 600 "${KRAKEN_HOME:-$HOME}/.kraken/license/taco.json"
fi
KRAKEN_LICENSE="${KRAKEN_LICENSE:-premium}" python3 "$DEST/bin/kraken" taco after_install
echo "installed $DEST"
echo "verify: python3 $ROOT/scripts/sign-drop.py --verify"
