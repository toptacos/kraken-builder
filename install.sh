#!/bin/sh
# Quick install. Puts `kraken` on PATH. MIT core: https://github.com/toptacos/kraken-builder
set -eu
REPO="${KRAKEN_REPO:-https://github.com/toptacos/kraken-builder.git}"
SRC="${KRAKEN_SRC:-$HOME/.kraken/src}"
BIN_DIR="${KRAKEN_BIN:-$HOME/.local/bin}"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "need $1 on PATH" >&2; exit 1; }
}
need git
need python3
python3 -c "import yaml" 2>/dev/null || python3 -m pip install --user pyyaml >/dev/null

mkdir -p "$SRC" "$BIN_DIR" "$HOME/.kraken"
if [ -d "$SRC/.git" ]; then
  git -C "$SRC" pull --ff-only
elif [ -f "$SRC/kraken/__main__.py" ]; then
  :
else
  git clone --depth 1 "$REPO" "$SRC"
fi

cat > "$BIN_DIR/kraken" <<EOF
#!/bin/sh
set -eu
export PYTHONPATH="$SRC\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 -m kraken "\$@"
EOF
chmod 0755 "$BIN_DIR/kraken"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "Add to PATH: export PATH=\"$BIN_DIR:\$PATH\"" ;;
esac

export PYTHONPATH="$SRC${PYTHONPATH:+:$PYTHONPATH}"
export PATH="$BIN_DIR:$PATH"
python3 -m kraken init
python3 -m kraken vanilla
echo "ok: kraken is on $BIN_DIR/kraken"
echo "next: kraken self plan"
echo "docs: https://kraken.topta.co/cli"
echo "source: https://github.com/toptacos/kraken-builder"
