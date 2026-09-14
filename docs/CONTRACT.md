# Tentacle contract

A tentacle is a **separate repository** that ships:

1. `tentacle.yaml` (manifest)
2. One executable per OS (or a script during development)
3. Optional `README` and tests

It must not depend on kraken-core source. It depends on this contract only.

## tentacle.yaml

```yaml
name: pi-host
version: 0.1.0
runtime: binary
binary:
  linux: dist/pi-host-linux-amd64
  darwin: dist/pi-host-darwin-arm64
  windows: dist/pi-host-windows-amd64.exe
actions: [status, uname]
timeout_sec: 30
data_dir: data
```

## Invoke

Core runs `binary` with the JSON request on stdin. The process writes one JSON object to stdout and exits 0.

Non-zero exit is a transport failure. Application failures use `"ok": false` and exit 0.

## Languages

Go, Rust, PHP (FrankenPHP micro-binary), Python + PyInstaller, C, Bash for fixtures. If it can read stdin and write JSON, it is a tentacle.

## Adding a tentacle on a device

```bash
kraken tentacle add github.com/you/kraken-tentacle-weather
# unpacks into ~/.kraken/tentacles/weather
kraken run weather forecast --payload '{"zip":"27284"}'
```

Or copy the binary next to a project `.kraken/config.yaml` entry. Restart not required if core re-reads the chain per invocation (slice 2). Slice 1 Python loader still scans `arms/` in-process for built-in examples.
