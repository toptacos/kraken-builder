# Hooks: after_run, patch, and finish

*The feature that makes tentacles composable: another tentacle watches a run,
returns a `patch`, and core calls `finish` on the original tentacle — with the
patch. Every command below was executed by `scripts/verify_articles.py`, in
an isolated `KRAKEN_HOME` with no network.*

## The shape of it

A hook is not middleware, not a trigger, not a wrapper around bytes. It is
**another tentacle invocation** that core performs around your run:

```
    kraken run stamper grow
              │
              ▼
        stamper.grow  ──────────────▶ result: {value: 3}
              │
              ▼  after_run   (hooks from ~/.kraken/config.yaml or the manifest)
        stamp.convert  ────▶ result: {patch: {multiplier: 7}}
              │
              ▼  core sees a patch, tentacle declares finish
        stamper.finish(payload: {raw: <grow result>, patch: {multiplier: 7}})
              │
              ▼
        result: {value: 21, finished: true}
```

Three rules make that safe, and each one is testable:

1. **Hooks do not fire hooks.** Inside a hook, core sets `_IN_HOOK`, so the
   stamp tentacle's own run never recurses.
2. **A tentacle cannot hook itself** — `collect_hooks` skips a hook whose
   `tentacle` equals the target.
3. **A hook cannot corrupt the main result.** A missing or failing *optional*
   hook is reported as `{skipped: true}` and the run still succeeds.

## Step 1 — the tentacle with a `finish` action

`grow` produces a value; `finish` receives the raw result plus whatever patch
the hook produced and merges them:

```run,sh
mkdir -p stamper
cat > stamper/tentacle.yaml <<'EOF'
name: stamper
version: 0.1.0
license: free
runtime: binary
binary: handler.py
actions: [grow, finish]
description: Grows a value, then lets a hook finish it.
EOF

cat > stamper/handler.py <<'EOF'
import json, sys

req = json.load(sys.stdin)
action = req.get("action") or "grow"
payload = req.get("payload") or {}

if action == "grow":
    result = {"arm": "stamper", "value": 3}
elif action == "finish":
    raw = payload.get("raw") or {}
    # core hands finish the grow result as "raw" and the hook's patch as
    # "patch"; merging them is this tentacle's own business.
    merged = dict(raw)
    merged.update(payload.get("patch") or {})
    merged["finished"] = True
    result = {"arm": "stamper", **merged}
else:
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": False,
                                 "error": "unknown action: " + action}))
    sys.exit(0)

sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": True, "result": result}))
EOF

python3 -m kraken tentacle add stamper >/dev/null && echo "installed stamper"
```

```output
installed stamper
  Tests skipped: no tests/ directory
```

## Step 2 — the hook: a tentacle that returns a patch

The hook is an ordinary tentacle, and it receives the same envelope any
tentacle does -- with the target's response object under `payload.result`.
Its whole job is to answer with `{"patch": {...}}` in its result:

```run,sh
mkdir -p stamp
cat > stamp/tentacle.yaml <<'EOF'
name: stamp
version: 0.1.0
license: free
runtime: binary
binary: handler.py
actions: [convert]
description: A hook that multiplies whatever a run produced.
EOF

cat > stamp/handler.py <<'EOF'
import json, sys

req = json.load(sys.stdin)
payload = req.get("payload") or {}
# The hook payload carries the target's whole response object under
# "result" -- {v, id, ok, result: ...} -- so grow's answer is one level
# deeper, at result.result.value.
envelope = payload.get("result") or {}
inner = envelope.get("result") or {}
value = inner.get("value", 1)

sys.stdout.write(json.dumps({
    "v": 1,
    "id": req.get("id"),
    "ok": True,
    "result": {"patch": {"multiplier": 7, "saw_value": value}},
}))
EOF

python3 -m kraken tentacle add stamp >/dev/null && echo "installed stamp"
```

```output
installed stamp
  Tests skipped: no tests/ directory
```

## Step 3 — wire the hook in config

Hooks live in the project config (or the user config, or the tentacle
manifest — all three merge). Project config is `.kraken/config.yaml` in the
directory you run from:

```run,sh
mkdir -p .kraken
cat > .kraken/config.yaml <<'EOF'
version: 1
hooks:
  after_run:
    - tentacle: stamp
      action: convert
      optional: true
      when: ["stamper"]
EOF
cat .kraken/config.yaml
```

