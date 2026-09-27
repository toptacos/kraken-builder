# Using watch

## Install

```bash
./build.sh
kraken tentacle add .
kraken tentacle add examples/tentacles/watch-stamp
kraken list
kraken run watch ping
```

Copy `docker/config.yaml` hooks into `~/.kraken/config.yaml` if you want suckers on every run.

## Invocation shapes

Core has no plugin verb registry. All three are the same tentacle:

```bash
# 1. Contract (always works)
kraken run watch ACTION --payload '{"name":"laptop"}'

# 2. Flag wrapper shipped here
./contrib/kraken-watch.sh ACTION --name laptop --config config/watch.example.json

# 3. First-class verb (optional core patch)
#    see contrib/cli-watch-snippet.md
kraken watch ACTION --name laptop
```

## Actions

| Action | Payload highlights | Result |
|---|---|---|
| `ping` | — | arm, version, platform |
| `plan` | `name`, `interval_sec`, `config` | scheduler unit + paths |
| `build` | `host_only`, `out` | cross-compile + write profile |
| `apply` | profile fields | writes `~/.kraken/data/watch/<name>.json` |
| `status` / `list` | `name` | config + state + snapshot |
| `add` / `remove` | `id`, `kind`, `url`/`path` | mutate targets |
| `tick` | `name`, `live`, `attach_screen` | evaluate targets, maybe notify |
| `snapshot` | `name` | disk / load / memory |
| `browse` | `url`, `live` | title + hash (fixture unless live) |
| `capture` | `attach`/`file`, `live` | screenshot or fixture file |
| `notify` | `summary`, `level`, `webhook` | channel results |
| `task` | `level`, `command`, `exec` | register; exec needs grant env |
| `start` / `stop` | `interval_sec` | write / drop user timer |
| `finish` | `raw`, `patch` | sucker merge (called by core) |
| `clear` | `name` | delete profile state |

Unknown actions return `"ok": false`, `"error": {"code":"unknown_action"}`, exit 0.

## Flags (`contrib/kraken-watch.sh`)

`--config` `--name` `--url` `--webhook` `--kind` `--target` `--interval` `--attach-screen` `--attach-media` `--notify` `--summary` `--level` `--live` `--payload` `--dry-run` `--loop` `--timeout`

## Environment

| Variable | Meaning |
|---|---|
| `KRAKEN_HOME` | Relocate `.kraken` |
| `KRAKEN_OFFLINE=1` | Force fixtures |
| `KRAKEN_WATCH_LIVE=1` | Real HTTP + local capture tools |
| `KRAKEN_CHROME=1` | Hint to pair with browse-js |
| `KRAKEN_WATCH_EXEC=1` | Allow `task` exec (default deny) |
| `KRAKEN_NOTIFY_WEBHOOK` | HTTP notify (core + tentacle) |
| `KRAKEN_NOTIFY_STDOUT=1` | Print notify envelopes |
| `KRAKEN_NTFY_TOPIC` | Core ntfy backend |

## Example profiles

Homelab disk + site:

```bash
kraken run watch apply --payload '{
  "name": "pi",
  "interval_sec": 60,
  "targets": [
    {"id":"root","kind":"system","check":"disk","path":"/","warn_pct":85,"crit_pct":95,"on":"warn"},
    {"id":"site","kind":"browser","url":"https://kraken.topta.co","expect_status":200,"on":"change"}
  ]
}'
kraken run watch tick --payload '{"name":"pi"}'
```

User notes directory:

```bash
kraken run watch tick --payload '{
  "name": "notes",
  "targets": [{"id":"md","kind":"user","path":"~/Notes","patterns":["*.md"],"on":"change"}]
}'
```

Attach a screenshot only when something is already critical:

```bash
kraken run watch tick --payload '{
  "name": "desk",
  "attach_screen": true,
  "targets": [{"id":"disk","kind":"system","check":"disk","path":"/","crit_pct":95,"on":"crit"}]
}'
```

Workflow:

```bash
kraken workflow run workflows/watch-alerts.yaml
```

## Scheduler

`start` writes a **user** unit (systemd `--user`, LaunchAgent, or schtasks). It does not `systemctl enable` as root. `tick` from cron/`watch` on the host is the daemon-free option:

```bash
* * * * * KRAKEN_HOME=$HOME kraken run watch tick --payload '{"name":"laptop"}'
```
