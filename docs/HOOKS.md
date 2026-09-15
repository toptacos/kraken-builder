# Triggers, hooks, and middleware

Three words people mix up. In Kraken they are **not** the same layer.

| | Trigger | Hook | Middleware |
|---|---|---|---|
| Lives in | `arm.yaml` / `tentacle.yaml` `triggers:` | `hooks:` on a tentacle **or** `~/.kraken/config.yaml` | **Not used** in the local CLI |
| When | Advertises *how this tentacle may be started* | Core event → another tentacle | Would wrap bytes *inside* a process |
| Runs | `manual` CLI, `queue` drain | `before_run`, `after_run`, `on_error`, `after_install` | PHP/Laravel HTTP stack on api.topta.co only |
| Can abort the main work | No | `before_run` + `optional: false` + `ok: false` | N/A on device |
| Language | Label only | Same JSON contract as any tentacle | Framework-specific |

Core never imports tentacle source. A hook is just `invoke_binary` with extra payload fields (`hook`, `target`, `result`).

## Triggers (capability labels)

```yaml
# arms/echo/arm.yaml
triggers:
  - manual
  - queue
```

Meaning today: “this arm is allowed as a CLI `run` and as a `kraken queue` job.” Nothing in core *fires* a trigger by itself. A cron or n8n job that shells out to `kraken run echo ping` is still `manual` as far as core is concerned.

Working:

```bash
python3 bin/kraken run echo ping          # trigger = manual
python3 bin/kraken queue echo ping        # trigger = queue
```

## Hooks (side-effect tentacles)

```yaml
# .kraken/config.yaml (this repo ships this)
hooks:
  after_run:
    - tentacle: echo-bin
      action: ping
      optional: true
      when: ["echo", "*"]
```

Or on a tentacle:

```yaml
# examples/tentacles/weather-pro/tentacle.yaml
hooks:
  before_run:
    - tentacle: geo
      action: lookup
      optional: false
```

Working (from repo root):

```bash
python3 bin/kraken run echo ping
# result may include "_hooks": [{ "tentacle": "echo-bin", "ok": true, ... }]
```

Hook payload (protocol v1):

```json
{
  "hook": "after_run",
  "target": "echo",
  "target_action": "ping",
  "ok": true,
  "result": {},
  "plan": ["echo"]
}
```

Rules:

- Hook invokes **do not fire hooks** (`_IN_HOOK`). That is cycle-prevention for the hook graph.
- `tentacle` equal to the target is skipped (a tentacle cannot hook itself).
- Missing optional hook → `{skipped: true}`, main run still succeeds.
- `before_run` + `optional: false` + hook `ok: false` → `HookAbort`, main tentacle does not run, `on_error` still fires.
- `priority:` integer, lower runs first (default 100).
- `if: ok` runs only when the main result was ok. `if: error` on failure. `if: action=forecast` matches the action name.

## Middleware (control plane only)

Laravel / FrankenPHP middleware belongs on **https://api.topta.co** (auth, rate limit, license verify HTTP). It is not in `kraken run`. Do not add Python decorators around tentacle `handle()` as a “platform” feature — that only works for in-process arms and breaks the binary contract.

If you need “something around every HTTP request,” put it in `control-plane/laravel-api/`. If you need “something around every local run,” use a hook.

## Notify vs hooks

`kraken.core.notify.emit` is core’s own side effect:

- `KRAKEN_NOTIFY_STDOUT=1` prints `{"notify":"run",...}`
- `KRAKEN_NOTIFY_WEBHOOK` POSTs JSON

Use notify for a URL. Use a hook when the side effect is **another tentacle binary** (desktop, audit log, pager).

```bash
KRAKEN_NOTIFY_STDOUT=1 python3 bin/kraken run echo ping
```

## Cycle detection (dependency graph, not hooks)

`kraken.core.resolve` DFS-colors nodes. A node already on the walk is a cycle:

```text
loop-a → loop-b → loop-a
# ResolveError: dependency cycle: loop-a -> loop-b -> loop-a
```

That graph is `requires.tentacles`. Hook cycles are stopped by `_IN_HOOK` instead of DFS, because hooks are side effects, not data deps. Compose (`--compose`) walks `plan.order` and is also not a hook.

See `docs/DEPENDENCIES.md` and `tests/test_resolve.py`.
