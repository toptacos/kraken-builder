# Adding suckers

A **sucker** is a named hook row. Runtime is the same as any hook: another tentacle, JSON in / JSON out. Core never imports it. A tentacle cannot hook itself.

## Three files you add

1. A tentacle that implements `convert` (or `ping`) and, for envelope merge, returns `result.patch`.
2. A row in `suckers/<name>.yaml` for humans and reviews.
3. The same keys under `hooks.after_run` on the *target* (`watch`’s `tentacle.yaml`) **or** in `~/.kraken/config.yaml`.

`examples/suckers/*.yaml` in kraken-builder are not auto-loaded. Copy the keys into a live hooks list.

## Row schema

```yaml
sucker: after-watch          # documentation name only
tentacle: watch-stamp        # required; must not equal "watch"
action: convert              # default ping
optional: true               # default true
priority: 10                 # lower runs first
if: ok                       # ok | error | action=tick
when: ["watch"]              # target names or "*"
```

Collection order: user/project `hooks:` then the target manifest. Sorted by `priority`. `when` filters the **target being run**.

## Hook payload your sucker receives

```json
{
  "hook": "after_run",
  "target": "watch",
  "target_action": "tick",
  "ok": true,
  "result": { "v": 1, "ok": true, "result": { "arm": "watch" } },
  "plan": ["watch"]
}
```

## Patch merge (optional but useful)

If the sucker writes:

```json
{ "v": 1, "ok": true, "result": { "patch": { "sucker": "my-arm", "note": "…" } } }
```

and `watch` lists `finish`, core calls `watch finish` with `{raw, patch}` and sets `finished: true`. See `examples/tentacles/watch-stamp/handler.py`.

## Worked add

```bash
mkdir -p examples/tentacles/watch-pager
# tentacle.yaml name: watch-pager, actions: [convert]
# handler returns result.patch.channel = "pager"
cat > suckers/watch-pager.yaml <<'EOF'
sucker: watch-pager
tentacle: watch-pager
action: convert
optional: true
priority: 40
if: ok
when: ["watch"]
EOF
```

Append to `tentacle.yaml`:

```yaml
hooks:
  after_run:
    - tentacle: watch-pager
      action: convert
      optional: true
      priority: 40
      if: ok
      when: ["watch"]
```

```bash
kraken tentacle add examples/tentacles/watch-pager
kraken run watch ping
# result._hooks includes watch-pager
```

## Rules that will silently drop your row

- `tentacle: watch` on a watch run — self-hook stripped
- Hook invoke during another hook — `_IN_HOOK` skips nested hooks
- `if: ok` when the main envelope was `"ok": false`
- Missing binary + `optional: true` → `{skipped: true}` (CI-safe)
- `before_run` + `optional: false` + `ok: false` → `HookAbort`, main does not run

## Notify vs a sucker

URL / ntfy / stdout line → `KRAKEN_NOTIFY_*` (core).  
Another binary (stamp, pager, file convert) → sucker.  
Do not grow `kraken.core.notify`.

## Tests to copy

`tests/test_suckers.py` asserts the YAML row and that `watch-stamp convert` returns a patch. Add a case per new sucker. `tests/e2e_scenarios.py` scenario `sucker_stamp_and_finish` drives `finish` locally without core.
