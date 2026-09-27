# Cross-compiling watch safely

```bash
./build.sh           # six GOOS/GOARCH pairs + SHA256SUMS + buildinfo
./build.sh --host    # this machine only
```

Every invoke is:

```bash
CGO_ENABLED=0 GOOS=$os GOARCH=$arch \
  go build -trimpath -buildvcs=false -ldflags "-s -w" \
  -o dist/watch-$os-$arch ./cmd/watch
```

Windows names end in `.exe`.

## Why CGO stays off

Host `CGO_ENABLED` may be 1. The script overrides it. CGO-on cross-builds need a cross-gcc and pin libc. Kraken tentacles must run on Alpine and Pi images without that.

`go version -m dist/watch-linux-amd64` must contain:

```
build	-compiler=gc
build	CGO_ENABLED=0
build	GOOS=linux
build	GOARCH=amd64
```

`scripts/verify-dist.sh` fails the build if that receipt is wrong.

## Targets

| Artifact | Format | Executed in this repo’s CI |
|---|---|---|
| `watch-linux-amd64` | ELF | yes (Ubuntu + this host) |
| `watch-linux-arm64` | ELF | compile-only |
| `watch-darwin-amd64` | Mach-O | compile-only |
| `watch-darwin-arm64` | Mach-O | compile-only (`macos-latest` runs tests via `go run` / python) |
| `watch-windows-amd64.exe` | PE | compile-only |
| `watch-windows-arm64.exe` | PE | compile-only |

`tentacle.yaml` `platforms.*.tested` is `true` only for linux-amd64 until an arm64/macOS/Windows runner executes the binary.

## OS-specific source

```
internal/system/unix.go      //go:build !windows
internal/system/windows.go   //go:build windows
```

`GOOS=windows go build ./cmd/watch` is the compile check that those tags work.

## Not included

Codesign (Gatekeeper / SmartScreen), `lipo` universal Mac binaries, QEMU execution of arm64. Those are release-engineering steps on top of `go build`.
