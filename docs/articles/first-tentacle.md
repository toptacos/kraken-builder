# Your first tentacle

*A tentacle is any executable that reads one JSON object on stdin and writes
one JSON object on stdout. This article builds one from an empty directory,
installs it, runs it, breaks it on purpose, and fixes it — with every
command's real output shown. Every block on this page was executed by
`scripts/verify_articles.py`; none of it is written by hand.*

Time: about five minutes. You need a shell and Python 3.11+. You do not need
an account, a network connection, or Docker.

## What you are building

```
                    one JSON object on stdin
   kraken run  ───────────────────────────────▶  your executable
   (or any
    language's            one JSON object on
    caller)  ◀───────────────────────────────   stdout, exit 0
```

Core has no opinion about your language, your dependencies, or your
packaging. It shells out, and the contract is the whole integration surface.

## The request you will receive

Core writes exactly this to your stdin:

```json
{
  "v": 1,
  "id": "1",
  "op": "invoke",
  "action": "ping",
  "payload": {}
}
```

- `v` — protocol version. Today it is always `1`.
- `id` — a request id. Echo it back; that is how a caller matches a response.
- `op` — `invoke`. The only operation there is.
- `action` — which verb your tentacle was asked for.
- `payload` — the caller's arguments, a JSON object (possibly empty).

## The response you write back

```json
{
  "v": 1,
  "id": "1",
  "ok": true,
  "result": { "arm": "my-tool", "action": "ping" }
}
```

Success is `"ok": true` with `result`. A refusal is `"ok": false` with
`error` — **and exit code 0**. This distinction is the spine of the whole
contract and we will prove why in a minute.

## Step 1 — the manifest

Every tentacle is a directory with a `tentacle.yaml`. Make one:

```run,sh
mkdir -p my-tool
cat > my-tool/tentacle.yaml <<'EOF'
name: my-tool
version: 0.1.0
license: free
runtime: binary
binary: handler.sh
actions: [ping, greet]
description: The tentacle from the first-tentacle article.
EOF
cat my-tool/tentacle.yaml
```

```output
name: my-tool
version: 0.1.0
license: free
runtime: binary
binary: handler.sh
actions: [ping, greet]
description: The tentacle from the first-tentacle article.
```

The keys, all of which you just wrote:

