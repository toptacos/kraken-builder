# Notification system

Tentacles return data. Core notifies.

## Events

| Event | When |
|---|---|
| `run` | After a successful `_invoke_one` of the *target* tentacle |
| `hook` | After a hook tentacle runs |

## Backends

| Backend | Enable |
|---|---|
| stdout JSON | `KRAKEN_NOTIFY_STDOUT=1` |
| HTTP POST | `KRAKEN_NOTIFY_WEBHOOK=https://…` |
| other | Write a hook tentacle; do not grow `notify.py` |

Body:

```json
{"event": "run", "payload": {"name": "echo", "action": "ping", "ok": true}, "product": "kraken"}
```

Webhook failures are swallowed (4s timeout). Local CLI must not die because Slack is down. Required user-facing failure belongs in `on_error` hooks with `optional: false`.
