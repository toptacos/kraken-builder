# Plan-only compose stub

Written by `kraken init --env`. Loopback binds. `docker.public: false`.
`kraken up --file compose.yaml` prints the plan and starts nothing.

```bash
kraken init --env --dir .
kraken up --file compose.yaml
```

For the mycelium-driven shift (doctor + inventory + report):

```bash
# from a mycelium checkout
bash examples/04-kraken-compose/run.sh dry-run
```

Never `docker compose up` or `kraken up --start` from an agent unless the
operator asked to start containers.