```output
version: 1
hooks:
  after_run:
    - tentacle: stamp
      action: convert
      optional: true
      when: ["stamper"]
```

## Step 4 — watch it happen

Run the tentacle. The response carries `_hooks` (what fired) and, because the
hook returned a patch and `finish` is a declared action, `finished: true`:

```run,sh
python3 -m kraken run stamper grow
```

```output
{"v": 1, "id": "1", "ok": true, "result": {"arm": "stamper", "value": 3, "multiplier": 7, "saw_value": 3, "finished": true}, "_hooks": [{"tentacle": "stamp", "ok": true, "result": {"v": 1, "id": "1", "ok": true, "result": {"patch": {"multiplier": 7, "saw_value": 3}}}}], "finished": true}
```

Read that output as the diagram above: `value` is still 3 from `grow`, but
`multiplier` and `saw_value` came from the hook, and `finished: true` says the
`finish` action ran and merged them.

## Step 5 — prove the hook is what did it

Same tentacle, same command, no hook in config. Move the config aside:

```run,sh
mv .kraken/config.yaml /tmp/hooks-off.yaml
python3 -m kraken run stamper grow
mv /tmp/hooks-off.yaml .kraken/config.yaml
```

```output
{"v": 1, "id": "1", "ok": true, "result": {"arm": "stamper", "value": 3}}
```

No `_hooks`, no `finished` — `grow` ran and answered, and nothing else
happened. That is the seam the hook plugs into.

## Step 6 — the safety valves

Optional is the difference between a hook that participates and a hook that
must succeed. A missing hook tentacle answers `{skipped: true}` and the run
still works:

```run,sh
python3 -m kraken tentacle add stamp >/dev/null 2>&1
python3 - <<'EOF'
import os, pathlib, subprocess, sys, json, tempfile

# Point the hook at a tentacle that does not exist.
cfg = pathlib.Path(".kraken/config.yaml")
cfg.write_text(
    "version: 1\n"
    "hooks:\n"
    "  after_run:\n"
    "    - tentacle: does-not-exist\n"
    "      action: convert\n"
    "      optional: true\n"
    "      when: [\"stamper\"]\n"
)
out = subprocess.run(
    [sys.executable, "-m", "kraken", "run", "stamper", "grow"],
    capture_output=True, text=True,
)
data = json.loads(out.stdout)
print("run ok:", data["result"]["value"] == 3)
print("hooks reported:", json.dumps(data.get("_hooks")))
cfg.write_text(
    "version: 1\n"
    "hooks:\n"
    "  after_run:\n"
    "    - tentacle: stamp\n"
    "      action: convert\n"
    "      optional: true\n"
    "      when: [\"stamper\"]\n"
)
EOF
```

```output
run ok: True
hooks reported: [{"tentacle": "does-not-exist", "ok": false, "skipped": true, "error": "'arm not loaded: does-not-exist'"}]
```

`resolver reports "does-not-exist" is not installed` in the hook entry, the
main answer is untouched, and the exit code stays 0. Now make the hook
*required* and watch the run fail instead — this is the one configuration
where a hook can stop the work:

```run,expect-fail,sh
cp .kraken/config.yaml /tmp/good-config.yaml
cat > .kraken/config.yaml <<'EOF'
version: 1
hooks:
  before_run:
    - tentacle: does-not-exist
      action: convert
      optional: false
      when: ["stamper"]
EOF
if python3 -m kraken run stamper grow >aborted.txt 2>&1; then rc=0; else rc=$?; fi
tail -1 aborted.txt
echo "exit code: $rc"
cp /tmp/good-config.yaml .kraken/config.yaml
exit $rc
```

```output
kraken.core.hooks.HookAbort: before_run hook 'does-not-exist' aborted stamper: 'arm not loaded: does-not-exist'
exit code: 1
```

`before_run` with `optional: false` is the only combination that aborts the
main run — a gate, not a spy. Everything else observes.

## What a hook is for

Audit logs, notifications, a cache warmer, a post-processor that rewrites a
result — every one of those is a tentacle you already know how to write,
hanging off a run without touching the tentacle's code. That is the
composition model: no plugin host, no event bus, one JSON envelope reused
for everything.

Full semantics in `docs/HOOKS.md`; the four events are `before_run`,
`after_run`, `on_error`, and `after_install`.
