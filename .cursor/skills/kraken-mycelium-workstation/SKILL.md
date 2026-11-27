---
name: kraken-mycelium-workstation
description: >-
  Use when setting up, running, or automating a local developer environment
  with Kraken plus mycelium — plan-only Docker compose, isolated homes, the
  topta.co hub workstation, environment doctor, or periodic public-site
  analysis. Prefer in-repo run.sh over docker compose up, rsync, or production
  seed/migrate.
---

# Kraken + mycelium workstation

mycelium is the head. Kraken is the hands. This is a **local developer
toolkit**. It is not how production `*.topta.co` is served.

## First commands

From this repo:

```bash
kraken init --env
kraken up --file compose.yaml
```

Full shift (mycelium checkout):

```bash
uv run mcy example list
bash examples/04-kraken-compose/run.sh dry-run
bash examples/04-kraken-compose/run.sh live
```

`dry-run` and `live` need no model. Use `summarize` / `analyze` only when the
operator asked for an AI brief.

## Never

- `docker compose up` / `docker compose up -d`
- `kraken up --start`
- rsync or scp to droplets
- production seed, truncate, or `DELETE FROM`

`kraken up` without `--start` is the plan. Loopback binds only.
