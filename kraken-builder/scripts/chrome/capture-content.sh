#!/bin/sh
# Capture branded stills of live Kraken pages in Chrome Default (matt@topta.co).
# Prefers window screencapture; falls back to Chrome headless --screenshot
# when the agent session cannot grab the framebuffer.
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
MEDIA="$ROOT/media"
PROFILE="${KRAKEN_CHROME_PROFILE:-Default}"
CHROME="${KRAKEN_CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
mkdir -p "$MEDIA"
LOG="$MEDIA/content-capture.log"
: > "$LOG"

headless_shot() {
  url="$1"
  png="$2"
  if [ ! -x "$CHROME" ]; then
    echo "no chrome binary" | tee -a "$LOG"
    return 1
  fi
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars \
    --window-size=1280,800 --screenshot="$png" "$url" >>"$LOG" 2>&1
}

capture_url() {
  name="$1"
  url="$2"
  echo "== $name $url" | tee -a "$LOG"
  open -a "Google Chrome" --args --profile-directory="$PROFILE" "$url" >/dev/null 2>&1 || true
  sleep 4
  osascript -e 'tell application "Google Chrome" to activate' >/dev/null 2>&1 || true
  sleep 1
  png="$MEDIA/${name}.png"
  WID="$(osascript -e 'tell application "Google Chrome" to id of window 1' 2>/dev/null || true)"
  if [ -n "$WID" ]; then
    screencapture -x -l "$WID" "$png" 2>>"$LOG" || true
  fi
  if [ ! -f "$png" ]; then
    screencapture -x "$png" 2>>"$LOG" || true
  fi
  if [ ! -f "$png" ]; then
    echo "screencapture unavailable, headless $name" | tee -a "$LOG"
    headless_shot "$url" "$png" || true
  fi
  if [ -f "$png" ]; then
    echo "png $png $(wc -c < "$png" | tr -d ' ')" | tee -a "$LOG"
  else
    echo "screencapture failed $name" | tee -a "$LOG"
  fi
}

capture_url home "https://kraken.topta.co/"
capture_url cli "https://kraken.topta.co/cli"
capture_url articles "https://kraken.topta.co/blog"
capture_url why-core "https://kraken.topta.co/blog/why-core-stays-small"
capture_url languages "https://kraken.topta.co/blog/tentacle-bash-go"
capture_url compile "https://kraken.topta.co/blog/compile-c-docker-suckers"
capture_url automate "https://kraken.topta.co/blog/automate-your-day"
capture_url lesson-01 "https://kraken.topta.co/blog/lesson-01-install"
capture_url job-pi "https://kraken.topta.co/blog/job-pi-photos"
capture_url job-jump "https://kraken.topta.co/blog/job-jump-host"
capture_url docs-tentacle "https://kraken.topta.co/docs/tentacle"
capture_url github "https://github.com/toptacos/kraken-builder"

if [ "${KRAKEN_RECORD:-0}" = "1" ]; then
  open -a "Google Chrome" --args --profile-directory="$PROFILE" "https://kraken.topta.co/cli" >/dev/null 2>&1 || true
  sleep 3
  osascript -e 'tell application "Google Chrome" to activate' >/dev/null 2>&1 || true
  mov="$MEDIA/install-tour.mov"
  screencapture -v -V 8 "$mov" 2>>"$LOG" || echo "video unavailable (no framebuffer)" | tee -a "$LOG"
  if [ -f "$mov" ]; then
    echo "mov $mov" | tee -a "$LOG"
  fi
fi

echo "done" | tee -a "$LOG"
ls -la "$MEDIA" | tee -a "$LOG"
