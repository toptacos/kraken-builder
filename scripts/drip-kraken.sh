#!/bin/sh
# Record drip steps on api.topta.co for a register email. Does not blast a list.
# Day 0 install, day 2 write-a-tentacle, day 7 catalog.
set -eu
EMAIL="${1:-}"
if [ -z "$EMAIL" ]; then
  echo "usage: drip-kraken.sh you@example.com"
  exit 1
fi
API="${KRAKEN_API_BASE:-https://api.topta.co}"
curl -fsS -X POST "$API/api/kraken/beta" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"tentacle\":\"drip\"}" >/dev/null || true
curl -fsS -X POST "$API/api/kraken/contact" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"body\":\"drip day0 install https://kraken.topta.co/cli\",\"scope\":\"kraken\",\"source\":\"drip\"}"
echo "ok: drip recorded for $EMAIL"
echo "human send: day0 install, day2 https://kraken.topta.co/docs/tentacle, day7 https://kraken.topta.co/catalog"
