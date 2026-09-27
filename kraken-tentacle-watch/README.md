# watch

Free Kraken tentacle. MIT. Do not import `kraken.core`.

**One binary. Many tentacles.** `watch` is the arm that turns host, user, browser, and media signals into the same JSON envelope Kraken already knows how to grant, hook, and notify.

```
JSON in → policy → exec → JSON out
```

## What it does

| Layer | Action | Default |
|---|---|---|
| System | disk, load, memory snapshot | fixture-safe, no extra daemons |
| User | directory hash / file change | `$KRAKEN_HOME/.kraken/data/watch/` |
| Browser | HTTP title + body hash | fixture unless `KRAKEN_WATCH_LIVE=1` |
| Media | attach screenshot or an existing file | fixture unless live + a local capture tool |
| Notify | stdout, webhook, Slack, Discord, ntfy, desktop | webhook failures swallowed at 4s |
| Tasks | user or system units | exec is default-deny (`KRAKEN_WATCH_EXEC=1`) |

Live Chrome JS injection is **not** reimplemented here. Pair with the official `browse-js` / `chrome-capture` tentacles and set `KRAKEN_CHROME=1` when you actually want the Default profile.

## Documentation

| Doc | Contents |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the tentacle was built, layout, pipeline |
| [docs/USAGE.md](docs/USAGE.md) | Install, actions, flags, example profiles |
| [docs/SUCKERS.md](docs/SUCKERS.md) | How to add another hook tentacle |
| [docs/CROSS_COMPILE.md](docs/CROSS_COMPILE.md) | Safe `CGO_ENABLED=0` matrix + receipts |
| [docs/DOCKER.md](docs/DOCKER.md) | Alpine image + GitHub Actions |
| [docs/TESTING.md](docs/TESTING.md) | Contract, e2e scenarios, benchmarks |
| [docs/SECURITY.md](docs/SECURITY.md) | Default-deny, grants, what not to point at |
| [contrib/cli-watch-snippet.md](contrib/cli-watch-snippet.md) | Optional `kraken watch` core patch |
| [branding/index.html](branding/index.html) | Mark, hero, test screencasts, GIFs |

## Docker / CI

Minimum Alpine image and GitHub Actions (`compile`, `e2e` matrix, `kraken-e2e`, `image`) live in `Dockerfile` and `.github/workflows/ci.yml`. Full notes: `docs/DOCKER.md`.

```bash
docker build -t kraken-watch:local .
docker run --rm --network=none -e KRAKEN_OFFLINE=1 kraken-watch:local
bash scripts/ci-test.sh          # same suite without a daemon
```

Suckers: `suckers/after-watch.yaml` (watch-stamp convert) and `suckers/watch-log.yaml` (echo-bin ping). The image copies `docker/config.yaml` into `$KRAKEN_HOME/.kraken/config.yaml` so `kraken run watch ping` attaches `_hooks`.

## Install

```bash
./build.sh
kraken tentacle add .
kraken tentacle add examples/tentacles/watch-stamp
kraken list
kraken run watch ping
```

`./build.sh` cross-compiles CGO-free Go binaries for linux/darwin/windows × amd64/arm64. That is the documented Kraken shipping format (`docs/CONTRACT.md`, `docs/PLATFORMS.md`).

`handler.sh` is the manifest `binary:` so `tentacle add` works before a compile: it prefers `dist/watch-$GOOS-$GOARCH`, then `go run`, then `handler.py`.

## Command

Core verbs stay `kraken run NAME ACTION --payload JSON`.

```bash
kraken run watch plan   --payload '{"name":"laptop","config":"config/watch.example.json"}'
kraken run watch apply  --payload '{"name":"laptop"}'
kraken run watch tick   --payload '{"name":"laptop"}'
kraken run watch browse --payload '{"url":"https://kraken.topta.co"}'
kraken run watch capture --payload '{}'
kraken run watch notify --payload '{"summary":"disk warn","level":"warn","webhook":"https://example.invalid/hook"}'
kraken run watch start  --payload '{"name":"laptop","interval_sec":60}'
```

Flag front-end (same payload):

```bash
./contrib/kraken-watch.sh --help
./contrib/kraken-watch.sh tick --name laptop --config config/watch.example.json
./contrib/kraken-watch.sh browse --url https://kraken.topta.co --live
```

To make `kraken watch` itself a first-class verb the way `kraken monitor` is, copy `contrib/cli-watch-snippet.md` into `kraken/core/cli.py`.

## Flags / payload

| Flag | Payload key | Meaning |
|---|---|---|
| `--name` | `name` | Profile under `~/.kraken/data/watch/` |
| `--config` | `config` | JSON file (example in `config/watch.example.json`) |
| `--url` | `url` | Browser target |
| `--webhook` | `webhook` | Extra HTTP notify channel |
| `--kind` | `kind` | `system` `user` `browser` `media` `task` |
| `--target` | `id` | add/remove |
| `--interval` | `interval_sec` | scheduler plan |
| `--attach-screen` | `attach_screen` | screenshot on fired alert |
| `--attach-media` | `attach` | existing file |
| `--notify` | `channels[]` | backend type |
| `--live` | `live` | real HTTP / OS capture tools |
| `--dry-run` | *(action=plan)* | print unit + config, do not tick |
| `--loop --timeout N` | wrapper only | repeated tick, still no daemon |

Environment:

| Variable | Meaning |
|---|---|
| `KRAKEN_HOME` | Relocate `.kraken` |
| `KRAKEN_OFFLINE=1` | Force fixtures |
| `KRAKEN_WATCH_LIVE=1` | Real HTTP + screenshot tools |
| `KRAKEN_CHROME=1` | Hint to pair with browse-js |
| `KRAKEN_WATCH_EXEC=1` | Allow `task` exec (default deny) |
| `KRAKEN_NOTIFY_WEBHOOK` | Core + tentacle webhook |
| `KRAKEN_NOTIFY_STDOUT=1` | Print notify envelopes on stderr |

## Best practices this tentacle follows

- Contract v1, exit 0, `"ok": false` on app errors.
- No `kraken.core` import.
- State only under `$KRAKEN_HOME/.kraken/data/watch/`.
- Default deny for live capture and shell exec.
- No required daemon: `tick` is one evaluation (same idea as `hotreload`).
- `start` writes a **user** systemd timer / LaunchAgent / schtasks plan; it does not install a system service by itself.
- Hooks listed in `tentacle.yaml` point at *other* tentacles (`save-text`), never at `watch`.
- Notify backends match `docs/NOTIFY.md`: tentacle returns data; HTTP failures do not crash the CLI.
- Cross-compile with `CGO_ENABLED=0`. Missing platform stays `tested: false`.

## Security

This is a homelab observer for **your** machine. Do not point it at other people’s sessions, inboxes, or displays. Screen attach is an explicit, local capture for an alert you already own. Treat `KRAKEN_WATCH_EXEC=1` like `hotreload`’s command runner — whoever can `kraken run` owns the shell.

```bash
kraken grant watch
```

Core grant files are default-deny. Live browse/capture still also need the env flags above.

## Layout

```
tentacle.yaml          manifest
handler.sh             cross-platform dispatcher
handler.py             zero-Go fallback
cmd/watch              Go binary (canonical)
internal/*             contract, config, system, browser, media, notify, schedule
config/watch.example.json
contrib/kraken-watch.sh
contrib/cli-watch-snippet.md
hooks/notify-watch.yaml
workflows/watch-alerts.yaml
build.sh
```

## Workflow

```bash
kraken workflow run workflows/watch-alerts.yaml
```
