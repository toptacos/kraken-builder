#!/bin/sh
# Add URL-prefix properties in Search Console using Chrome Default (matt@topta.co).
# HTML file google8c292cfe0da6151b.html must already be at each site root.
# Stay on matt@topta.co — if the page says mattmcachran@gmail.com, switch accounts first.
set -eu
SITES="${SITES:-https://kraken.topta.co/ https://topta.co/ https://tacos.topta.co/ https://music.topta.co/ https://blog.topta.co/ https://profile.topta.co/ https://dashboard.topta.co/ https://discgolf.topta.co/ https://ai.topta.co/ https://portfolio.topta.co/}"
LOG="$(cd "$(dirname "$0")" && pwd)/media/gsc-properties.log"
mkdir -p "$(dirname "$LOG")"
: > "$LOG"

# Prefer the Search Console tab if one exists; otherwise use front tab.
osascript <<'EOF' >/dev/null
tell application "Google Chrome"
  activate
end tell
EOF

for url in $SITES; do
  echo "== $url" | tee -a "$LOG"
  osascript <<EOF
tell application "Google Chrome"
  set found to false
  repeat with w from 1 to (count of windows)
    repeat with t from 1 to (count of tabs of window w)
      if (URL of tab t of window w) contains "search.google.com/search-console" then
        set URL of tab t of window w to "https://search.google.com/search-console/ownership?resource_id=$url"
        set index of window w to 1
        set active tab index of window w to t
        set found to true
        exit repeat
      end if
    end repeat
    if found then exit repeat
  end repeat
  if not found then
    tell front window to set URL of active tab to "https://search.google.com/search-console/ownership?resource_id=$url"
  end if
end tell
EOF
  sleep 8
  osascript <<'EOF' | tee -a "$LOG"
tell application "Google Chrome"
  execute active tab of front window javascript "JSON.stringify({href:location.href,title:document.title,acct:(document.body.innerText||'').match(/Signed in as:[^\\n]+/)?.[0]||'',ok:/verified owner|Successfully verified|Overview/.test(document.body.innerText||'')})"
end tell
EOF
  echo | tee -a "$LOG"
done
echo "done. If acct is gmail, reopen with matt@topta.co and rerun." | tee -a "$LOG"
