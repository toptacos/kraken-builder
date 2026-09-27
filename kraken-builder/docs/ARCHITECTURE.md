# Architecture

Kraken is two planes that share one contract.

```
 User / agent
      │  JSON request
      ▼
 kraken-core  (one cross-platform executable)
      │  discovers .kraken chain
      │  routes action → tentacle binary
      ▼
 tentacle binary (any language, any repo)
      │  JSON response
      ▼
 kraken-core notify / queue / log
```

## Planes

| Plane | Runs | Stack | State |
|---|---|---|---|
| Core CLI | Every device | Slice 1: Python. Target: FrankenPHP static binary wrapping a thin Laravel/Symfony console app | Files under `.kraken/` |
| Control plane | kraken.topta.co | Laravel + FrankenPHP + Postgres | Accounts, catalog, licenses, billing |
| Tentacles | Separate repos | Any language compiled to one binary | Own `data/` inside `.kraken/tentacles/<name>/` |

Core never imports tentacle source. It only execs a binary and parses JSON.

## Why not compile Laravel into every tentacle

A full PHP framework in each tool would fight “lean core.” Laravel + FrankenPHP + Postgres belong on the **control plane** and optionally inside **one** `kraken` binary for `kraken serve` / `kraken login`. Tentacles stay dumb workers.

## Discovery

1. `/etc/kraken` or `%ProgramData%\kraken`
2. `~/.kraken`
3. Every `.kraken` from filesystem root down to cwd (cwd wins)

Each directory may contain `config.yaml`, `data/`, `logs/`, `tentacles/`.

## Runtime

- Request: `{ "v":1, "id":"…", "op":"invoke", "action":"status", "payload":{} }`
- Response: `{ "v":1, "id":"…", "ok":true, "result":{} }` or `{ "ok":false, "error":{ "code":"…", "message":"…" } }`
- Transport for local tentacles: stdin/stdout, one JSON object, process exits.
- Optional later: Unix socket / localhost HTTP for long-running tentacles.

## Notifications

Core owns user-facing effects: stdout, desktop, webhook, email draft. Tentacles return data only.
