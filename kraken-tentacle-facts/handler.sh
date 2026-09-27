#!/usr/bin/env bash
# facts — POSIX-ish bash handler. JSON is printf-built from shell-safe fields.
set -eu
raw=$(cat || true)
[ -n "$raw" ] || raw='{"action":"ping"}'

# Extract "action":"..." without jq. First match only.
action=$(printf '%s' "$raw" | tr '\n' ' ' | sed -n 's/.*"action"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -n "$action" ] || action=ping

esc() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

ok() {
  printf '{"v":1,"id":null,"ok":true,"result":%s}\n' "$1"
}

err() {
  printf '{"v":1,"id":null,"ok":false,"error":{"code":"%s","message":"%s"}}\n' "$(esc "$1")" "$(esc "$2")"
}

host=$(hostname 2>/dev/null || printf 'unknown')
user=${USER:-${USERNAME:-unknown}}
sys=$(uname -s 2>/dev/null || printf 'unknown')
mach=$(uname -m 2>/dev/null || printf 'unknown')
offline=false
[ "${KRAKEN_OFFLINE:-}" = "1" ] && offline=true
cwd=$(pwd)
khome=${KRAKEN_HOME:-}

case "$action" in
  ping|"")
    ok "{\"arm\":\"facts\",\"version\":\"0.1.0\",\"protocol\":1,\"runtime\":\"bash\"}"
    ;;
  host)
    ok "{\"arm\":\"facts\",\"hostname\":\"$(esc "$host")\",\"user\":\"$(esc "$user")\",\"system\":\"$(esc "$sys")\",\"machine\":\"$(esc "$mach")\",\"offline\":$offline}"
    ;;
  env)
    ok "{\"arm\":\"facts\",\"env\":{\"KRAKEN_HOME\":\"$(esc "$khome")\",\"KRAKEN_OFFLINE\":\"$(esc "${KRAKEN_OFFLINE:-}")\",\"HOME\":\"$(esc "${HOME:-}")\"}}"
    ;;
  snapshot)
    ok "{\"arm\":\"facts\",\"host\":\"$(esc "$host")\",\"system\":\"$(esc "$sys")\",\"cwd\":\"$(esc "$cwd")\",\"kraken_home\":\"$(esc "$khome")\"}"
    ;;
  finish)
    ok "{\"arm\":\"facts\",\"finished\":true}"
    ;;
  *)
    err unknown_action "unknown action $action"
    ;;
esac