| Key | Meaning |
|---|---|
| `name` | The name `kraken run` uses. Unique per device. |
| `version` | Semver. The resolver reads it for dependency constraints. |
| `license` | `free` or `premium`. Premium is a *check against this same open source* — never a hidden binary. |
| `runtime` | `binary` for an external executable (the other kind, in-process arms, is core's own business). |
| `binary` | Path to your executable, relative to this file. `.sh` runs via bash, `.py` via python3, `.js` via node, `.go` via `go run`, and so on. |
| `actions` | The verbs this tentacle answers. Anything else is a refusal, dealt with below. |

## Step 2 — the handler

The smallest honest handler, in POSIX sh. Note `exec python3 -c`: the request
must stay on stdin, so the script cannot be fed in as a heredoc — a heredoc
*is* stdin, and reading it would consume the request.

```run,sh
cat > my-tool/handler.sh <<'EOF'
#!/bin/sh
set -eu
exec python3 -c '
import json, sys

req = json.load(sys.stdin)
action = req.get("action") or "ping"
payload = req.get("payload") or {}
name = payload.get("name", "world")

if action == "ping":
    result = {"arm": "my-tool", "action": action, "pong": True}
elif action == "greet":
    result = {"arm": "my-tool", "action": action, "greeting": f"hello, {name}"}
else:
    # A refusal is an answer, not a crash: ok:false, exit 0.
    sys.stdout.write(json.dumps({
        "v": 1,
        "id": req.get("id"),
        "ok": False,
        "error": "unknown action: " + action,
    }))
    sys.exit(0)

sys.stdout.write(json.dumps({
    "v": 1,
    "id": req.get("id"),
    "ok": True,
    "result": result,
}))
'
EOF
chmod +x my-tool/handler.sh
cat my-tool/handler.sh | head -3
```

```output
#!/bin/sh
set -eu
exec python3 -c '
```

## Step 3 — install and list it

```run,sh
python3 -m kraken tentacle add my-tool
```

```output
{"ok": true, "name": "my-tool", "root": "<work>/home/.kraken/tentacles/my-tool", "plan": {"root": "my-tool", "order": ["my-tool"], "nodes": {"my-tool": {"version": "0.1.0", "kind": "binary"}}, "optional_missing": []}}
  Tests skipped: no tests/ directory
```

Installed tentacles live under `$KRAKEN_HOME` and are scanned on each run —
no restart, no daemon, no registry:

```run,sh
python3 -m kraken list | grep my-tool
```

```output
my-tool	0.1.0	ping,greet	binary	free
```

## Step 4 — run it

```run,sh
python3 -m kraken run my-tool ping
```

```output
{"v": 1, "id": "1", "ok": true, "result": {"arm": "my-tool", "action": "ping", "pong": true}}
```

That is the whole product experience: one command, one JSON object. Pass
arguments with `--payload`:

```run,sh
python3 -m kraken run my-tool greet --payload '{"name":"kraken"}'
```

```output
{"v": 1, "id": "1", "ok": true, "result": {"arm": "my-tool", "action": "greet", "greeting": "hello, kraken"}}
```

## Step 5 — an action you did not declare

Your manifest promised `[ping, greet]`. Ask for something else:

```run,sh
python3 -m kraken run my-tool explode
```

```output
{"v": 1, "id": "1", "ok": false, "error": "unknown action: explode"}
```

Look closely at what happened there. Core asked your handler, your handler
answered `"ok": false` **with exit 0**, and the CLI dutifully printed your
refusal. An application failure is a normal, inspectable result.

## Step 6 — break it on purpose (the mistake that costs an afternoon)

Now the same handler, but it exits 1 on that branch. The output is the
contract violation:

```run,expect-fail,sh
mkdir -p bad-tool
sed 's/name: my-tool/name: bad-tool/' my-tool/tentacle.yaml > bad-tool/tentacle.yaml
sed 's/    sys.exit(0)/    sys.exit(1)/' my-tool/handler.sh > bad-tool/handler.sh
chmod +x bad-tool/handler.sh
python3 -m kraken tentacle add bad-tool
python3 -m kraken run bad-tool explode
```

```output
{"ok": true, "name": "bad-tool", "root": "<work>/home/.kraken/tentacles/bad-tool", "plan": {"root": "bad-tool", "order": ["bad-tool"], "nodes": {"bad-tool": {"version": "0.1.0", "kind": "binary"}}, "optional_missing": []}}
  Tests skipped: no tests/ directory
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "<repo>/kraken/__main__.py", line 3, in <module>
    raise SystemExit(main())
                     ~~~~^^
  File "<repo>/kraken/core/cli.py", line 493, in main
    run_named(
    ~~~~~~~~~^
        root,
        ^^^^^
    ...<4 lines>...
        home=home,
        ^^^^^^^^^^
    )
    ^
  File "<repo>/kraken/core/runner.py", line 121, in run_named
    result = _invoke_one(root, name, action, body, home)
  File "<repo>/kraken/core/runner.py", line 85, in _invoke_one
    return invoke_binary(binary, action, payload, timeout=tentacle_timeout(spec))
  File "<repo>/kraken/core/contract.py", line 119, in invoke_binary
    raise RuntimeError(
    ...<2 lines>...
    )
RuntimeError: <work>/home/.kraken/tentacles/bad-tool/handler.sh exited 1 on action 'explode': no stderr
```

A non-zero exit means **transport failure**: core never sees your JSON
error, and your carefully written reason is demoted to a stack-traceish
`RuntimeError`. Two tentacles in this repo's history shipped exactly that
bug (berth and ledger), and the contract sweep now hunts for it.

## Step 7 — the rule, stated once

> Exit 0 always. Carry every failure in the body: `"ok": false` plus an
> `error` string.

If your process dies — truly dies — let it: exit non-zero, print the
traceback to stderr. Core will surface the stderr in the error, which is the
one time that is useful.

## What you have

A tentacle is a directory. To ship it, that directory is your repository:

```run,sh
ls my-tool
```

```output
handler.sh
tentacle.yaml
```

Anyone installs it the same way you did:

```run,sh
python3 -m kraken tentacle add my-tool && python3 -m kraken run my-tool ping | head -1
```

```output
{"ok": true, "name": "my-tool", "root": "<work>/home/.kraken/tentacles/my-tool", "plan": {"root": "my-tool", "order": ["my-tool"], "nodes": {"my-tool": {"version": "0.1.0", "kind": "binary"}}, "optional_missing": []}}
{"v": 1, "id": "1", "ok": true, "result": {"arm": "my-tool", "action": "ping", "pong": true}}
  Tests skipped: no tests/ directory
```

From here:

- **docs/CONTRACT.md** — the contract, written as the spec it is.
- **Polyglot: one contract, six languages** (this directory) — the same
  handler in sh, python, node, php, ruby, perl, and go.
- **Hooks: after_run, patch, and finish** (this directory) — react to every
  run without touching the tentacle.
- **docs/TUTORIAL_TENTACLES.md** — deeper manifest semantics and linting.

Every command and output on this page was executed by
`scripts/verify_articles.py` on a machine with no network, in an isolated
`KRAKEN_HOME` (`KRAKEN_OFFLINE=1`). If a step here ever lies, CI fails.
