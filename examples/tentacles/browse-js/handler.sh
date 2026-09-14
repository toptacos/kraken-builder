#!/bin/sh
# Dispatch: osascript on macOS when Chrome is present, else Node fixture.
# stdin JSON → stdout JSON. Core never imports this.
set -eu
DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
if [ "${KRAKEN_OFFLINE:-}" = "1" ] || ! command -v osascript >/dev/null 2>&1; then
  exec node "$DIR/fixture.js"
fi
if ! command -v node >/dev/null 2>&1; then
  exec osascript "$DIR/chrome.applescript"
fi
# Prefer fixture unless KRAKEN_CHROME=1 so CI/docs stay deterministic.
if [ "${KRAKEN_CHROME:-}" != "1" ]; then
  exec node "$DIR/fixture.js"
fi
exec osascript "$DIR/chrome.applescript"
