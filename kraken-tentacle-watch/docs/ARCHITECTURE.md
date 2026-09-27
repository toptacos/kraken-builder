# How watch was built

`watch` is a Kraken **tentacle**, not an in-process arm and not a fork of core.

```
JSON in → policy (core) → exec (this binary) → JSON out
```

Core never imports this source. The only coupling is `docs/CONTRACT.md` in `toptacos/kraken-builder`: protocol `v: 1`, exit 0, `"ok": false` for application errors.

## Why Go

Kraken’s contract lists Go, Rust, C, PyInstaller, FrankenPHP, and Bash. Go was chosen because:

- `CGO_ENABLED=0` yields one static file per `GOOS/GOARCH` with no libc pin
- `//go:build windows` / `!windows` keeps syscall graphs legal on every target
- The same stdin/stdout envelope works on the host via `go run` before `dist/` exists

Python `handler.py` and POSIX `handler.sh` are fallbacks, not the shipping form.

## Layout

```
cmd/watch/main.go          dispatcher (actions)
internal/contract          protocol v1 read/write
internal/config            watch profile JSON
internal/state             $KRAKEN_HOME/.kraken/data/watch
internal/system            disk / load / memory / tree hash
internal/browser           HTTP probe or fixture
internal/media             screenshot attach or fixture
internal/notify            stdout / webhook / slack / discord / ntfy / desktop
internal/schedule          user systemd / launchd / schtasks plans
handler.sh                 dist binary → go run → python3
handler.py                 zero-Go fixture
examples/tentacles/watch-stamp   sucker that returns result.patch
suckers/*.yaml             named hook rows (copy into config)
```

## Build pipeline

```bash
CGO_ENABLED=0 GOOS=$os GOARCH=$arch \
  go build -trimpath -buildvcs=false -ldflags "-s -w" \
  -o dist/watch-$os-$arch ./cmd/watch
```

- `-trimpath` strips builder paths from the binary
- `-buildvcs=false` keeps two checkouts from embedding different git dirt
- `-ldflags "-s -w"` drops symbols
- `go version -m dist/watch-*` must show `CGO_ENABLED=0` and the intended `GOOS`/`GOARCH`

`./build.sh` writes `dist/SHA256SUMS` and `dist/*.buildinfo`. `./build.sh --host` builds only the machine you are on.

## Runtime selection

`tentacle.yaml` points at `handler.sh` so `kraken tentacle add` works before a compile:

1. `dist/watch-$GOOS-$GOARCH[.exe]` if present (staged to `$TMPDIR` when the install mount is `noexec`)
2. `go run ./cmd/watch` if a toolchain exists
3. `python3 handler.py`

## What core does around a run

```
resolve → license → before_run hooks → invoke watch → after_run|on_error → notify
```

If an `after_run` hook returns `{result: {patch: {…}}}` and `watch` lists `finish`, core calls `watch finish` and sets `finished: true`. That is how `watch-stamp` stamps an envelope without importing core.

## What was deliberately not built

- No daemon. `tick` is one evaluation; `start` only writes a *user* unit.
- No Chrome JS injection. Pair `browse-js` + `KRAKEN_CHROME=1`.
- No system-wide service install. System units stay grant-gated.
- `task` exec is default-deny (`KRAKEN_WATCH_EXEC=1`).
- Live HTTP / screenshot tools stay behind `KRAKEN_WATCH_LIVE=1` or `KRAKEN_OFFLINE=1`.
