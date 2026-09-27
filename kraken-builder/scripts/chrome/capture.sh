#!/bin/sh
# Capture PNG of the front Chrome window and optional 8s screen recording.
# Output: scripts/chrome/media/
set -eu
ROOT="$(cd "$(dirname "$0")" && pwd)"
MEDIA="$ROOT/media"
mkdir -p "$MEDIA"
STAMP="$(date +%Y%m%d-%H%M%S)"
PNG="$MEDIA/chrome-$STAMP.png"
MOV="$MEDIA/chrome-$STAMP.mov"

osascript <<'APPLESCRIPT'
tell application "Google Chrome" to activate
delay 0.4
APPLESCRIPT

# Window screenshot of Chrome if possible; else full display.
WID="$(osascript -e 'tell application "Google Chrome" to id of window 1' 2>/dev/null || true)"
if [ -n "$WID" ]; then
  screencapture -x -l "$WID" "$PNG" 2>/dev/null || screencapture -x "$PNG"
else
  screencapture -x "$PNG"
fi
echo "png $PNG"

if [ "${KRAKEN_RECORD:-0}" = "1" ]; then
  # Timed recording of the main display. Stop after 8 seconds.
  screencapture -v -V 8 "$MOV" 2>/dev/null || echo "screencapture -V not available; png only"
  [ -f "$MOV" ] && echo "mov $MOV"
fi
