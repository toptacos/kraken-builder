#!/bin/sh
# Launch Google Chrome with the matt@topta.co profile (directory: Default).
set -eu
PROFILE="${KRAKEN_CHROME_PROFILE:-Default}"
URL="${1:-https://kraken.topta.co}"
open -a "Google Chrome" --args --profile-directory="$PROFILE" "$URL"
echo "opened $URL profile=$PROFILE"
