# AGENTS.md

Kraken (`kraken` / `k`) is a local-first JSON plugin runner. Not Payward.

## Commands

```bash
python3 -m pytest -q
kraken doctor
kraken init --home /tmp/kraken-home
kraken init --env --dir /tmp/reef
kraken up --file compose.yaml
```

## Local workstation (Kraken + mycelium)

Isolated homes. Docker plan-only. No production writes.

```bash
kraken init --env
kraken up --file compose.yaml
```

The full shift (mycelium + tentacles + report) lives in mycelium
`examples/04-kraken-compose/`. Do not `docker compose up` or
`kraken up --start`. Suggested prompt: "Plan my local stack (no containers)".

## Layout

- `kraken/core/` — CLI, policy, compose plan, tentacle loader
- `examples/tentacles/` — MIT arms
- `examples/environments/compose/` — plan-only workstation stub
- `tests/` — pytest
