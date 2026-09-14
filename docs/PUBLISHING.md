# Write a plugin and list it for other people

Two registries exist. Do not mix them up.

| Registry | What it is | Who uses it |
|---|---|---|
| **Device** | `Registry` in `kraken.core.registry` + `~/.kraken/tentacles/` | One machine. `kraken tentacle add`. |
| **Catalog** | Hosted list on `api.topta.co` + `schemas/catalog.json` | Other people. Publish a slug, source URL, license flag. |

You ship a **tentacle**, not an in-process arm, if anyone else should install it.

## 1. Write the tentacle

Directory:

```
my-arm/
  tentacle.yaml
  handler.py          # or a compiled binary
  README.md
  tests/
```

`tentacle.yaml`:

```yaml
name: my-arm
version: "0.1.0"
license: free          # or premium
runtime: binary
binary: handler.py
actions: [ping, work]
description: One sentence.
homepage: https://github.com/you/kraken-tentacle-my-arm
requires:
  protocol: 1
  core: ">=0.1.0"
```

Handler speaks protocol v1 on stdin/stdout. Exit 0 always for app errors; set `"ok": false`.

```python
#!/usr/bin/env python3
import json, sys

def main():
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "ping"
    payload = req.get("payload") or {}
    if action == "ping":
        out = {"pong": True}
    elif action == "work":
        out = {"echo": payload}
    else:
        sys.stdout.write(json.dumps({
            "v": 1, "id": req.get("id"), "ok": False,
            "error": {"code": "unknown_action", "message": action},
        }))
        return 0
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": True, "result": out}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

Rules:

- Do not import `kraken.core`.
- Do not read `~/.kraken/keys` yourself. Core already gated premium.
- Put state under payload `dir` or `$KRAKEN_HOME/.kraken/data/<name>/`.
- List every action in the manifest. Unknown actions return `ok: false`.

Copy `examples/tentacles/geo` (free) or `weather-pro` (premium).

## 2. Register it on one device

```bash
kraken tentacle add ./my-arm
# or
kraken tentacle add github.com/you/kraken-tentacle-my-arm
kraken list
kraken run my-arm ping --payload '{}'
```

`tentacle add` copies the folder to `~/.kraken/tentacles/my-arm/` and records the lockfile. That is the **device registry**. Other people do not see it yet.

Premium:

```bash
# in tentacle.yaml: license: premium
kraken license set my-arm YOUR_KEY
KRAKEN_LICENSE_OFFLINE=1 kraken run my-arm work --payload '{}'
```

## 3. Register it for other people (catalog)

Today the public catalog is a static file plus Laravel stubs. Fill both.

### A. Repo catalog (ships with the site)

Add a row to `schemas/catalog.json`:

```json
{
  "name": "my-arm",
  "version": "0.1.0",
  "license": "free",
  "source": "https://github.com/you/kraken-tentacle-my-arm",
  "actions": ["ping", "work"],
  "blurb": "Does one job.",
  "author": "you"
}
```

The marketing site reads this list (or the API) for the Catalog cards.

### B. Control plane (other installs)

Drop `control-plane/laravel-api/routes/kraken.php` into api.topta.co.

```
POST /api/kraken/catalog/register
  { "name", "version", "source", "license", "actions", "blurb", "author_email" }

GET  /api/kraken/catalog
  → [ { name, version, source, license, blurb } ]

POST /api/kraken/licenses/verify
POST /api/kraken/licenses/issue
POST /api/kraken/beta
```

Until those routes are live on the server, `kraken tentacle add github.com/you/repo` is the public install path. The catalog is how people **find** the URL.

### C. Human review (beta)

`website/register.html` and `website/publish.html` collect author email + source URL. No unsigned binary is promoted on kraken.topta.co without a source URL and a version.

Install command you print in the README:

```bash
kraken tentacle add https://github.com/you/kraken-tentacle-my-arm.git
```

## 4. Checklist before you ask for a listing

- [ ] `tentacle.yaml` name is unique (lowercase, hyphen)
- [ ] handler exits 0 on app failure
- [ ] no secrets printed to stdout
- [ ] `license: premium` only if you will issue keys
- [ ] README has add + run + payload examples
- [ ] tests that speak the contract (see `tests/test_dev_tentacles.py`)
- [ ] you will not run `curl | sh` from the tentacle itself

See also `docs/PLUGINS.md`, `docs/CONTRACT.md`, `docs/SECURITY.md`.
