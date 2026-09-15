#!/bin/sh
# Capture branded stills of live Kraken pages in Chrome Default (matt@topta.co).
set -eu
ROOT="$(cd "$(dirname "$0")" && pwd)"
MEDIA="$ROOT/media"
PROFILE="${KRAKEN_CHROME_PROFILE:-Default}"
mkdir -p "$MEDIA"
LOG="$MEDIA/content-capture.log"
: > "$LOG"

capture_url() {
  name="$1"
  url="$2"
  echo "== $name $url" | tee -a "$LOG"
  open -a "Google Chrome" --args --profile-directory="$PROFILE" "$url"
  sleep 5
  osascript -e 'tell application "Google Chrome" to activate' >/dev/null 2>&1 || true
  sleep 1
  png="$MEDIA/${name}.png"
  WID="$(osascript -e 'tell application "Google Chrome" to id of window 1' 2>/dev/null || true)"
  if [ -n "$WID" ]; then
    screencapture -x -l "$WID" "$png" 2>>"$LOG" || screencapture -x "$png" 2>>"$LOG" || echo "screencapture failed $name" | tee -a "$LOG"
  else
    screencapture -x "$png" 2>>"$LOG" || echo "screencapture failed $name" | tee -a "$LOG"
  fi
  [ -f "$png" ] && echo "png $png $(wc -c < "$png")" | tee -a "$LOG"
}

capture_url home "https://kraken.topta.co/"
capture_url cli "https://kraken.topta.co/cli"
capture_url articles "https://kraken.topta.co/blog"
capture_url why-core "https://kraken.topta.co/blog/why-core-stays-small"
capture_url languages "https://kraken.topta.co/blog/tentacle-bash-go"
capture_url compile "https://kraken.topta.co/blog/compile-c-docker-suckers"
capture_url automate "https://kraken.topta.co/blog/automate-your-day"
capture_url docs-tentacle "https://kraken.topta.co/docs/tentacle"
capture_url github "https://github.com/toptacos/kraken-builder"

if [ "${KRAKEN_RECORD:-0}" = "1" ]; then
  open -a "Google Chrome" --args --profile-directory="$PROFILE" "https://kraken.topta.co/cli"
  sleep 3
  osascript -e 'tell application "Google Chrome" to activate' >/dev/null 2>&1 || true
  mov="$MEDIA/install-tour.mov"
  screencapture -v -V 8 "$mov" 2>>"$LOG" || echo "video unavailable" | tee -a "$LOG"
  [ -f "$mov" ] && echo "mov $mov" | tee -a "$LOG"
fi

echo "done" | tee -a "$LOG"
ls -la "$MEDIA" | tee -a "$LOG"
