#!/bin/sh
# Manual + CI helper. Never echoes secrets.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
CREDS="${TOPTACO_CREDS:-$HOME/Projects/Companies/TopTacos/toptaco-creds.env}"
if [ -f "$CREDS" ]; then
  # shellcheck disable=SC1090
  set -a
  . "$CREDS"
  set +a
fi
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
cd "$ROOT"

echo "== unit =="
python3 -m pytest \
  tests/test_notes_tunnel_llm.py \
  tests/test_expose.py \
  tests/test_scopes_ca.py \
  tests/test_panel.py \
  tests/test_scourge_grant.py \
  tests/test_suckers.py \
  tests/test_install_wrapper.py \
  tests/test_license_upgrade.py \
  tests/test_wx_sucker.py \
  tests/test_browse_js.py \
  -q

echo "== install (isolated HOME) =="
python3 -m pytest tests/test_live_workflows.py::test_isolated_path_install -q

echo "== live auth / tokens / premium =="
if [ -n "${BLOG_ADMIN_EMAIL:-}" ] && [ -n "${BLOG_ADMIN_PASSWORD:-}" ]; then
  python3 -m pytest tests/test_live_auth_e2e.py tests/test_live_workflows.py -q
else
  echo "skip live: BLOG_ADMIN_EMAIL/PASSWORD unset"
fi

echo "ok"
