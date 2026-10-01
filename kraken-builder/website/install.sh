#!/bin/sh
# Kraken installer — copies nothing privileged. Delegates to the one real
# installer so this file and `install.sh` in the repo cannot drift.
#
# Kept as a separate file only because kraken.topta.co serves it at a URL.
set -eu

REPO_RAW="${KRAKEN_RAW:-https://raw.githubusercontent.com/toptacos/kraken-builder/main/install.sh}"

if ! command -v curl >/dev/null 2>&1; then
  echo "need curl on PATH" >&2
  exit 1
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT INT TERM

curl -fsSL "$REPO_RAW" -o "$tmp/install.sh"
sh "$tmp/install.sh" "$@"

cat <<'MSG'

Kraken is a local CLI — nothing was installed outside your home directory.
Troubleshooting: https://kraken.topta.co/docs.html
MSG
