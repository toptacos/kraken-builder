#!/bin/sh
# Launch pass using Chrome Default (matt@topta.co).
# Opens site, GitHub, Search Console, X drafts. Captures PNG.
# Does not create accounts. Does not click Post.
set -eu
ROOT="$(cd "$(dirname "$0")" && pwd)"
PROFILE="${KRAKEN_CHROME_PROFILE:-Default}"
JS="$(tr '\n' ' ' < "$ROOT/inject.js")"
LOG="$ROOT/media/launch-log.txt"
mkdir -p "$ROOT/media"
: > "$LOG"

open_and_probe() {
  url="$1"
  name="$2"
  echo "== $name $url" | tee -a "$LOG"
  open -a "Google Chrome" --args --profile-directory="$PROFILE" "$url"
  sleep 4
  out="$(osascript "$ROOT/chrome-ops.applescript" "$url" "$JS" 2>/dev/null || echo '{"ok":false}')"
  echo "$out" | tee -a "$LOG"
  KRAKEN_RECORD="${KRAKEN_RECORD:-0}" sh "$ROOT/capture.sh" | tee -a "$LOG"
}

open_and_probe "https://kraken.topta.co" "home"
open_and_probe "https://kraken.topta.co/cli" "cli"
open_and_probe "https://kraken.topta.co/docs/tentacle" "tutorial"
open_and_probe "https://github.com/toptacos/kraken-builder" "github"
open_and_probe "https://search.google.com/search-console?resource_id=https://kraken.topta.co/" "search-console"

# X compose drafts — human clicks Post
open -a "Google Chrome" --args --profile-directory="$PROFILE" \
  "https://x.com/intent/tweet?text=Kraken%20CLI%20is%20open%20source%20MIT.%20One%20binary.%20Many%20tentacles.%0Acurl%20-fsSL%20https%3A//kraken.topta.co/install.sh%20%7C%20sh%0Akraken%20demo%0Ahttps%3A//kraken.topta.co"
sleep 2
open -a "Google Chrome" --args --profile-directory="$PROFILE" \
  "https://x.com/intent/tweet?text=Write%20a%20tentacle%20in%20any%20language.%20JSON%20in%2C%20JSON%20out.%20https%3A//kraken.topta.co/docs/tentacle"

echo "done. media in $ROOT/media" | tee -a "$LOG"
echo "human: Search Console submit sitemap, X Post, profile Subscribe"
