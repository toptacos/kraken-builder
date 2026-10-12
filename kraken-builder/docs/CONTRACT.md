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

### `requires` — the exact versions this tentacle needs

Optional, and checked before your handler runs — at `kraken tentacle add`
and at every `kraken run`. An undeclared requirement is never probed, so a
manifest that asks for nothing spawns nothing to find out.

```yaml
requires:
  protocol: 1          # the envelope version core must speak
  core: ">=0.4.0"      # the kraken version this tentacle needs
  python: ">=3.11"     # the runtime your handler needs
  node: ">=18"
```

| Key | Checked against |
|---|---|
| `protocol` | core's protocol version (today 1) |
| `core` | the running kraken version |
| a tool name (`python`, `node`, `bash`, `php`, `ruby`, `perl`, `go`, `rustc`, `docker`, `git`, …) | the version installed on this machine |

Constraints use one grammar everywhere: `>=`, `<=`, `>`, `<`, `==`, `~`, `^`,
or space-separated AND (`">=3.11 <4"`). A bound that fails is a refusal, not
a traceback:

```
$ kraken run geo lookup
{"ok": false, "error": "geo requires python >=3.11; have 3.10.12"}
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

# Pin the release, the way you pin a docker image tag:
kraken tentacle add github.com/you/kraken-tentacle-weather@v1.2.3
# A tag that disagrees with the manifest is refused:
#   error: ...@v2.0.0 declares version 1.0.0; install the tag that matches it'
```

Or copy the binary next to a project `.kraken/config.yaml` entry. Restart not required if core re-reads the chain per invocation (slice 2). Slice 1 Python loader still scans `arms/` in-process for built-in examples.
