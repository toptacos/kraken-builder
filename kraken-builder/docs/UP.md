# `kraken up`

Core owns one Docker network, named `kraken`. Arms only *plan*; core runs it.
`berth` turns a `project.yaml` into a compose plan, and `kraken up` reconciles
that plan with core's network policy and hands it to Docker — or, by default,
just shows you what it would do.

## The split

| Step | Who | What |
|---|---|---|
| Read `project.yaml` | `berth` | Parses config, writes `compose.yaml` + `project.json` |
| Plan | `kraken up` | Reads that plan, normalizes the network, reports services and ports |
| Start | `kraken up --start` | Creates the shared network if absent, then `docker compose up -d` |

`berth` never starts a daemon. Neither does `kraken up`, unless you ask.

## Usage

```bash
# 1. Have an arm write a plan
kraken run berth up --payload '{"yaml":"name: demo\nservices:\n  api:\n    image: nginx:alpine"}'

# 2. Look at it. Starts nothing.
kraken up

# 3. Actually run it.
kraken up --start
```

Other inputs:

```bash
kraken up --file ./my-compose.yaml   # an explicit plan
kraken up --arm board                # read a specific planning arm's plan
```

The plan is found at `$KRAKEN_HOME/.kraken/data/<arm>/compose.yaml`, where
`<arm>` is the first of `berth`, `board`, `inlet` that wrote one.

## Output

```json
{
  "ok": true,
  "verb": "up",
  "project": "demo",
  "network": { "name": "kraken", "driver": "bridge", "enabled": true },
  "services": [
    { "name": "api", "image": "nginx:alpine", "ports": ["8080:80"],
      "networks": ["kraken"], "build": false }
  ],
  "orphan_networks": [],
  "public_ports": ["8080:80"],
  "daemon": false,
  "next": ["kraken up --start   # runs docker compose up -d on the shared network"]
}
```

Always JSON on stdout, so `kraken up | jq` works.

## The shared network name

`kraken` is the single shared name, and it is **bare** — not `kraken_dev`, not
`kraken_default`. `berth`, `sites/kraken.yaml`, and these docs all say `kraken`,
so core normalizes *to* it.

Arbitrary labels are still namespaced, so a project cannot claim the shared
network:

| Requested | Resolved |
|---|---|
| `kraken` | `kraken` |
| `kraken_ci` | `kraken_ci` |
| `lab` | `kraken_lab` |
| *(unset)* | `kraken` |

This matters more than it looks. When core and an arm disagreed about the name,
`docker compose up` still "succeeded" — the containers just ran on an isolated
network and never talked to each other. `kraken up` now reports
`network_mismatch` and names the services instead.

## Refusals

`kraken up` declines to act in three situations, each with a distinct code so a
script can branch on it:

| Code | When |
|---|---|
| `network_mismatch` | A service is attached to a network other than core's |
| `offline` | `--start` was passed but `KRAKEN_OFFLINE=1` is set |
| `no_docker` | `--start` was passed but `docker` is not on `PATH` |
| `no_plan` | No compose plan found and none was supplied |

## Safety notes

- **Plan-only by default.** `kraken up` without `--start` reads files and
  prints. It writes nothing, and starts nothing.
- **Ports are reported, never added.** A port only reaches Docker if it was
  already in the plan that the arm wrote. Core does not open one.
- **Secrets never appear.** Compose text is parsed, not echoed, and core does
  not write the plan back out. `sites/*.yaml` and plan files are public config.
- **Offline is a hard stop** for anything that would touch a network, not just
  telemetry.
