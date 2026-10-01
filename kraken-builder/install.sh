#!/bin/sh
# Quick install. Puts `kraken` on PATH. MIT core: https://github.com/toptacos/kraken-builder
#
# Deliberately no `pip install`. A pip console script hardcodes two absolute
# paths: the interpreter in its shebang, and — for `pip install -e .` — the
# checkout location in an editable finder. Move or rename the repo and you get
#   ModuleNotFoundError: No module named 'kraken'
# with nothing pointing at the cause. This installer instead writes a launcher
# that re-resolves the source tree on every run, and records the chosen path in
# $HOME/.kraken/source so a later move is a one-line fix.
set -eu

REPO="${KRAKEN_REPO:-https://github.com/toptacos/kraken-builder.git}"
SRC="${KRAKEN_SRC:-$HOME/.kraken/src}"
BIN_DIR="${KRAKEN_BIN:-$HOME/.local/bin}"
POINTER="$HOME/.kraken/source"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "need $1 on PATH" >&2; exit 1; }
}
need git
need python3
python3 -c "import yaml" 2>/dev/null || python3 -m pip install --user pyyaml >/dev/null

mkdir -p "$(dirname "$SRC")" "$BIN_DIR" "$HOME/.kraken"

if [ -n "${KRAKEN_SRC:-}" ] && [ -f "$SRC/kraken/core/cli.py" ]; then
  echo "ok: using existing checkout $SRC"
elif [ -d "$SRC/.git" ]; then
  git -C "$SRC" pull --ff-only
elif [ -f "$SRC/kraken/core/cli.py" ]; then
  :
else
  git clone --depth 1 "$REPO" "$SRC"
fi

# The old guard was `[ -f "$SRC/kraken/__main__.py" ]`, which passes for a tree
# that has lost kraken/core. Check the module the console entry imports.
if [ ! -f "$SRC/kraken/core/cli.py" ]; then
  echo "install: $SRC is not a kraken checkout (no kraken/core/cli.py)" >&2
  exit 1
fi

printf '%s\n' "$SRC" > "$POINTER"
chmod 0600 "$POINTER"

# `$0` is meaningless under `curl … | sh`, which is how the README installs it,
# so the launcher's location cannot be derived from this script's own path.
# $SRC is the reliable answer: it is a real checkout by this point, whether it
# was cloned, passed in, or already present.
LAUNCHER=""
for candidate in "$SRC/scripts/kraken" "$(dirname "$0")/scripts/kraken"; do
  if [ -f "$candidate" ]; then
    LAUNCHER="$candidate"
    break
  fi
done
if [ -z "$LAUNCHER" ]; then
  cat >&2 <<MSG
install: cannot find scripts/kraken in $SRC.
install: the source tree is incomplete — it must contain scripts/kraken.
install: re-clone with: git clone --depth 1 $REPO "$SRC"
MSG
  exit 1
fi

# A `kraken` earlier on PATH than $BIN_DIR beats the launcher below. The usual
# culprit is a stale `pip install -e .` console script, and it fails with a
# traceback that looks nothing like shadowing. Name it now, not later.
shadow="$(command -v kraken 2>/dev/null || true)"
if [ -n "$shadow" ]; then
  shadow_dir="$(CDPATH= cd -- "$(dirname "$shadow")" 2>/dev/null && pwd || echo "$shadow")"
  bin_dir="$(CDPATH= cd -- "$BIN_DIR" && pwd)"
  if [ "$shadow_dir" != "$bin_dir" ]; then
    cat >&2 <<MSG
install: warning — $shadow comes before $BIN_DIR on PATH.
install: the launcher installed just now would be shadowed by it.
install: if you previously ran 'pip install -e .' or 'pip install kraken-cli',
install: remove that stale console script first:
install:     python3 -m pip uninstall kraken-cli
install: or put $BIN_DIR earlier in PATH.
MSG
  fi
fi

install -m 0755 "$LAUNCHER" "$BIN_DIR/kraken"
ln -sf "$BIN_DIR/kraken" "$BIN_DIR/k"
echo "ok: k is an alias for kraken (PATH). Tentacle names are unchanged: k run wx"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "Add to PATH: export PATH=\"$BIN_DIR:\$PATH\"" ;;
esac

export PYTHONPATH="$SRC${PYTHONPATH:+:$PYTHONPATH}"
export PATH="$BIN_DIR:$PATH"
python3 -m kraken init
python3 -m kraken vanilla
echo "ok: kraken is on $BIN_DIR/kraken"
echo "first JSON (geo lookup fixture):"
python3 -m kraken demo || python3 -m kraken run geo lookup --payload '{"ip":"1.1.1.1"}' || true
echo "next: kraken doctor"
echo "then: kraken run filesort scan --payload '{\"path\":\".\"}'"
echo "moving this checkout later? re-run this script, or set KRAKEN_SRC."
echo "docs: https://kraken.topta.co/cli"
echo "troubleshooting: docs/TROUBLESHOOTING.md"
echo "source: https://github.com/toptacos/kraken-builder"
